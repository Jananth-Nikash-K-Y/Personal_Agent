"""
Productivity tools — Task management and long-term memory.
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def remember(fact: str) -> str:
    """Store a fact in long-term memory."""
    from core.history import history
    try:
        added = history.add_memory(fact)
        if added:
            return json.dumps({"status": "success", "message": f"Memory stored: {fact}"})
        else:
            return json.dumps({"status": "duplicate", "message": f"I already remember that: {fact}"})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def forget(fact_id: int) -> str:
    """Remove a fact from long-term memory by its ID."""
    from core.history import history
    try:
        success = history.remove_memory(fact_id)
        if success:
            return json.dumps({"status": "success", "message": f"Memory {fact_id} forgotten."})
        else:
            return json.dumps({"status": "not_found", "message": f"Memory ID {fact_id} not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def add_task(title: str, description: str = None, priority: str = "Medium", due_date: str = None, project: str = None) -> str:
    """Add a task to the local TODO list."""
    from core.history import history
    try:
        task_id = history.add_task(title, description, priority, due_date, project)
        return json.dumps({"status": "success", "task_id": task_id, "message": f"Task '{title}' added."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def list_tasks(status: str = "Pending", project: str = None) -> str:
    """List tasks, optionally filtered by status or project."""
    from core.history import history
    try:
        tasks = history.get_tasks(status, project)
        return json.dumps({"status": "success", "count": len(tasks), "tasks": tasks})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def complete_task(task_id: int) -> str:
    """Mark a task as completed."""
    from core.history import history
    try:
        success = history.update_task(task_id, status="Completed")
        if success:
            return json.dumps({"status": "success", "message": f"Task {task_id} completed."})
        else:
            return json.dumps({"status": "not_found", "message": f"Task ID {task_id} not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

async def update_task(task_id: int, title: str = None, description: str = None, priority: str = None, due_date: str = None, status: str = None) -> str:
    """Update details of an existing task."""
    from core.history import history
    try:
        updates = {}
        if title: updates["title"] = title
        if description: updates["description"] = description
        if priority: updates["priority"] = priority
        if due_date: updates["due_date"] = due_date
        if status: updates["status"] = status
        success = history.update_task(task_id, **updates)
        if success:
            return json.dumps({"status": "success", "message": f"Task {task_id} updated."})
        else:
            return json.dumps({"status": "not_found", "message": f"Task ID {task_id} not found."})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
