"""
Central configuration for Lee — Personal AI Assistant.
"""
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinal_lee")

# ── Identity ──────────────────────────────────────────────────────────────────
AGENT_NAME = os.getenv("AGENT_NAME", "Lee")
AGENT_VERSION = "2.1.0"
AGENT_USER_NAME = os.getenv("AGENT_USER_NAME", "Boss")

# ── API Keys ──────────────────────────────────────────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# ── Security — Owner-only access ──────────────────────────────────────────────
# Get your Telegram user ID from @userinfobot in Telegram
# Get your Discord user ID: Developer Mode → right-click yourself → Copy ID
TELEGRAM_OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))
DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))

# ── Model Settings ────────────────────────────────────────────────────────────
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.3-70b-instruct")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "40"))

# ── Server Settings ───────────────────────────────────────────────────────────
# Web dashboard removed for security, running headless.

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "Lee.db")
USER_MEMORY_PATH = os.path.join(DATA_DIR, "user_memory.txt")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_PROMPT = f"""You are {AGENT_NAME}, personal assistant to {AGENT_USER_NAME},
a developer based in Tamil Nadu, India (IST timezone).

User preferences:
- Prefers concise responses unless detail is needed
- Primary languages: Python, JavaScript
- Working directory: ~/Desktop/Personal_AI_Assistant
- Common tasks: coding help, web research, file management

Always greet by name. Remember context from earlier in the conversation.
You have access to a persistent long-term memory database. Use the `remember` tool to proactively save important facts, preferences, or project details about the user as you learn them. Use the `forget` tool to remove outdated facts.
The facts you remember will be automatically injected into your context at the start of future conversations.

You have access to system tools that let you interact with the user's machine. When the user asks you to do something that requires a tool, use the appropriate tool function.

Capabilities you have:
- Get system information (CPU, RAM, disk, battery)
- Get current date and time
- Open applications on the Mac
- Execute shell commands
- Read and write files
- List directory contents
- Read and set clipboard contents
- Take screenshots
- Search the web
- Get weather information
- Read your Gmail emails and send emails via Gmail

Guidelines:
- **Be extremely human-like and conversational.** Write as if you are texting or Slacking a close colleague.
- Use the `web_search` tool to look up current events, real-time info, or whenever the user asks to search the web.
- Use the `share_file_to_chat` tool to send a local file to the chat so the user can download it natively.
- Avoid robotic structuring ("Here is the information you requested", "I have executed the tool").
- Use varied sentence lengths, natural pacing, and occasional conversational fillers (e.g., "Ah,", "Got it.", "Give me a second...").
- Do not use overly formal or pedantic language. Keep it breezy, warm, and witty.
- When you use a tool, mention it naturally (e.g., "Let me just check your calendar" instead of "Executing set_reminder tool").
- If a request seems dangerous, warn the user like a friend would ("Whoa, hold on, that command looks like it might delete everything...").
- You are a trusted companion and a highly competent developer. Let that personality shine through.
- If you don't know something, admit it conversationally ("I'm actually not sure about that one," or "I couldn't find anything on that.")
- Use emojis sparingly but effectively to convey tone.
"""


# ── Tool Definitions (for Groq function calling) ─────────────────────────────
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get system information including CPU usage, memory, disk space, and battery status.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Get the current date, time, day of week, and timezone.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open a macOS application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Name of the application to open (e.g., 'Safari', 'Terminal', 'Finder')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute a shell command and return its output. Use for system operations, file management, or getting information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file from the local filesystem.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the directory to list. Defaults to home directory."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Get the current contents of the system clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to copy to the clipboard"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the current screen.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information on a given query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g., 'London', 'New York')"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unread_emails",
            "description": "Fetch unread emails from the user's Gmail Inbox.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of emails to retrieve (default is 5)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Draft and send an email via Gmail. Always confirm with the user before sending, unless explicitly asked to send it automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject of the email"
                    },
                    "body": {
                        "type": "string",
                        "description": "Content body of the email (plain text or basic HTML)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Append content to an existing file without overwriting it. Creates the file if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file to append to"},
                    "content": {"type": "string", "description": "Content to append to the file"}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default web browser on macOS.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to open (e.g., 'https://example.com')"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Create a reminder in macOS Reminders app.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the reminder"},
                    "notes": {"type": "string", "description": "Additional notes (optional)"},
                    "due_date": {"type": "string", "description": "Due date/time e.g. '2024-12-25 10:00' (optional)"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Save a fact about the user or project to long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "The fact to remember (e.g. 'User is learning Rust', 'Favorite color is blue')"}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget",
            "description": "Delete a fact from long-term memory by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact_id": {"type": "integer", "description": "The ID of the memory fact to delete (find the ID in your system prompt)"}
                },
                "required": ["fact_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "share_file_to_chat",
            "description": "Share a local file (document, image, etc.) natively in the chat to the user so they can download it directly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Absolute or relative path to the file to be shared"}
                },
                "required": ["file_path"]
            }
        }
    }
]
