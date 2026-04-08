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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
INDIAN_API_KEY = os.getenv("INDIAN_API_KEY", "")

# ── MCP Server API Keys ────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")              # GitHub MCP


# ── Ollama Fallback Settings ───────────────────────────────────────────────────
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# ── Sync & Productivity ───────────────────────────────────────────────────────
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "~/Documents/ObsidianVault")

# ── Security — Owner-only access ──────────────────────────────────────────────
# Get your Telegram user ID from @userinfobot in Telegram
# Get your Discord user ID: Developer Mode → right-click yourself → Copy ID
TELEGRAM_OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))
DISCORD_OWNER_ID = int(os.getenv("DISCORD_OWNER_ID", "0"))

# ── Model Settings ────────────────────────────────────────────────────────────
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
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

# ── Knowledge Base (RAG) — 10-Layer Security Firewall ─────────────────────────
# Only files in KNOWLEDGE_BASE_DIR are indexed. Local-only embeddings.
KNOWLEDGE_BASE_DIR = os.getenv("KNOWLEDGE_BASE_DIR", os.path.join(DATA_DIR, "knowledge"))
VECTOR_DB_PATH = os.path.join(DATA_DIR, "chroma_db")
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # 100% Private, Local-only on Mac
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

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
- **Tone**: Breezy, witty, and highly competent. Text like a close developer colleague on Slack or Telegram.
- **Short & Snappy**: Use varied sentence lengths. Avoid long paragraphs. 
- **No Fillers**: Don't say "Here is the info," "I've updated the file," or "As an AI assistant...". Just provide the answer or do the task.
- **Human Reactions**: Use natural fillers like "Ah,", "Got it.", "Whoops, my bad.", "One sec...".
- **Tamil Nadu Context**: You know local context (IST time, local market prices in ₹, etc.).

Memory & Learning:
You have access to a persistent long-term memory database. Use the `remember` tool to proactively save important facts, preferences, or project details about the user as you learn them. Use the `forget` tool to remove outdated facts.
The facts you remember will be automatically injected into your context at the start of future conversations.

Capabilities you have:
- Get system information (CPU, RAM, disk, battery), current date/time, and weather.
- Open applications, execute shell commands, read/write/list files (including `move_file`, `edit_file`, `directory_tree` and more via Filesystem MCP).
- Read/set clipboard, take screenshots.
- **IMPORTANT — News & Elaboration**: 
    - When asked for news, use `get_top_news`. 
    - **STRICT: DO NOT provide the same list of headlines twice.** If the user asks for news again, either find new stories or explain that you've already shared the latest.
    - **ELABORATION**: If the user asks to "elaborate" or "tell me more" about a specific headline, DO NOT just search for more headlines. You MUST use `web_search` on that specific topic or URL to get the actual story content and summarize it.
    - **Source Quality**: For market news, prioritize reputable sources like *Moneycontrol, Economic Times, Livemint, Bloomberg, or Reuters*. Avoid low-quality SEO sites (e.g., "School Assembly News").
- **MCP-Powered Capabilities** (available if servers are connected):
    - **Sequential Thinking** (`sequentialthinking`): Use this tool when tackling complex problems — debugging, multi-step plans, architecture decisions. Break your thinking into explicit steps.
    - **GitHub** (`search_repositories`, `list_issues`, `create_issue`, `create_pull_request`, etc.): Manage repos, issues, PRs and code search directly.
    - **OpenStreetMap** (`show-map`, `geocode`): Render map views and perform geocoding for addresses or coordinates.
- **Personal Management Tools**:
    - **Tasks**: Use `add_task`, `list_tasks`, and `complete_task` to manage your work.
    - **Knowledge Search** (`search_knowledge`): Use this tool to search through your local documents (PDFs, Markdown, text). This is your "Semantic Brain." If the user asks about a project or a file you don't immediately see, search the knowledge base.
    - **Expenses**: Use `log_expense` to track spending. You can also parse receipts from photos. Weekly summaries are available via `get_expense_summary`.
    - **Contacts**: Use `add_contact` and `search_contacts` to build your local CRM. Save emails, phones, and relationship context here.
    - **Web Monitoring**: Use `add_web_monitor` to watch URLs for changes (e.g. stock drops, job postings). Lee will alert you when they change.
