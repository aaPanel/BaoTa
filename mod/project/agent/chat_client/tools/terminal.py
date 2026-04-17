from . import register_tool
from .base import _xml_response
import threading
import subprocess
import time
import uuid
import os

# --- Command Manager for Non-blocking Commands ---
class CommandManager:
    def __init__(self):
        self.commands = {}
        self.lock = threading.Lock()

    def start_command(self, command: str, cwd: str) -> tuple:
        cmd_id = str(uuid.uuid4())
        
        shell_cmd = command
        if os.name == 'nt':
             shell_cmd = ["powershell", "-Command", command]
        
        try:
            process = subprocess.Popen(
                shell_cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                shell=False if os.name == 'nt' else True 
            )
        except Exception as e:
            return None, str(e)

        cmd_info = {
            "id": cmd_id,
            "process": process,
            "output": [], # List of lines
            "status": "running",
            "start_time": time.time(),
            "cwd": cwd,
            "command": command
        }
        
        with self.lock:
            self.commands[cmd_id] = cmd_info

        # Start thread to read output
        t = threading.Thread(target=self._read_output, args=(cmd_id, process))
        t.daemon = True
        t.start()
        
        return cmd_id, None

    def _read_output(self, cmd_id, process):
        try:
            for line in iter(process.stdout.readline, ''):
                with self.lock:
                    if cmd_id in self.commands:
                        self.commands[cmd_id]["output"].append(line)
        except Exception:
            pass
        finally:
            try:
                process.stdout.close()
            except:
                pass
            
            return_code = process.wait()
            
            with self.lock:
                if cmd_id in self.commands:
                    self.commands[cmd_id]["status"] = "done"
                    self.commands[cmd_id]["returncode"] = return_code

    def get_status(self, cmd_id: str, priority: str = "bottom", limit: int = 1000):
        with self.lock:
            if cmd_id not in self.commands:
                return None
            
            cmd = self.commands[cmd_id]
            output_lines = cmd["output"]
            
            if priority == "bottom":
                lines = output_lines[-limit:]
            else:
                lines = output_lines[:limit]
                
            return {
                "status": cmd["status"],
                "returncode": cmd.get("returncode"),
                "output": "".join(lines),
                "cwd": cmd["cwd"],
                "command": cmd["command"]
            }

    def stop_command(self, cmd_id: str):
        with self.lock:
            if cmd_id not in self.commands:
                return False
            
            cmd = self.commands[cmd_id]
            if cmd["status"] == "running":
                try:
                    cmd["process"].terminate() 
                    cmd["status"] = "stopped"
                except:
                    pass
                return True
            return False

_CMD_MANAGER = CommandManager()

