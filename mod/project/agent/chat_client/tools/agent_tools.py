from . import register_tool
import os
import glob
import re
import shutil
import time
from typing import List

# Import shared helper
from .base import _xml_response

import subprocess
import os, sys;

os.chdir('/www/server/panel/');
sys.path.insert(0, 'class/');
sys.path.insert(0, '/www/server/panel/');
import public;


# --- Tools ---

@register_tool(category="Agent", name_cn="Glob查找", risk_level="low")
def Glob(pattern: str, path: str = None) -> str:
    """
    - Fast file pattern matching tool that works with any codebase size
    - Supports glob patterns like "**/*.js" or "src/**/*.ts"
    - Returns matching file paths sorted by modification time
    - Use this tool when you need to find files by name patterns
    - When you are doing an open-ended search that may require multiple rounds of globbing and grepping, use the Task tool instead
    - You have the capability to call multiple tools in a single response. It is always better to speculatively perform multiple searches as a batch that are potentially useful.
    
    Args:
        pattern: The glob pattern to match files against
        path: The directory to search in. If not specified, the current working directory will be used. IMPORTANT: Omit this field to use the default directory. DO NOT enter "undefined" or "null" - simply omit it for the default behavior. Must be a valid directory path if provided.
    """
    if not path:
        path = os.getcwd()
    
    try:
        if not os.path.exists(path):
             return _xml_response("error", f"Path not found: {path}")

        search_path = os.path.join(path, pattern)
        files = glob.glob(search_path, recursive=True)
        
        # Filter only files and sort by mtime (descending)
        file_stats = []
        for f in files:
            if os.path.isfile(f):
                try:
                    mtime = os.path.getmtime(f)
                    file_stats.append((f, mtime))
                except:
                    pass
        
        file_stats.sort(key=lambda x: x[1], reverse=True)
        
        limit = 100
        truncated = False
        if len(file_stats) > limit:
            file_stats = file_stats[:limit]
            truncated = True
            
        output = [f[0] for f in file_stats]
        
        if not output:
            return _xml_response("done", "No files found")
            
        result = "\n".join(output)
        if truncated:
            result += f"\n\n(Results are truncated: showing first {limit} results. Consider using a more specific path or pattern.)"
            
        return _xml_response("done", result)
    except Exception as e:
        return _xml_response("error", str(e))

