"""
Central tool registry for Sentinal Lee.
This module imports all sub-tools and exports them to maintain compatibility 
with the core engine's tool dispatch system.
"""
from .system import (
    get_system_info, get_datetime, open_application, open_url, 
    run_shell_command, get_clipboard, set_clipboard, take_screenshot
)
from .files import (
    read_file, write_file, append_file, list_directory, share_file_to_chat
)
from .web import (
    web_search, get_top_news, get_weather, add_web_monitor
)
from .finance import (
    get_market_data, get_indian_analysis, log_expense, get_expense_summary, 
    generate_monthly_finance_report
)
from .comms import (
    get_unread_emails, send_email, get_calendar_events, add_calendar_event,
    set_reminder, add_contact, search_contacts
)
from .productivity import (
    remember, forget, add_task, list_tasks, complete_task, update_task
)
from .knowledge import search_knowledge

# Export a registry map for the engine to easily dispatch
TOOL_FUNCTIONS = {
    # System
    "get_system_info": get_system_info,
    "get_datetime": get_datetime,
    "open_application": open_application,
    "open_url": open_url,
    "run_shell_command": run_shell_command,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "take_screenshot": take_screenshot,
    
    # Files
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_directory": list_directory,
    "share_file_to_chat": share_file_to_chat,
    
    # Web
    "web_search": web_search,
    "get_top_news": get_top_news,
    "get_weather": get_weather,
    "add_web_monitor": add_web_monitor,
    
    # Finance
    "get_market_data": get_market_data,
    "get_indian_analysis": get_indian_analysis,
    "log_expense": log_expense,
    "get_expense_summary": get_expense_summary,
    "generate_monthly_finance_report": generate_monthly_finance_report,
    
    # Comms
    "get_unread_emails": get_unread_emails,
    "send_email": send_email,
    "get_calendar_events": get_calendar_events,
    "add_calendar_event": add_calendar_event,
    "set_reminder": set_reminder,
    "add_contact": add_contact,
    "search_contacts": search_contacts,
    
    # Productivity
    "remember": remember,
    "forget": forget,
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "update_task": update_task,
    
    # Knowledge (RAG)
    "search_knowledge": search_knowledge,
}