- **Vision & Documents**: 
    - You can "see" images and read PDFs. If the user sends a file, summarize it and ask what they want to do next.
- **Human-like interaction**: Mention tools naturally (e.g. "Let me check the logs..." instead of "Executing read_file").
- If a request seems dangerous, warn the user like a friend would ("Whoa, that command looks like a wipe-all... are you sure?").
- You are a trusted companion and a highly competent developer. Let that personality shine.
- Use emojis sparingly but effectively to convey tone (e.g. 🚀, 💻, 🧠).
"""


# ── Tool Definitions (for Gemini/OpenAI function calling) ─────────────────────────
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Fetch calendar events from Apple Calendar for the next X days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default is 1)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "Add an event to Apple Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the event"},
                    "start_time": {"type": "string", "description": "Start time in natural language (e.g., 'Tomorrow at 10am' or 'March 27, 2026 10:00:00 AM')"},
                    "duration_mins": {"type": "integer", "description": "Duration in minutes (default is 30)"},
                    "location": {"type": "string", "description": "Optional location"},
                    "notes": {"type": "string", "description": "Optional notes/description"}
                },
                "required": ["title", "start_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add a new personal task or Todo item to the local tracker.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the task"},
                    "description": {"type": "string", "description": "Extended details about the task"},
                    "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "default": "Medium"},
                    "due_date": {"type": "string", "description": "Due date e.g. '2024-12-25'"},
                    "project": {"type": "string", "description": "Category or project name (e.g. 'Work', 'Home', 'SentinalLee')"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List existing tasks, filtered by status or project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["Pending", "Completed"], "default": "Pending"},
                    "project": {"type": "string", "description": "Filter by project name"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "The ID of the task to complete"}
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": "Draft a personal expense or income log. If the user doesn't provide a category and sub-category, you MUST use 'UNKNOWN' instead of asking them. An interactive menu will be shown so they can just click what category it is.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Total amount"},
                    "description": {"type": "string", "description": "What was the money spent on? Or where did the income come from?", "default": "General"},
                    "category": {"type": "string", "description": "High-level category. If not clearly stated, use 'UNKNOWN'.", "default": "UNKNOWN"},
                    "sub_category": {"type": "string", "description": "More specific category. If not clearly stated, use 'UNKNOWN'.", "default": "UNKNOWN"},
                    "expense_type": {"type": "string", "description": "'expense' or 'income'", "enum": ["expense", "income"], "default": "expense"},
                    "merchant": {"type": "string", "description": "Where was the money spent/received? (e.g. 'Amazon', 'Employer')"},
                    "currency": {"type": "string", "default": "INR"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_expense_summary",
            "description": "Get a list of recent expenses you've logged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_contact",
            "description": "Save a new contact (name, email, phone, etc.) to your local address book.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the contact"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "relationship": {"type": "string", "description": "How do you know them? (e.g. 'Friend', 'Work', 'Family')"},
                    "notes": {"type": "string"},
                    "tags": {"type": "string", "description": "Comma-separated tags"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search your local contacts for a name or details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Name or keyword to search for"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_web_monitor",
            "description": "Watch a specific webpage for changes. Alerts you when the content updates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to watch"},
                    "label": {"type": "string", "description": "Friendly name for this monitor"},
                    "selector": {"type": "string", "description": "CSS selector to watch specifically (optional)"},
                    "threshold": {"type": "string", "description": "Alert condition (optional)"}
                },
                "required": ["url", "label"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Perform a semantic search across your local documents (PDFs, Markdown, text). Use this to find information in your personal knowledge base or project files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The natural language question or search terms to look for and retrieve relevant document context."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_monthly_finance_report",
            "description": "Generate an aesthetic 3D PNG pie chart report of the user's local expenses for a given month, and share it over Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "month_str": {"type": "string", "description": "The month to generate the report for, in YYYY-MM format (e.g. '2026-04')."}
                },
                "required": ["month_str"]
            }
        }
    }
]