@register_tool(category="Agent", name_cn="Grep搜索", risk_level="low")
def Grep(pattern: str, include: str = None, path: str = None) -> str:
    r"""
    - Fast content search tool that works with any codebase size
    - Searches file contents using regular expressions
    - Supports full regex syntax (eg. "log.*Error", "function\s+\w+", etc.)
    - Filter files by pattern with the include parameter (eg. "*.js", "*.{ts,tsx}")
    - Returns file paths and line numbers with at least one match sorted by modification time
    - Use this tool when you need to find files containing specific patterns
    - If you need to identify/count the number of matches within files, use the Bash tool with `rg` (ripgrep) directly. Do NOT use `grep`.
    - When you are doing an open-ended search that may require multiple rounds of globbing and grepping, use the Task tool instead
    
    Args:
        pattern: The regex pattern to search for in file contents
        path: The directory to search in. Defaults to the current working directory.
        include: File pattern to include in the search (e.g. "*.js", "*.{ts,tsx}")
    """
    if not path:
        path = os.getcwd()
        
    try:
        import glob as glob_module
        
        # 1. Find files
        files_to_search = []
        if os.path.isfile(path):
            files_to_search = [path]
        else:
            search_glob = include if include else "**/*"
            # Support simple brace expansion if needed, but glob doesn't support it natively in all versions
            # For simplicity, we assume standard glob patterns
            candidates = glob_module.glob(os.path.join(path, search_glob), recursive=True)
            files_to_search = [f for f in candidates if os.path.isfile(f)]

        regex = re.compile(pattern)
        matches = []
        MAX_LINE_LENGTH = 2000
        
        for file_path in files_to_search:
            try:
                # Check file size/binary? Skip for now to keep simple
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    try:
                         mtime = os.path.getmtime(file_path)
                    except:
                         mtime = 0
                         
                    for i, line in enumerate(lines):
                        if regex.search(line):
                            matches.append({
                                "path": file_path,
                                "lineNum": i + 1,
                                "lineText": line.rstrip(),
                                "mtime": mtime
                            })
            except Exception:
                continue

        # Sort by mtime desc
        matches.sort(key=lambda x: x["mtime"], reverse=True)
        
        limit = 100
        truncated = len(matches) > limit
        final_matches = matches[:limit] if truncated else matches
        
        if not final_matches:
            return _xml_response("done", "No files found")
            
        output_lines = [f"Found {len(matches)} matches{f' (showing first {limit})' if truncated else ''}"]
        
        current_file = ""
        for match in final_matches:
            if current_file != match["path"]:
                if current_file != "":
                    output_lines.append("")
                current_file = match["path"]
                output_lines.append(f"{match['path']}:")
            
            line_text = match["lineText"]
            if len(line_text) > MAX_LINE_LENGTH:
                line_text = line_text[:MAX_LINE_LENGTH] + "..."
            output_lines.append(f"  Line {match['lineNum']}: {line_text}")
            
        if truncated:
            output_lines.append("")
            output_lines.append(f"(Results truncated: showing {limit} of {len(matches)} matches. Consider using a more specific path or pattern.)")
            
        return _xml_response("done", "\n".join(output_lines))

    except Exception as e:
        return _xml_response("error", str(e))

@register_tool(category="Agent", name_cn="列出目录", risk_level="low")
def LS(path: str = None, ignore: List[str] = None) -> str:
    """
    Lists files and directories in a given path. The path parameter must be absolute; omit it to use the current workspace directory. You can optionally provide an array of glob patterns to ignore with the ignore parameter. You should generally prefer the Glob and Grep tools, if you know which directories to search.
    
    Args:
        path: The absolute path to the directory to list (must be absolute, not relative).
        ignore: List of glob patterns to ignore.
    """
    if not path:
        path = os.getcwd()
        
    try:
        if not os.path.exists(path):
            return _xml_response("error", "Path not found")
            
        DEFAULT_IGNORE = [
            "node_modules", "__pycache__", ".git", "dist", "build", "target",
            "vendor", "bin", "obj", ".idea", ".vscode", ".zig-cache", "zig-out",
            "coverage", "tmp", "temp", ".cache", "logs",
            ".venv", "venv", "env"
        ]
        
        ignore_patterns = DEFAULT_IGNORE + (ignore if ignore else [])
        
        LIMIT = 100
        
        def should_ignore(name):
            return name in ignore_patterns or any(glob.fnmatch.fnmatch(name, p) for p in ignore_patterns)
        
        try:
            entries = os.listdir(path)
        except PermissionError:
            return _xml_response("error", f"Permission denied: {path}")
        
        dirs = []
        files = []
        for entry in entries:
            if should_ignore(entry):
                continue
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)
        
        dirs.sort()
        files.sort()
        
        output_lines = [f"{path}/"]
        
        for d in dirs:
            subdir_path = os.path.join(path, d)
            output_lines.append(f"  {d}/")
            
            try:
                sub_entries = os.listdir(subdir_path)
            except PermissionError:
                continue
            
            sub_dirs = []
            sub_files = []
            for entry in sub_entries:
                if should_ignore(entry):
                    continue
                entry_path = os.path.join(subdir_path, entry)
                if os.path.isdir(entry_path):
                    sub_dirs.append(entry)
                else:
                    sub_files.append(entry)
            
            sub_dirs.sort()
            sub_files.sort()
            
            count = 0
            truncated = False
            for sub_d in sub_dirs:
                if count >= LIMIT:
                    truncated = True
                    break
                output_lines.append(f"    {sub_d}/")
                count += 1
            
            for sub_f in sub_files:
                if count >= LIMIT:
                    truncated = True
                    break
                output_lines.append(f"    {sub_f}")
                count += 1
            
            if truncated:
                output_lines.append(f"    ... (当前目录仅展示{LIMIT}条，若需要更多请再次使用LS工具查看该目录)")
        
        for f in files:
            output_lines.append(f"  {f}")
        
        return _xml_response("done", "\n".join(output_lines))
    except Exception as e:
        return _xml_response("error", str(e))

