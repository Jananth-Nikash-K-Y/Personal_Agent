"""
Core AI engine for Lee — handles LLM interaction and tool execution.
"""
import json
import uuid
import asyncio
from typing import AsyncGenerator
from groq import Groq

from config import GROQ_API_KEY, MODEL_NAME, MAX_TOKENS, TEMPERATURE, SYSTEM_PROMPT, TOOL_DEFINITIONS
from core.tools import TOOL_FUNCTIONS
from core.history import history


groq_client = Groq(api_key=GROQ_API_KEY)


async def generate_conversation_title(user_message: str) -> str:
    """Generate a short title for a conversation based on the first message."""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

    # Build messages for the LLM
    context_messages = history.get_recent_messages_for_context(conversation_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + context_messages

    try:
        # Call Groq with tools
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

        assistant_message = response.choices[0].message

        # Handle tool calls (may be multiple rounds)
        max_tool_rounds = 5
        round_count = 0

        while assistant_message.tool_calls and round_count < max_tool_rounds:
            round_count += 1

            # Add assistant's tool-calling message to context
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                yield {"type": "tool_call", "tool_name": tool_name, "tool_args": tool_args}

                # Execute the tool
                tool_result = await execute_tool(tool_name, tool_args)

                yield {"type": "tool_result", "tool_name": tool_name, "content": tool_result}

                # Add tool result to context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

                # Save tool interaction to history
                history.add_message(
                    conversation_id, str(uuid.uuid4()), "assistant",
                    f"[Tool Call: {tool_name}({json.dumps(tool_args)})]",
                    tool_name=tool_name
                )
                history.add_message(
                    conversation_id, str(uuid.uuid4()), "tool",
                    tool_result, tool_call_id=tool_call.id, tool_name=tool_name
                )

            # Call the LLM again with tool results
            response = groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
            )

            assistant_message = response.choices[0].message

        # Final text response
        reply = assistant_message.content or "I completed the action."
        reply_id = str(uuid.uuid4())
        history.add_message(conversation_id, reply_id, "assistant", reply)

        yield {"type": "message", "content": reply, "message_id": reply_id, "conversation_id": conversation_id}

    except Exception as e:
        error_msg = f"Sorry, I ran into an error: {str(e)}"
        yield {"type": "error", "content": error_msg}


async def chat_simple(user_message: str, conversation_id: str = None, channel: str = "web") -> str:
    """Simplified chat that returns just the final text response. Used by Discord channel."""
    final_reply = ""
    final_conv_id = conversation_id

    async for event in chat(user_message, conversation_id, channel):
        if event["type"] == "conversation_id":
            final_conv_id = event["content"]
        elif event["type"] == "message":
            final_reply = event["content"]
        elif event["type"] == "error":
            final_reply = event["content"]

    return final_reply, final_conv_id
