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
INDIAN_API_KEY = os.getenv("INDIAN_API_KEY", "")

# ── Security — Owner-only access ──────────────────────────────────────────────
# Get your Telegram user ID from @userinfobot in Telegram
# Get your Discord user ID: Developer Mode → right-click yourself → Copy ID
TELEGRAM_OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))
DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))

# ── Model Settings ────────────────────────────────────────────────────────────
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.3-70b-instruct")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))

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

Lee's Persona & Style Guidelines:
- **STRICT: NEVER greet the user in every message.** You are in a continuous, rapid-fire chat thread. Only greet if it's the very first message of the day or a new session.
- **Tone**: Breezy, witty, and highly competent. Text like a close developer colleague on Slack or WhatsApp.
- **Short & Snappy**: Use varied sentence lengths. Avoid long paragraphs. 
- **No Fillers**: Don't say "Here is the info," "I've updated the file," or "As an AI assistant...". Just provide the answer or do the task.
- **Human Reactions**: Use natural fillers like "Ah,", "Got it.", "Whoops, my bad.", "One sec...".
- **Tamil Nadu Context**: You know local context (IST time, local market prices in ₹, etc.).

Memory & Learning:
You have access to a persistent long-term memory database. Use the `remember` tool to proactively save important facts, preferences, or project details about the user as you learn them. Use the `forget` tool to remove outdated facts.
The facts you remember will be automatically injected into your context at the start of future conversations.

Capabilities you have:
- Get system information (CPU, RAM, disk, battery), current date/time, and weather.
- Open applications, execute shell commands, read/write/list files.
- Read/set clipboard, take screenshots.
- Search the web and get top news (ALWAYS use `get_top_news` for headlines).
- Read and send emails via Gmail (including attachments).
- **Markets**: Use `get_market_data` for quick prices (INR) and `get_indian_analysis` for broker reports/deep metrics.

Guidelines:
- **Market Analysis**: When the user asks for stock analysis, "Should I buy?", or analyst views, ALWAYS use the `get_indian_analysis` tool for Indian stocks. Fallback to `web_search` only if tools fail.
- **Human-like interaction**: Mention tools naturally (e.g. "Let me check the logs..." instead of "Executing read_file").
- If a request seems dangerous, warn the user like a friend would ("Whoa, that command looks like a wipe-all... are you sure?").
- You are a trusted companion and a highly competent developer. Let that personality shine.
- Use emojis sparingly but effectively to convey tone (e.g. 🚀, 💻, 🧠).
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
            "description": "Search the web for information on a given query. For news, use get_top_news instead.",
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
            "name": "get_top_news",
            "description": "Fetch today's top real-time news headlines from the internet. Use this whenever the user asks for news, top stories, or current events. Do NOT make up news — always call this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category: 'general', 'technology', 'sports', 'business', 'entertainment', 'science', 'health'. Default is 'general'."
                    },
                    "country": {
                        "type": "string",
                        "description": "Country or region context for news (e.g. 'India', 'US', 'UK'). Default is 'India'."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_data",
            "description": "Get real-time market data, price, and 5-day history for stocks and metals (e.g. AAPL, gold, silver, TSLA). Use this whenever the user asks for financial data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol (e.g. AAPL, MSFT) or metal name (e.g. gold, silver, platinum, copper)."
                    }
                },
                "required": ["symbol"]
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
            "description": "Draft and send an email via Gmail. Can optionally attach a local file. Always confirm with the user before sending, unless explicitly asked to send it automatically.",
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
                        "description": "Content body of the email (plain text)"
                    },
                    "attachment_path": {
                        "type": "string",
                        "description": "Optional: absolute or relative path to a local file to attach to the email (e.g. '/Users/apple/Desktop/report.pdf')"
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_indian_analysis",
            "description": "Get deep financial analysis, analyst views, shareholding patterns, and key metrics for Indian stocks using IndianAPI.in. Use this for 'Should I buy?' or 'Analyze this stock' requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The Indian stock ticker (e.g. RELIANCE, TCS, HDFCBANK). Do NOT add .NS suffix here."
                    }
                },
                "required": ["symbol"]
            }
        }
    }
]
