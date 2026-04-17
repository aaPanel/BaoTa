from typing import List, Dict, Any, Optional
import json
from . import register_tool
from .base import _xml_response

import json
import os
import time
from typing import List, Dict, Any, Optional
from enum import Enum


class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TodoItem:
    def __init__(self, content: str, status: TodoStatus = TodoStatus.PENDING,
                 id: Optional[str] = None, priority: TodoPriority = TodoPriority.MEDIUM):
        self.id = id or str(int(time.time() * 1000))  # Simple ID generation
        self.content = content
        self.status = status
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "status": self.status,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        return cls(
            content=data["content"],
            status=TodoStatus(data.get("status", "pending")),
            id=data.get("id"),
            priority=TodoPriority(data.get("priority", "medium"))
        )


class TodoManager:
    def __init__(self, session_id: str, sessions_dir: str = "sessions"):
        self.session_id = session_id
        self.session_dir = os.path.join(sessions_dir, session_id)
        self.file_path = os.path.join(self.session_dir, "todos.json")
        self._ensure_sessions_dir()
    
    def _ensure_sessions_dir(self):
        if not os.path.exists(self.session_dir):
            try:
                os.makedirs(self.session_dir)
            except OSError:
                pass
    
    def get_todos(self) -> List[TodoItem]:
        if not os.path.exists(self.file_path):
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TodoItem.from_dict(item) for item in data]
        except Exception:
            return []
    
    def save_todos(self, todos: List[TodoItem]):
        data = [item.to_dict() for item in todos]
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def update_todos(self, new_todos_data: List[Dict[str, Any]], merge: bool = False) -> List[TodoItem]:
        if merge:
            current_todos = self.get_todos()
            current_map = {t.id: t for t in current_todos}
            
            for item_data in new_todos_data:
                item_id = item_data.get("id")
                if item_id and item_id in current_map:
                    # Update existing
                    existing = current_map[item_id]
                    existing.content = item_data.get("content", existing.content)
                    existing.status = TodoStatus(item_data.get("status", existing.status))
                    existing.priority = TodoPriority(item_data.get("priority", existing.priority))
                else:
                    # Add new
                    new_item = TodoItem.from_dict(item_data)
                    current_todos.append(new_item)
            
            final_todos = current_todos
        else:
            final_todos = [TodoItem.from_dict(item) for item in new_todos_data]
        
        self.save_todos(final_todos)
        return final_todos


# Load descriptions from files would be ideal, but for now we embed them or read them if possible.
# Since we are implementing them in python, we can just put the text in docstrings.

TODO_READ_DESC = """Use this tool to read the current to-do list for the session. This tool should be used proactively and frequently to ensure that you are aware of
the status of the current task list. You should make use of this tool as often as possible, especially in the following situations:
- At the beginning of conversations to see what's pending
- Before starting new tasks to prioritize work
- When the user asks about previous tasks or plans
- Whenever you're uncertain about what to do next
- After completing tasks to update your understanding of remaining work
- After every few messages to ensure you're on track

Usage:
- This tool takes in no parameters. So leave the input blank or empty. DO NOT include a dummy object, placeholder string or a key like "input" or "empty". LEAVE IT BLANK.
- Returns a list of todo items with their status, priority, and content
- Use this information to track progress and plan next steps
- If no todos exist yet, an empty list will be returned"""

TODO_WRITE_DESC = """Use this tool to create and manage a structured task list for your current coding session. This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user.
It also helps the user understand the progress of the task and overall progress of their requests.

## When to Use This Tool
Use this tool proactively in these scenarios:
1. Complex multistep tasks - When a task requires 3 or more distinct steps or actions
2. Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
3. User explicitly requests todo list - When the user directly asks you to use the todo list
4. User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
5. After receiving new instructions - Immediately capture user requirements as todos. Feel free to edit the todo list based on new information.
6. After completing a task - Mark it complete and add any new follow-up tasks
7. When you start working on a new task, mark the todo as in_progress. Ideally you should only have one todo as in_progress at a time. Complete existing tasks before starting new ones.

## Task States and Management
1. **Task States**: Use these states to track progress:
   - pending: Task not yet started
   - in_progress: Currently working on (limit to ONE task at a time)
   - completed: Task finished successfully
   - cancelled: Task no longer needed

2. **Task Management**:
   - Update task status in real-time as you work
   - Mark tasks complete IMMEDIATELY after finishing (don't batch completions)
   - Only have ONE task in_progress at any time
   - Complete current tasks before starting new ones
   - Cancel tasks that become irrelevant

3. **Task Breakdown**:
   - Create specific, actionable items
   - Break complex tasks into smaller, manageable steps
   - Use clear, descriptive task names"""

@register_tool(category="Agent", name_cn="读取待办", risk_level="low")
def TodoRead(**kwargs) -> str:
    """
    Use this tool to read your todo list.
    """
    # Override docstring with full description
    TodoRead.__doc__ = TODO_READ_DESC
    
    session_id = kwargs.get("session_id") or kwargs.get("parent_session_id")
    sessions_dir = kwargs.get("sessions_dir", "sessions")
    if not session_id:
        return _xml_response("error", "Session ID not found in context.")
        
    manager = TodoManager(session_id, sessions_dir=sessions_dir)
    todos = manager.get_todos()
    
    pending_count = len([t for t in todos if t.status != "completed"])
    
    output = {
        "title": f"{pending_count} todos",
        "output": json.dumps([t.to_dict() for t in todos], indent=2, ensure_ascii=False),
        "metadata": {
            "todos": [t.to_dict() for t in todos]
        }
    }
    
    # Return formatted string similar to other tools
    return _xml_response("done", output['output'])

@register_tool(category="Agent", name_cn="写入待办", risk_level="low")
def TodoWrite(todos: List[Dict[str, Any]], merge: bool = False, summary: Optional[str] = None, **kwargs) -> str:
    """
    Use this tool to create and manage a structured task list for your current coding session.
    
    Args:
        todos: Array of todo items. Each item should have 'content', 'status' (pending/in_progress/completed), 'id', and 'priority'.
        merge: Whether to merge with existing todos.
        summary: Optional summary of work accomplished.
    """
    # Override docstring with full description
    TodoWrite.__doc__ = TODO_WRITE_DESC
    
    session_id = kwargs.get("session_id") or kwargs.get("parent_session_id")
    sessions_dir = kwargs.get("sessions_dir", "sessions")
    if not session_id:
        return _xml_response("error", "Session ID not found in context.")
        
    manager = TodoManager(session_id, sessions_dir=sessions_dir)
    updated_todos = manager.update_todos(todos, merge=merge)
    
    pending_count = len([t for t in updated_todos if t.status != "completed"])
    
    output = {
        "title": f"{pending_count} todos",
        "output": json.dumps([t.to_dict() for t in updated_todos], indent=2, ensure_ascii=False),
        "metadata": {
            "todos": [t.to_dict() for t in updated_todos]
        }
    }
    
    result_str = output['output']
        
    return _xml_response("done", result_str)
