"""
Central configuration for Lee — Personal AI Assistant.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Identity ──────────────────────────────────────────────────────────────────
AGENT_NAME = "Lee"
AGENT_VERSION = "2.0.0"

# ── API Keys ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# ── Model Settings ────────────────────────────────────────────────────────────
MODEL_NAME = "llama-3.3-70b-versatile"
MAX_TOKENS = 4096
TEMPERATURE = 0.7
MAX_HISTORY_MESSAGES = 40

# ── Server Settings ───────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8000

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(DATA_DIR, "Lee.db")
USER_MEMORY_PATH = os.path.join(DATA_DIR, "user_memory.txt")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_PROMPT = f"""You are {AGENT_NAME}, personal assistant to [Your Name],
a developer based in Tamil Nadu, India (IST timezone).

User preferences:
- Prefers concise responses unless detail is needed
- Primary languages: Python, JavaScript
- Working directory: ~/Desktop/Personal_AI_Assistant
- Common tasks: coding help, web research, file management

Always greet by name. Remember context from earlier in the conversation.
You have access to a persistent user memory file at {USER_MEMORY_PATH}. 
You should read this file when starting a new conversation and use the `write_file` tool to update it when you learn new preferences or facts about the user.

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
- Be concise and helpful. Use markdown formatting in your responses.
- When you use a tool, briefly explain what you're doing.
- If a request seems dangerous (like deleting system files), warn the user first.
- Be proactive — if you can anticipate follow-up needs, mention them.
- You have personality: warm, witty, and competent. You're not just an assistant, you're a trusted companion.
- If you don't know something and can't find it with your tools, say so honestly.
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
    }
]
