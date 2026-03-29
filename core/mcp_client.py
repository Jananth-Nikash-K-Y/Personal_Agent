"""
MCP Client — manages long-lived connections to external MCP servers.

On startup, each enabled server is launched as a stdio subprocess using npx.
Tools discovered from each server are merged into the engine's tool registry,
replacing any built-in tools of the same logical name.

Servers:
  - sequential-thinking  (no key required) - structured chain-of-thought reasoning
  - filesystem           (no key required) - enhanced file ops, replaces read/write/list
  - brave-search         (BRAVE_API_KEY)   - replaces web_search with Brave results
  - github               (GITHUB_TOKEN)    - repo, issue, PR management
  - google-maps          (GOOGLE_MAPS_API_KEY) - places, directions, geocoding
"""

import json
import logging
import os
from contextlib import AsyncExitStack

logger = logging.getLogger(__name__)

# ── Alias Map ─────────────────────────────────────────────────────────────────
# Maps an MCP tool name to the built-in tool name it should REPLACE.
# A value of None means it's a brand-new capability (no built-in to hide).
_TOOL_ALIASES: dict[str, str | None] = {
    # Filesystem MCP — same names as builtins (direct replacement)
    "read_file": "read_file",
    "write_file": "write_file",
    "list_directory": "list_directory",
    # New filesystem capabilities
    "read_multiple_files": None,
    "edit_file": None,
    "create_directory": None,
    "directory_tree": None,
    "move_file": None,
    "search_files": None,
    "get_file_info": None,
    "list_allowed_directories": None,
}

# ── Global State ───────────────────────────────────────────────────────────────
_exit_stack: AsyncExitStack | None = None
_sessions: dict = {}          # server_name → ClientSession
_tool_to_session: dict = {}   # tool_name   → (ClientSession, mcp_tool_name)

# ── Public Registries (populated by initialize()) ─────────────────────────────
MCP_TOOL_DEFINITIONS: list[dict] = []      # OpenAI function-calling format
MCP_TOOL_FUNCTIONS: dict = {}              # name → async callable
REPLACED_BUILTIN_TOOLS: set[str] = set()  # built-in names hidden from TOOL_DEFINITIONS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mcp_schema_to_openai(tool) -> dict:
    """Convert an MCP Tool object to the OpenAI function-calling dict format."""
    schema = tool.inputSchema if tool.inputSchema else {
        "type": "object", "properties": {}, "required": []
    }
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": (tool.description or "").strip(),
            "parameters": schema,
        },
    }


async def _dispatch(session, mcp_name: str, arguments: dict) -> str:
    """Call a tool on an MCP session and return a JSON string result."""
    try:
        result = await session.call_tool(mcp_name, arguments=arguments)
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            elif hasattr(block, "data"):
                parts.append(f"[binary data, {len(block.data)} bytes]")
            else:
                parts.append(str(block))
        combined = "\n".join(parts)
        return json.dumps({"status": "success", "result": combined})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def _make_tool_func(session, mcp_name: str):
    """Create a bound async wrapper function for a specific MCP tool."""
    async def _wrapper(**kwargs):
        return await _dispatch(session, mcp_name, kwargs)
    _wrapper.__name__ = mcp_name
    return _wrapper


def get_active_tool_definitions(builtin_definitions: list) -> list:
    """
    Return the merged TOOL_DEFINITIONS list for the LLM:
      - Built-in tools MINUS any replaced by an MCP server
      - PLUS all discovered MCP tool definitions
    """
    active_builtins = [
        t for t in builtin_definitions
        if t["function"]["name"] not in REPLACED_BUILTIN_TOOLS
    ]
    return active_builtins + MCP_TOOL_DEFINITIONS


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def initialize():
    """
    Start all enabled MCP server subprocesses and populate the tool registries.
    Servers with missing API keys are skipped gracefully with a log warning.
    """
    global _exit_stack

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        logger.error(
            "MCP SDK not installed. Run: pip install mcp  — MCP tools will be unavailable."
        )
        return

    from config import GITHUB_TOKEN

    home = os.path.expanduser("~")

    server_configs = [
        {
            "name": "sequential-thinking",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            "extra_env": {},
            "enabled": True,
            "description": "Chain-of-thought reasoning tool",
        },
        {
            "name": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", home],
            "extra_env": {},
            "enabled": True,
            "description": f"Enhanced file access under {home}",
        },
        {
            "name": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "extra_env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN,
                "GITHUB_TOKEN": GITHUB_TOKEN,
            },
            "enabled": bool(GITHUB_TOKEN),
            "description": "GitHub repos, issues, PRs, branches",
        },
        {
            "name": "openstreetmap",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-map", "--stdio"],
            "extra_env": {},
            "enabled": True,
            "description": "OpenStreetMap — maps and geocoding",
        },
    ]

    _exit_stack = AsyncExitStack()
    await _exit_stack.__aenter__()

    connected_count = 0

    for cfg in server_configs:
        if not cfg["enabled"]:
            logger.info(f"⏭  MCP [{cfg['name']}] skipped — API key not configured")
            continue

        try:
            # Merge process environment with server-specific env vars
            env = {
                **os.environ,
                **{k: v for k, v in cfg["extra_env"].items() if v}
            }

            params = StdioServerParameters(
                command=cfg["command"],
                args=cfg["args"],
                env=env,
            )

            read_stream, write_stream = await _exit_stack.enter_async_context(
                stdio_client(params)
            )
            session = await _exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()

            _sessions[cfg["name"]] = session

            # Discover all tools this server exposes
            tools_result = await session.list_tools()
            tool_count = 0

            for tool in tools_result.tools:
                openai_def = _mcp_schema_to_openai(tool)
                MCP_TOOL_DEFINITIONS.append(openai_def)

                wrapper = _make_tool_func(session, tool.name)
                MCP_TOOL_FUNCTIONS[tool.name] = wrapper
                _tool_to_session[tool.name] = (session, tool.name)

                # Handle cross-name aliases (e.g. brave_web_search → web_search)
                alias_builtin = _TOOL_ALIASES.get(tool.name)
                if alias_builtin and alias_builtin != tool.name:
                    MCP_TOOL_FUNCTIONS[alias_builtin] = wrapper
                    _tool_to_session[alias_builtin] = (session, tool.name)

                # Track which built-ins this MCP tool replaces
                if tool.name in _TOOL_ALIASES:
                    builtin_name = _TOOL_ALIASES[tool.name]
                    if builtin_name:
                        REPLACED_BUILTIN_TOOLS.add(builtin_name)

                tool_count += 1

            connected_count += 1
            logger.info(f"✅ MCP [{cfg['name']}] — {tool_count} tools  ({cfg['description']})")

        except Exception as exc:
            logger.warning(f"⚠️  MCP [{cfg['name']}] failed to start: {exc}")

    total_tools = len(MCP_TOOL_FUNCTIONS)
    logger.info(
        f"🔌 MCP ready — {total_tools} tools across {connected_count} active servers"
    )
    if REPLACED_BUILTIN_TOOLS:
        replaced_list = ", ".join(sorted(REPLACED_BUILTIN_TOOLS))
        logger.info(f"🔄 Built-in tools replaced by MCP: {replaced_list}")


async def shutdown():
    """Cleanly shut down all MCP server connections and child processes."""
    global _exit_stack
    if _exit_stack:
        try:
            await _exit_stack.aclose()
        except Exception as e:
            logger.warning(f"MCP shutdown warning: {e}")
        finally:
            _exit_stack = None
            logger.info("🔌 MCP servers disconnected.")