@register_tool(category="Agent", name_cn="读取文件", risk_level="medium")
def Read(file_path: str, offset: int = 1, limit: int = 2000) -> str:
    """
    Read a file or directory from the local filesystem. If the path does not exist, an error is returned.
    
    Usage:
    - The filePath parameter should be an absolute path.
    - By default, this tool returns up to 2000 lines from the start of the file.
    - The offset parameter is the line number to start from (1-indexed).
    - To read later sections, call this tool again with a larger offset.
    - Use the grep tool to find specific content in large files or files with long lines.
    - If you are unsure of the correct file path, use the glob tool to look up filenames by glob pattern.
    - Contents are returned with each line prefixed by its line number as `<line>: <content>`. For example, if a file has contents "foo\\n", you will receive "1: foo\\n". For directories, entries are returned one per line (without line numbers) with a trailing `/` for subdirectories.
    - Any line longer than 2000 characters is truncated.
    - Call this tool in parallel when you know there are multiple files you want to read.
    - Avoid tiny repeated slices (30 line chunks). If you need more context, read a larger window.
    - This tool can read image files and PDFs and return them as file attachments.
    
    Args:
        file_path: The absolute path to the file to read.
        offset: The line number to start reading from (must be at least 1). Only provide if the file is too large to read at once.
        limit: The number of lines to read (must be at least 1, cannot be negative). Only provide if the file is too large to read at once.
    """
    try:
        if not os.path.exists(file_path):
            return _xml_response("error", f"File not found: {file_path}")
            
        if os.path.isdir(file_path):
            # Directory listing logic
            entries = os.listdir(file_path)
            entries.sort()
            
            start = offset - 1
            sliced = entries[start : start + limit]
            truncated = (start + len(sliced)) < len(entries)
            
            entry_lines = []
            for entry in sliced:
                full_p = os.path.join(file_path, entry)
                if os.path.isdir(full_p):
                    entry_lines.append(entry + "/")
                else:
                    entry_lines.append(entry)
            
            output = f"<path>{file_path}</path>\n<type>directory</type>\n<entries>\n"
            output += "\n".join(entry_lines)
            if truncated:
                output += f"\n(Showing {len(sliced)} of {len(entries)} entries. Use 'offset' parameter to read beyond entry {offset + len(sliced)})"
            else:
                output += f"\n({len(entries)} entries)"
            output += "\n</entries>"
            return _xml_response("done", output)

        # Check binary (simple check)
        BINARY_EXTENSIONS = {
            '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.class', '.jar', '.war', '.7z',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        }
        ext = os.path.splitext(file_path)[1].lower()
        if ext in BINARY_EXTENSIONS:
            return _xml_response("done", f"<path>{file_path}</path>\n<type>binary</type>\n<content>Binary file detected (extension {ext}). Cannot read as text.</content>")

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            
        total_lines = len(lines)
        start_index = max(0, offset - 1)
        end_index = min(total_lines, start_index + limit)
        
        selected_lines = lines[start_index:end_index]
        
        content_lines = []
        for i, line in enumerate(selected_lines):
            content_lines.append(f"{start_index + i + 1}: {line.rstrip()}")
            
        output = f"<path>{file_path}</path>\n<type>file</type>\n<content>\n"
        output += "\n".join(content_lines)
        
        if end_index < total_lines:
            output += f"\n\n(Showing lines {offset}-{end_index} of {total_lines}. Use offset={end_index + 1} to continue.)"
        else:
            output += f"\n\n(End of file - total {total_lines} lines)"
            
        output += "\n</content>"
            
        return _xml_response("done", output)
    except Exception as e:
        return _xml_response("error", str(e))