@register_tool(category="Agent", name_cn="运行命令", risk_level="high")
class RunCommand:
    """
    Executes a given bash command in a persistent shell session with optional timeout, ensuring proper handling and security measures.
    
    All commands run in ${directory} by default. Use the `workdir` parameter if you need to run a command in a different directory. AVOID using `cd <directory> && <command>` patterns - use `workdir` instead.
    
    IMPORTANT: This tool is for terminal operations like git, npm, docker, etc. DO NOT use it for file operations (reading, writing, editing, searching, finding files) - use the specialized tools for this instead.
    
    Before executing the command, please follow these steps:
    
    1. Directory Verification:
       - If the command will create new directories or files, first use `ls` to verify the parent directory exists and is the correct location
       - For example, before running "mkdir foo/bar", first use `ls foo` to check that "foo" exists and is the intended parent directory
    
    2. Command Execution:
       - Always quote file paths that contain spaces with double quotes (e.g., rm "path with spaces/file.txt")
       - Examples of proper quoting:
         - mkdir "/Users/name/My Documents" (correct)
         - mkdir /Users/name/My Documents (incorrect - will fail)
         - python "/path/with spaces/script.py" (correct)
         - python /path/with spaces/script.py (incorrect - will fail)
       - After ensuring proper quoting, execute the command.
       - Capture the output of the command.
    
    Usage notes:
      - The command argument is required.
      - You can specify an optional timeout in milliseconds. If not specified, commands will time out after 120000ms (2 minutes).
      - It is very helpful if you write a clear, concise description of what this command does in 5-10 words.
      - If the output exceeds ${maxLines} lines or ${maxBytes} bytes, it will be truncated and the full output will be written to a file. You can use Read with offset/limit to read specific sections or Grep to search the full content. Because of this, you do NOT need to use `head`, `tail`, or other truncation commands to limit output - just run the command directly.
    
      - Avoid using Bash with the `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`, or `echo` commands, unless explicitly instructed or when these commands are truly necessary for the task. Instead, always prefer using the dedicated tools for these commands:
        - File search: Use Glob (NOT find or ls)
        - Content search: Use Grep (NOT grep or rg)
        - Read files: Use Read (NOT cat/head/tail)
        - Edit files: Use Edit (NOT sed/awk)
        - Write files: Use Write (NOT echo >/cat <<EOF)
        - Communication: Output text directly (NOT echo/printf)
      - When issuing multiple commands:
        - If the commands are independent and can run in parallel, make multiple Bash tool calls in a single message. For example, if you need to run "git status" and "git diff", send a single message with two Bash tool calls in parallel.
        - If the commands depend on each other and must run sequentially, use a single Bash call with '&&' to chain them together (e.g., `git add . && git commit -m "message" && git push`). For instance, if one operation must complete before another starts (like mkdir before cp, Write before Bash for git operations, or git add before git commit), run these operations sequentially instead.
        - Use ';' only when you need to run commands sequentially but don't care if earlier commands fail
        - DO NOT use newlines to separate commands (newlines are ok in quoted strings)
      - AVOID using `cd <directory> && <command>`. Use the `workdir` parameter to change directories instead.
        <good-example>
        Use workdir="/foo/bar" with command: pytest tests
        </good-example>
        <bad-example>
        cd /foo/bar && pytest tests
        </bad-example>
    
    Args:
        command: The command to execute
        blocking: Whether to block and wait for the command to finish.
        cwd: The working directory to run the command in.
        timeout: Optional timeout in milliseconds (default 120000ms = 2 mins). Only applies if blocking=True.
        description: Clear, concise description of what this command does.
    """
    def execute(self, command: str, blocking: bool = True, cwd: str = None, timeout: int = 120000, description: str = None) -> str:
        if not cwd:
            cwd = os.getcwd()
            
        if blocking:
            try:
                shell_cmd = command
                if os.name == 'nt':
                     shell_cmd = ["powershell", "-Command", command]
                     
                # timeout is in ms, subprocess.run takes seconds
                timeout_sec = timeout / 1000.0
                
                start_time = time.time()
                result = subprocess.run(
                    shell_cmd,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    shell=False if os.name == 'nt' else True,
                    timeout=timeout_sec
                )
                output = result.stdout + result.stderr
                
                # Format output similar to bash tool
                metadata = f"Exit Code: {result.returncode}\nDuration: {time.time() - start_time:.2f}s"
                
                final_output = output
                if description:
                    final_output = f"Description: {description}\n\n{output}"
                    
                return _xml_response("done", final_output)
                
            except subprocess.TimeoutExpired:
                 return _xml_response("error", f"Command timed out after {timeout} ms")
            except Exception as e:
                return _xml_response("error", str(e))
        else:
            cmd_id, err = _CMD_MANAGER.start_command(command, cwd)
            if err:
                return _xml_response("error", err)
                
            result = f"""<terminal_id>new</terminal_id>
<terminal_cwd>{cwd}</terminal_cwd>
Note: Command ID is provided for you to check command status later.
<command_id>{cmd_id}</command_id>
The command is running, you need to call check_command_status tool to get more logs to know whether it's running successfully.
"""
            return _xml_response("running", result)

@register_tool(category="Agent", name_cn="检查命令状态", risk_level="low")
class CheckCommandStatus:
    """
    Check the status and output of a non-blocking command.
    
    Args:
        command_id: ID of the command to get status for.
        output_priority: Priority for displaying command output. 'bottom' (show newest lines) or 'top'.
    """
    def execute(self, command_id: str, output_priority: str = "bottom") -> str:
        status_info = _CMD_MANAGER.get_status(command_id, output_priority)
        if not status_info:
            return _xml_response("error", "Command ID not found")
            
        logs = status_info["output"]
        status_str = status_info["status"]
        
        result = f"""<terminal_id>unknown</terminal_id>
<terminal_cwd>{status_info['cwd']}</terminal_cwd>
<command_id>{command_id}</command_id>
<command_status>{status_str.capitalize()}</command_status><command_run_logs>
```
{logs}
```
</command_run_logs>
"""
        return _xml_response("done", result)

@register_tool(category="Agent", name_cn="停止命令", risk_level="medium")
class StopCommand:
    """
    Terminate a running command.
    
    Args:
        command_id: The command id of the running command that you need to terminate.
    """
    def execute(self, command_id: str) -> str:
        if _CMD_MANAGER.stop_command(command_id):
            return _xml_response("done", f"Command {command_id} stopped.")
        else:
            return _xml_response("error", f"Failed to stop command {command_id} (not running or not found).")
