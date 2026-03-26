"""
Core AI engine for Lee — handles LLM interaction and tool execution.
"""
import json
import uuid
import asyncio
import logging
from typing import AsyncGenerator
from openai import OpenAI

from config import NVIDIA_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT, TOOL_DEFINITIONS, USER_MEMORY_PATH
from core.tools import TOOL_FUNCTIONS
from core.history import history

logger = logging.getLogger(__name__)

openai_client = OpenAI(
    api_key=NVIDIA_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1"
)


async def generate_conversation_title(user_message: str) -> str:
    """Generate a short title for a conversation based on the first message."""
    try:
        response = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Generate a very short conversation title (3-6 words) for the following message. Return ONLY the title, nothing else."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=20,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip().strip('"')
    except Exception:
        return user_message[:40] + ("..." if len(user_message) > 40 else "")


async def _load_user_memory() -> str:
    """Load user memory from SQLite to inject into system prompt."""
    try:
        memories = history.get_all_memories()
        if memories:
            lines = ["--- Persistent Long-Term Memory ---"]
            for m in memories:
                lines.append(f"[ID: {m['id']}] {m['fact']}")
            lines.append("--- End of Memory ---")
            return "\n\n" + "\n".join(lines)
    except Exception as e:
        logger.warning(f"Could not load user memory: {e}")
    return ""


