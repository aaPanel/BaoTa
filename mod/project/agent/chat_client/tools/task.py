from typing import Optional, Generator, Dict, Any
import json
import uuid
import os
from . import register_tool
from .base import _xml_response

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AgentDefinition:
    name: str
    description: str
    allowed_tools: List[str]
    system_prompt_template: str

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._register_default_agents()

    def register(self, agent: AgentDefinition):
        self._agents[agent.name] = agent

    def get(self, name: str) -> Optional[AgentDefinition]:
        return self._agents.get(name)

    def list_agents(self) -> List[AgentDefinition]:
        return list(self._agents.values())

    def _register_default_agents(self):
        # Search Agent
        self.register(AgentDefinition(
            name="search",
            description="A specialist for searching the codebase and file system. Use this for exploration and information gathering.",
            allowed_tools=["Glob", "Grep", "LS", "Read", "CheckCommandStatus", "RunCommand"],
            system_prompt_template="You are a search specialist. Your goal is to find information in the codebase efficiently. Use Glob and Grep tools to locate files and content. Use Read to inspect file contents. Do not modify files."
        ))

        # Planner Agent
        self.register(AgentDefinition(
            name="planner",
            description="A specialist for planning tasks and managing todo lists.",
            allowed_tools=["TodoWrite", "Read", "Task"],
            system_prompt_template="You are a planner. Your goal is to break down complex tasks into manageable steps. Use the TodoWrite tool to manage the task list. You can delegate subtasks to other agents using the Task tool."
        ))

        # Coder Agent
        self.register(AgentDefinition(
            name="coder",
            description="A specialist for writing and modifying code.",
            allowed_tools=["Glob", "Grep", "LS", "Read", "Write", "DeleteFile", "SearchReplace", "RunCommand", "CheckCommandStatus", "StopCommand", "Task"],
            system_prompt_template="You are a coding specialist. Your goal is to implement features and fix bugs. You can read and write files. You can also run commands to verify your work. If you need to search extensively, delegate to the search agent."
        ))

# Global registry instance
agent_registry = AgentRegistry()


