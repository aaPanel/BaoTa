import os
from . import register_tool
from .base import _xml_response

@register_tool(category="Agent", name_cn="任务总结", risk_level="low")
def TaskSummary(content: str, **kwargs) -> str:
    """
    Use this tool to save the final summary of the current task.
    You should call this tool at the very end of the task execution to document what has been achieved.
    
    Args:
        content: The detailed summary of the task execution, including what was done, any files created or modified, and any important notes. Markdown format is preferred.
    """
    session_id = kwargs.get("session_id") or kwargs.get("parent_session_id")
    sessions_dir = kwargs.get("sessions_dir", "sessions")
    
    if not session_id:
        return _xml_response("error", "Session ID not found in context. This tool requires a session context.")
            
    return _xml_response("done", content)