async def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool function and return its result."""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})

    try:
        result = await func(**arguments)
        return result
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tool execution failed: {str(e)}"})


async def _run_tool_call(tool_call: dict):
    """Parse and execute a single tool call, returning (tool_name, tool_args, tool_result)."""
    tool_name = tool_call["function"]["name"]
    try:
        args_str = tool_call["function"]["arguments"]
        tool_args = json.loads(args_str) if args_str else {}
        if not isinstance(tool_args, dict):
            tool_args = {}
    except Exception:
        tool_args = {}

    try:
        tool_result = await execute_tool(tool_name, tool_args)
    except Exception as e:
        tool_result = json.dumps({"status": "error", "message": str(e)})

    return tool_name, tool_args, tool_result


async def chat(
    user_message: str,
    conversation_id: str = None,
    channel: str = "web",
    callback=None,
) -> AsyncGenerator[dict, None]:
    """
    Process a user message and yield response events.

    Events:
    - {"type": "conversation_id", "content": "..."}
    - {"type": "tool_call", "tool_name": "...", "tool_args": {...}}
    - {"type": "tool_result", "tool_name": "...", "content": "..."}
    - {"type": "message", "content": "...", "message_id": "..."}
    - {"type": "error", "content": "..."}
    """
    is_new_conversation = not conversation_id

    # Create or retrieve conversation
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        title = await generate_conversation_title(user_message)
        history.create_conversation(conversation_id, title=title, channel=channel)
    else:
        conv = history.get_conversation(conversation_id)
        if not conv:
            history.create_conversation(conversation_id, title="Continued Chat", channel=channel)

    yield {"type": "conversation_id", "content": conversation_id}

    # Save user message
    user_msg_id = str(uuid.uuid4())
    history.add_message(conversation_id, user_msg_id, "user", user_message)

    # Build system prompt — always inject user memory so resumed conversations
    # also have access to the latest known facts about the user
    memory_snippet = await _load_user_memory()
    if memory_snippet:
        effective_system_prompt = SYSTEM_PROMPT + memory_snippet
    else:
        effective_system_prompt = SYSTEM_PROMPT

    # Build messages for the LLM
    context_messages = history.get_recent_messages_for_context(conversation_id)
    messages = [{"role": "system", "content": effective_system_prompt}] + context_messages

    try:
        max_tool_rounds = 5
        round_count = 0

        while round_count <= max_tool_rounds:
            # Check limit BEFORE calling the LLM to prevent an extra round executing
            if round_count >= max_tool_rounds:
                limit_msg = f"⚠️ I hit my tool-use limit ({max_tool_rounds} rounds) and couldn't complete the task fully. Please try rephrasing or breaking it into smaller steps."
                limit_id = str(uuid.uuid4())
                history.add_message(conversation_id, limit_id, "assistant", limit_msg)
                yield {"type": "message", "content": limit_msg, "message_id": limit_id, "conversation_id": conversation_id}
                break

            round_count += 1

            # Call OpenAI without streaming for reliable tool parsing on 3rd-party endpoints
            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stream=False
            )

            message = response.choices[0].message
            full_content = message.content or ""
            is_tool_call = bool(message.tool_calls)

            current_tool_calls_dict = {}

            # Fallback for Nvidia NIM leaking tool calls into text
            if not is_tool_call and full_content:
                import re
                
                # Check for {"name": "tool_name", "parameters": {...}} leak
                json_match = re.search(r'\{\s*"name"\s*:\s*".+?",\s*"parameters"\s*:\s*\{.*?\}\s*\}', full_content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        class DummyFunction:
                            def __init__(self, name, args):
                                self.name = name
                                self.arguments = args
                        class DummyCall:
                            def __init__(self, func):
                                self.id = "call_" + str(uuid.uuid4())[:10]
                                self.function = func
                                self.type = "function"
                        
                        message.tool_calls = [DummyCall(DummyFunction(parsed["name"], json.dumps(parsed.get("parameters", {}))))]
                        is_tool_call = True
                        full_content = full_content.replace(json_match.group(0), "").strip()
                    except Exception:
                        logger.debug("Fallback JSON tool-call parse failed, skipping.", exc_info=True)
                
                # Check for pseudo-code Python format: web_search.query("abc") or web_search("abc")
                if not is_tool_call:
                    py_match = re.search(r'([a-zA-Z0-9_]+)(?:\.[a-zA-Z0-9_]+)?\(\s*"([^"]+)"\s*\)', full_content)
                    if py_match:
                        tool_name = py_match.group(1)
                        if tool_name in TOOL_FUNCTIONS:
                            args_str = "{}"
                            if tool_name == "web_search": args_str = json.dumps({"query": py_match.group(2)})
                            elif tool_name == "run_shell_command": args_str = json.dumps({"command": py_match.group(2)})
                            elif tool_name == "read_file": args_str = json.dumps({"file_path": py_match.group(2)})
                            
                            class DummyFunction:
                                def __init__(self, name, args):
                                    self.name = name
                                    self.arguments = args
                            class DummyCall:
                                def __init__(self, func):
                                    self.id = "call_" + str(uuid.uuid4())[:10]
                                    self.function = func
                                    self.type = "function"
                            
                            message.tool_calls = [DummyCall(DummyFunction(tool_name, args_str))]
                            is_tool_call = True
                            full_content = full_content.replace(py_match.group(0), "").strip()

            if full_content:
                yield {"type": "content_chunk", "content": full_content}

            if is_tool_call:
                for idx, tc in enumerate(message.tool_calls):
                    current_tool_calls_dict[idx] = {
                        "id": getattr(tc, "id", "call_" + str(uuid.uuid4())[:10]),
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }

            if not is_tool_call:
                # Final text response
                reply = full_content or "I completed the action."
                reply_id = str(uuid.uuid4())
                history.add_message(conversation_id, reply_id, "assistant", reply)
                yield {"type": "message", "content": reply, "message_id": reply_id, "conversation_id": conversation_id}
                break

            # --- Handle tool calls ---
            tool_calls_data = [current_tool_calls_dict[idx] for idx in sorted(current_tool_calls_dict.keys())]

            # Add assistant's tool-calling message to context
            messages.append({
                "role": "assistant",
                "content": full_content,
                "tool_calls": tool_calls_data
            })

            # Save assistant's tool-calling message to history ONCE
            history.add_message(
                conversation_id, str(uuid.uuid4()), "assistant",
                json.dumps({"content": full_content, "tool_calls": tool_calls_data}),
                tool_name="multiple_tool_calls"
            )

            # Emit tool_call events first (before execution)
            for tool_call in tool_calls_data:
                tool_name = tool_call["function"]["name"]
                try:
                    args_str = tool_call["function"]["arguments"]
                    tool_args = json.loads(args_str) if args_str else {}
                    if not isinstance(tool_args, dict):
                        tool_args = {}
                except Exception:
                    tool_args = {}
                yield {"type": "tool_call", "tool_name": tool_name, "tool_args": tool_args}

            # Execute all tool calls concurrently
            tasks = [_run_tool_call(tc) for tc in tool_calls_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for tool_call, result in zip(tool_calls_data, results):
                if isinstance(result, Exception):
                    tool_name = tool_call["function"]["name"]
                    tool_result = json.dumps({"status": "error", "message": str(result)})
                    tool_args = {}
                else:
                    tool_name, tool_args, tool_result = result

                yield {"type": "tool_result", "tool_name": tool_name, "content": tool_result}

                # Add tool result to context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                })

                # Save the individual tool result to history
                history.add_message(
                    conversation_id, str(uuid.uuid4()), "tool",
                    tool_result, tool_call_id=tool_call["id"], tool_name=tool_name
                )

    except Exception as e:
        logger.error(f"Engine error: {e}", exc_info=True)
        # Handle specific Groq API parsing error metadata
        failed_gen = getattr(e, "failed_generation", "")
        if failed_gen:
            error_msg = f"Sorry, I ran into an error generating the tool call: {str(e)}\n\nFailed text: {failed_gen}"
        else:
            error_msg = f"Sorry, I ran into an error: {str(e)}"
        yield {"type": "error", "content": error_msg}


async def chat_simple(user_message: str, conversation_id: str = None, channel: str = "web") -> tuple:
    """Simplified chat that returns just the final text response. Used by Discord/Telegram channels."""
    final_reply = ""
    final_conv_id = conversation_id
    files_to_send = []

    async for event in chat(user_message, conversation_id, channel):
        if event["type"] == "conversation_id":
            final_conv_id = event["content"]
        elif event["type"] == "message":
            final_reply = event["content"]
        elif event["type"] == "error":
            final_reply = event["content"]
        elif event["type"] == "tool_result" and event.get("tool_name") == "share_file_to_chat":
            try:
                data = json.loads(event["content"])
                if data.get("status") == "file_sharing_queued" and "path" in data:
                    files_to_send.append(data["path"])
            except Exception:
                pass

    return final_reply, final_conv_id, files_to_send