@register_tool(category="Agent", name_cn="Task子代理", risk_level="medium")
def Task(description: str, prompt: str, subagent_type: str, task_id: Optional[str] = None, **kwargs) -> str:
    """
    Launch a sub-agent to handle a complex task autonomously.
    
    Args:
        description: A short description of the task.
        prompt: The detailed instructions for the agent.
        subagent_type: The type of agent to use ('search', 'planner', 'coder').
        task_id: Optional ID to resume a previous task session.
    
    
Launch a new agent to handle complex, multistep tasks autonomously.

Available agent types and the tools they have access to:
["search", "planner", "coder"]

When using the Task tool, you must specify a subagent_type parameter to select which agent type to use.

When to use the Task tool:
- When you are instructed to execute custom slash commands. Use the Task tool with the slash command invocation as the entire prompt. The slash command can take arguments. For example: Task(description="Check the file", prompt="/check-file path/to/file.py")

When NOT to use the Task tool:
- If you want to read a specific file path, use the Read or Glob tool instead of the Task tool, to find the match more quickly
- If you are searching for a specific class definition like "class Foo", use the Glob tool instead, to find the match more quickly
- If you are searching for code within a specific file or set of 2-3 files, use the Read tool instead of the Task tool, to find the match more quickly
- Other tasks that are not related to the agent descriptions above


Usage notes:
1. Launch multiple agents concurrently whenever possible, to maximize performance; to do that, use a single message with multiple tool uses
2. When the agent is done, it will return a single message back to you. The result returned by the agent is not visible to the user. To show the user the result, you should send a text message back to the user with a concise summary of the result. The output includes a task_id you can reuse later to continue the same subagent session.
3. Each agent invocation starts with a fresh context unless you provide task_id to resume the same subagent session (which continues with its previous messages and tool outputs). When starting fresh, your prompt should contain a highly detailed task description for the agent to perform autonomously and you should specify exactly what information the agent should return back to you in its final and only message to you.
4. The agent's outputs should generally be trusted
5. Clearly tell the agent whether you expect it to write code or just to do research (search, file reads, web fetches, etc.), since it is not aware of the user's intent. Tell it how to verify its work if possible (e.g., relevant test commands).
6. If the agent description mentions that it should be used proactively, then you should try your best to use it without the user having to ask for it first. Use your judgement.

Example usage (NOTE: The agents below are fictional examples for illustration only - use the actual agents listed above):

<example_agent_descriptions>
"code-reviewer": use this agent after you are done writing a significant piece of code
"greeting-responder": use this agent when to respond to user greetings with a friendly joke
</example_agent_description>

<example>
user: "Please write a function that checks if a number is prime"
assistant: Sure let me write a function that checks if a number is prime
assistant: First let me use the Write tool to write a function that checks if a number is prime
assistant: I'm going to use the Write tool to write the following code:
<code>
function isPrime(n) {
  if (n <= 1) return false
  for (let i = 2; i * i <= n; i++) {
    if (n % i === 0) return false
  }
  return true
}
</code>
<commentary>
Since a significant piece of code was written and the task was completed, now use the code-reviewer agent to review the code
</commentary>
assistant: Now let me use the code-reviewer agent to review the code
assistant: Uses the Task tool to launch the code-reviewer agent
</example>

<example>
user: "Hello"
<commentary>
Since the user is greeting, use the greeting-responder agent to respond with a friendly joke
</commentary>
assistant: "I'm going to use the Task tool to launch the with the greeting-responder agent"
</example>
    """
    
    # Deferred import to avoid circular dependency
    from ..agent import Agent

    # 1. Validate Agent Type
    agent_def = agent_registry.get(subagent_type)
    if not agent_def:
        available = [a.name for a in agent_registry.list_agents()]
        return _xml_response("error", f"Unknown agent type: '{subagent_type}'. Available agents: {', '.join(available)}")

    # 2. Session Management
    if task_id:
        session_id = task_id
    else:
        # Create new session ID
        session_id = str(uuid.uuid4())

    # 3. Configure Agent
    # We need to construct a config that enables the specific tools for this agent
    # and sets the system prompt.
    
    # Get current working directory
    cwd = os.getcwd()
    
    # Get parent config if available
    parent_config = kwargs.get("parent_config", {})
    parent_session_id = kwargs.get("parent_session_id")
    
    # Start with default base config
    config = {
        "model_name": "gpt-4o", # Default
        "cwd": cwd,
        "code_mode": True, 
        "max_tool_iterations": 20
    }
    
    # Merge parent config (if any), but be careful not to overwrite critical agent-specific fields yet
    if parent_config:
        # Update config with parent config, but exclude 'tools' and 'system_prompt' which are specific to the subagent
        # We also want to preserve 'cwd' if parent has it
        for k, v in parent_config.items():
            if k not in ["tools", "system_prompt"]:
                config[k] = v
        
        # Determine sessions_dir
        # If we have a parent session, the sub-agent session should be stored inside it
        if parent_session_id:
            parent_sessions_dir = parent_config.get("sessions_dir", "sessions")
            # Structure: sessions/parent_id
            # The Agent class will append its session_id: sessions/parent_id/sub_id
            # So we set sessions_dir to: sessions/parent_id
            config["sessions_dir"] = os.path.join(parent_sessions_dir, parent_session_id)
    
    # Force agent-specific configuration
    config.update({
        "tools": agent_def.allowed_tools,
        "system_prompt": agent_def.system_prompt_template
    })

    # 4. Initialize Agent
    agent = Agent(session_id=session_id, config=config)
    
    try:
        # 5. Execute Agent Loop
        # Agent.chat is a generator. We need to consume it to let the agent run.
        # We collect the final response content.
        
        full_response = ""
        
        # Add a clear instruction to the prompt
        full_prompt = f"Task: {description}\n\nInstructions:\n{prompt}"
        
        generator = agent.chat(full_prompt)
        
        for chunk in generator:
            if chunk.get("type") == "content":
                full_response += chunk.get("response", "")
            elif chunk.get("type") == "error":
                return _xml_response("error", f"Agent error: {chunk.get('data')}")
                
        # 6. Return Result
        output = [
            f"task_id: {session_id}",
            "",
            "<task_result>",
            full_response,
            "</task_result>"
        ]
        
        return _xml_response("done", "\n".join(output))

    except Exception as e:
        return _xml_response("error", f"Task execution failed: {str(e)}")
    finally:
        # Clean up agent resources
        if hasattr(agent, "close"):
            agent.close()