@register_tool(category="Agent", name_cn="写入文件", risk_level="high")
def Write(file_path: str, content: str) -> str:
    """
    Writes a file to the local filesystem.
    
    Usage:
    - This tool will overwrite the existing file if there is one at the provided path.
    - If this is an existing file, you MUST use the Read tool first to read the file's contents. This tool will fail if you did not read the file first.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
    - Only use emojis if the user explicitly requests it. Avoid writing emojis to files unless asked.
    
    Args:
        content: The content to write to the file
        file_path: The absolute path to the file to write (must be absolute, not relative)
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return _xml_response("done", f"Wrote file successfully at: {file_path}")
    except Exception as e:
        return _xml_response("error", str(e))

@register_tool(category="Agent", name_cn="删除文件", risk_level="high")
def DeleteFile(file_paths: List[str]) -> str:
    """
    Delete files or directories.
    
    Args:
        file_paths: The list of file paths you want to delete, you MUST set file path to absolute path.
    """
    deleted = []
    errors = []
    for path in file_paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            deleted.append(path)
        except Exception as e:
            errors.append(f"{path}: {str(e)}")
            
    result = "<file_changes>\nThese files is deleted in this toolcall:\n<deleted_files>\n"
    for p in deleted:
        result += f"  - {p}\n"
    result += "</deleted_files>\n</file_changes>"
    
    if errors:
        result += f"\nErrors:\n" + "\n".join(errors)
        
    return _xml_response("done", result)


def _run_shell_cmd(command: list, timeout: int = 300) -> tuple:
    """
    Common function to execute shell commands.
    Returns (success: bool, output: str)
    """
    try:
        # Use shell=False for security when passing a list
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()
        
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Error: Command timed out after {timeout} seconds."
    except FileNotFoundError:
        return False, f"Error: Command not found: {command[0]}"
    except Exception as e:
        return False, f"Error executing command: {str(e)}"


@register_tool(category="系统", name_cn="获取服务状态", risk_level="low")
def get_service_status(service_name: str) -> str:
    """
    获取系统服务的状态 (Linux)。

    Args:
        service_name: 服务名称 (例如：'nginx', 'docker', 'mysql')。
    """
    success, output = _run_shell_cmd(["systemctl", "status", service_name])
    
    # Summary of first 20 lines
    summary = "\n".join(output.splitlines()[:20])
    
    if success:
        result = f"✅ Service '{service_name}' is active/running (or exited successfully).\n{summary}"
        return _xml_response("done", result)
    else:
        if "not found" in output.lower():
            return _xml_response("error", f"❌ Service '{service_name}' not found.")
        result = f"⚠️ Service '{service_name}' status check failed or inactive.\n{summary}"
        return _xml_response("done", result)


@register_tool(category="系统", name_cn="重启服务", risk_level="high")
def restart_service(service_name: str) -> str:
    """
    尝试重启指定的系统服务 (通常需要 root 权限)。

    Args:
        service_name: 服务名称。
    """
    success, output = _run_shell_cmd(["systemctl", "restart", service_name])
    if success:
        return _xml_response("done", f"✅ Service '{service_name}' restarted successfully.")
    else:
        return _xml_response("error", f"❌ Failed to restart '{service_name}':\n{output}")


@register_tool(category="系统", name_cn="获取系统资源", risk_level="low")
def get_system_resources() -> str:
    """
    获取当前系统 CPU 负载、内存使用和磁盘空间信息。

    returns:
        OS、 Load Average、 Memory、 Disk 信息字符串
    """
    try:
        # Load Average
        try:
            load1, load5, load15 = os.getloadavg()
            load_info = f"Load Avg: {load1:.2f}, {load5:.2f}, {load15:.2f}"
        except OSError:
            load_info = "Load Avg: N/A (Windows?)"
        
        # Memory
        mem_info = "Mem: Unknown"
        if os.path.exists('/proc/meminfo'):
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                total = 0
                available = 0
                for line in lines:
                    if 'MemTotal' in line:
                        total = int(line.split()[1]) // 1024  # MB
                    if 'MemAvailable' in line:
                        available = int(line.split()[1]) // 1024  # MB
                used = total - available
                percent = (used / total * 100) if total > 0 else 0
                mem_info = f"Mem: {used}MB/{total}MB ({percent:.1f}%)"
        
        # Disk
        disk = shutil.disk_usage("/")
        total_gb = disk.total // (1024 ** 3)
        used_gb = disk.used // (1024 ** 3)
        disk_percent = (disk.used / disk.total * 100)
        disk_info = f"Disk (/): {used_gb}GB/{total_gb}GB ({disk_percent:.1f}%)"
        os_info = public.get_os_version()
        
        result = f"{load_info}\n{mem_info}\n{disk_info}\nOS: {os_info}"
        return _xml_response("done", result)
    except Exception as e:
        return _xml_response("error", f"Error getting resources: {str(e)}")

@register_tool(category="网络", name_cn="域名检测", risk_level="low")
def check_domain(domain: str) -> str:
    """
    检测域名解析 (使用 dig 或 nslookup)。
    """
    # Try dig first
    success, output = _run_shell_cmd(["dig", "+short", domain])
    if success and output:
        return _xml_response("done", f"Dig result for {domain}:\n{output}")
    
    # Fallback to nslookup
    success, output = _run_shell_cmd(["nslookup", domain])
    if success:
        return _xml_response("done", f"Nslookup result for {domain}:\n{output}")
    
    return _xml_response("error", f"Error resolving domain {domain}.")


@register_tool(category="网络", name_cn="Ping检测", risk_level="low")
def ping_target(target: str) -> str:
    """
    Ping 目标主机 (发送 4 个包)。
    """
    success, output = _run_shell_cmd(["ping", "-c", "4", target])
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Ping failed:\n{output}")


@register_tool(category="网络", name_cn="Curl请求", risk_level="low")
def curl_url(url: str) -> str:
    """
    使用 curl 获取网页内容。
    """
    success, output = _run_shell_cmd(["curl", "-L", "-s", "--max-time", "10", url])
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Curl failed:\n{output}")


@register_tool(category="网站", name_cn="获取网站列表(不包含Docker站点)", risk_level="medium")
def get_sites() -> str:
    """
    获取在宝塔面板部署的全部网站列表（域名）;

    returns :
        [
            {
                "id": 1,
                "name": "www.example.com" or "ip_port", #网站域名或绑定的IP端口
                "project_type": "PHP|html" #网站类型

            }
        ]
    """
    import json
    sites = public.M('sites').field('id,name,project_type').select()
    return _xml_response("done", json.dumps(sites, ensure_ascii=False, indent=2))


@register_tool(category="网站", name_cn="获取网站配置", risk_level="medium")
def get_sites_conf(site_name: str) -> str:
    """
    获取网站的nginx或apache配置文件内容;

    Args:
        site_name: 网站域名或绑定的IP端口;

    returns :
        Nginx配置文件内容字符串;
    """
    
    site_data = public.M('sites').field('name,project_type').where("name=?", site_name).select()
    if not site_data:
        return _xml_response("error", f"Error: site '{site_name}' not found in panel.")
    
    res = site_data[0]['project_type'].lower()
    if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
        res = ''
    else:
        res = res + '_'
    
    full_path = f"/www/server/panel/vhost/nginx/{res}{site_name}.conf"
    if not os.path.exists(full_path):
        full_path = f"/www/server/panel/vhost/apache/{res}{site_name}.conf"
        if not os.path.exists(full_path):
            return _xml_response("error", f"Error: configuration for site '{site_name}' not found.")
    
    with open(full_path, 'r') as f:
        config_content = f.read()
    return _xml_response("done", config_content)


@register_tool(category="网站", name_cn="获取网站访问日志", risk_level="medium")
def get_sites_logs(site_name: str) -> str:
    """
    获取网站的原生访问日志(最大1000行);

    Args:
        site_name: 网站域名或绑定的IP端口;

    returns :
        访问日志内容;
    """
    import json
    from logsModel.siteModel import main
    logs_model = main()
    
    logs = logs_model.GetSiteLogs(public.to_dict_obj({"siteName": site_name}))
    return _xml_response("done", json.dumps(logs, ensure_ascii=False, indent=2))


@register_tool(category="网站", name_cn="获取指定网站流量访问数据", risk_level="medium")
def get_site_overview(site_name: str) -> str:
    """
    获取指定网站的访问信息（经过程序的统计加工后的数据）

    Args:
        site_name: 网站域名或绑定的IP端口;

    returns :
        访问信息、网站近七日流量、请求数量 UV\PV等;
    """
    import os, sys, json
    os.chdir('/www/server/panel/');
    sys.path.insert(0, 'class/');
    sys.path.insert(0, '/www/server/panel/');
    import public;
    from projectModel.monitorModel import main as monitor
    
    monitordata = monitor().get_overview(public.to_dict_obj({"site_name": site_name}))
    
    return _xml_response("done", json.dumps(monitordata, ensure_ascii=False, indent=2))

@register_tool(category="网站", name_cn="获取全部网站流量分析数据", risk_level="medium")
def get_site_analysis() -> str:
    """
    获取全部网站的流量分析数据(最近7天);
    """
    import os, sys, json
    os.chdir('/www/server/panel/');
    sys.path.insert(0, 'class/');
    sys.path.insert(0, '/www/server/panel/');
    import public;
    from projectModel.monitorModel import main as monitor
    
    monitordata = monitor().get_overview(public.to_dict_obj({"metric": "traffic", "order": "desc"}))
    
    return _xml_response("done", json.dumps(monitordata, ensure_ascii=False, indent=2))


@register_tool(category="数据库", name_cn="获取Mysql数据库列表", risk_level="medium")
def get_mysql_list() -> str:
    """
    获取面板中所有数据库列表（已对密码脱敏）

    returns :
        [
            {
                "name": "数据库名称",
                "username": "数据库用户名",
                "accept": "允许访问的IP",
                "type": "数据库类型"
            }
        ]
    """
    import json
    dbs = public.M('databases').field('name,username,accept,type').where("type=?", "MySQL").select()
    return _xml_response("done", json.dumps(dbs, ensure_ascii=False, indent=2))


@register_tool(category="系统", name_cn="获取资源占用TOP10进程", risk_level="low")
def get_top_processes() -> str:
    """
    获取系统中 CPU 和 内存 占用率最高的 TOP 10 进程。
    """
    output_parts = []
    
    # 1. CPU Top 10
    success_cpu, output_cpu = _run_shell_cmd(["ps", "-eo", "pid,user,%cpu,%mem,command", "--sort=-%cpu"])
    if success_cpu:
        lines = output_cpu.strip().splitlines()
        header = lines[0] if lines else ""
        top10 = lines[1:11]
        output_parts.append("--- CPU 占用 TOP 10 ---")
        output_parts.append(header)
        output_parts.extend(top10)
    else:
        output_parts.append(f"获取 CPU TOP 10 失败: {output_cpu}")
    
    output_parts.append("")  # 空行分隔
    
    # 2. Memory Top 10
    success_mem, output_mem = _run_shell_cmd(["ps", "-eo", "pid,user,%cpu,%mem,command", "--sort=-%mem"])
    if success_mem:
        lines = output_mem.strip().splitlines()
        header = lines[0] if lines else ""
        top10 = lines[1:11]
        output_parts.append("--- 内存 占用 TOP 10 ---")
        output_parts.append(header)
        output_parts.extend(top10)
    else:
        output_parts.append(f"获取内存 TOP 10 失败: {output_mem}")
    
    return _xml_response("done", "\n".join(output_parts))


@register_tool(category="网络", name_cn="获取服务器IP", risk_level="medium")
def get_server_ip() -> str:
    """
    获取服务器的内网和公网 IP 地址。
    返回信息包含:
    1. 各个网卡的 IP 地址
    2. 外部 IP 地址
    """
    info = []
    
    # Internal IPs with Interface names
    # Try ip -o -4 addr show first (Linux)
    success, output = _run_shell_cmd(['ip', '-o', '-4', 'addr', 'show'])
    if success:
        info.append("--- Network Interfaces (Internal) ---")
        info.append(output)
    else:
        # Fallback to hostname -I
        s, o = _run_shell_cmd(['hostname', '-I'])
        if s:
            info.append(f"Internal IPs: {o}")
        else:
            info.append("Internal IPs: Unable to retrieve (not Linux?)")
    
    # External IP
    external_ip = "Unknown"
    # Try multiple services
    services = ["https://api.bt.cn/Api/getIpAddress"]
    for service in services:
        s, o = _run_shell_cmd(["curl", "-s", "--connect-timeout", "3", service])
        if s and o:
            external_ip = o
            break
    
    info.append(f"\n--- External IP ---")
    info.append(external_ip)
    
    return _xml_response("done", "\n".join(info))


# --- New Tools ---

@register_tool(category="系统", name_cn="获取Docker信息", risk_level="low")
def get_docker_info() -> str:
    """获取 Docker 系统级信息 (docker info)。"""
    success, output = _run_shell_cmd(["docker", "info"])
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Error getting docker info: {output}")


@register_tool(category="系统", name_cn="获取Docker容器", risk_level="medium")
def get_docker_containers(all: bool = True) -> str:
    """
    获取 Docker 容器列表。

    Args:
        all: 是否显示所有容器 (包括未运行的)，默认为 True。
    """
    cmd = ["docker", "ps"]
    if all:
        cmd.append("-a")
    
    success, output = _run_shell_cmd(cmd)
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Error listing containers: {output}")


@register_tool(category="系统", name_cn="获取Docker容器详情", risk_level="medium")
def get_docker_inspect(container_id_or_name: str) -> str:
    """
    获取 Docker 容器详情。

    Args:
        container_id_or_name: Docker 容器 ID 或名称。
    """
    cmd = ["docker", "inspect", container_id_or_name]
    
    success, output = _run_shell_cmd(cmd)
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Error inspecting container {container_id_or_name}: {output}")


@register_tool(category="系统", name_cn="获取Docker容器日志", risk_level="medium")
def get_docker_logs(container_id_or_name: str) -> str:
    """
    获取 Docker 容器日志。

    Args:
        container_id_or_name: Docker 容器 ID 或名称。
    """
    cmd = ["docker", "logs", container_id_or_name]
    
    success, output = _run_shell_cmd(cmd)
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Error getting logs for container {container_id_or_name}: {output}")


@register_tool(category="系统", name_cn="获取防火墙状态", risk_level="medium")
def get_firewall_status() -> str:
    """获取 iptables 防火墙规则。"""
    success, output = _run_shell_cmd(["iptables", "-L", "-n", "-v"])
    if success:
        return _xml_response("done", output)
    return _xml_response("error", f"Error getting firewall status (requires root?): {output}")