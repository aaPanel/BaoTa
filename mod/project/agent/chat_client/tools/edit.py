from . import register_tool
from .base import _xml_response
import os
import re
import difflib
from typing import Generator

def _levenshtein(a: str, b: str) -> int:
    if not a: return len(b)
    if not b: return len(a)
    
    if len(a) > len(b):
        a, b = b, a
        
    previous_row = range(len(b) + 1)
    for i, c1 in enumerate(a):
        current_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def _simple_replacer(content: str, find: str) -> Generator[str, None, None]:
    if find in content:
        yield find

def _line_trimmed_replacer(content: str, find: str) -> Generator[str, None, None]:
    c_lines = content.split('\n')
    f_lines = find.split('\n')
    
    if f_lines and f_lines[-1] == "":
        f_lines.pop()
        
    if len(f_lines) > len(c_lines):
        return

    offsets = [0]
    curr = 0
    for line in c_lines:
        curr += len(line) + 1 
        offsets.append(curr)

    for i in range(len(c_lines) - len(f_lines) + 1):
        match = True
        for j in range(len(f_lines)):
            if c_lines[i+j].strip() != f_lines[j].strip():
                match = False
                break
        
        if match:
            start_idx = offsets[i]
            end_line_idx = i + len(f_lines) - 1
            end_idx = offsets[end_line_idx] + len(c_lines[end_line_idx])
            yield content[start_idx:end_idx]

def _block_anchor_replacer(content: str, find: str) -> Generator[str, None, None]:
    c_lines = content.split('\n')
    f_lines = find.split('\n')
    
    if len(f_lines) < 3: return
    if f_lines[-1] == "": f_lines.pop()
    
    first = f_lines[0].strip()
    last = f_lines[-1].strip()
    search_block_size = len(f_lines)
    
    candidates = []
    for i in range(len(c_lines)):
        if c_lines[i].strip() != first: continue
        
        for j in range(i + 2, len(c_lines)):
            if c_lines[j].strip() == last:
                candidates.append((i, j))
                break 
    
    if not candidates: return
    
    SINGLE_THRESHOLD = 0.0
    
    offsets = [0]
    curr = 0
    for line in c_lines:
        curr += len(line) + 1
        offsets.append(curr)

    def get_text(start_line, end_line):
        start_idx = offsets[start_line]
        end_idx = offsets[end_line] + len(c_lines[end_line])
        return content[start_idx:end_idx]

    if len(candidates) == 1:
        start, end = candidates[0]
        actual_size = end - start + 1
        
        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_size - 2)
        
        if lines_to_check > 0:
            for j in range(1, min(search_block_size - 1, actual_size - 1)):
                c_line = c_lines[start + j].strip()
                f_line = f_lines[j].strip()
                max_len = max(len(c_line), len(f_line))
                if max_len == 0: continue
                dist = _levenshtein(c_line, f_line)
                similarity += (1.0 - dist / max_len) / lines_to_check
                if similarity >= SINGLE_THRESHOLD: break
        else:
            similarity = 1.0
            
        if similarity >= SINGLE_THRESHOLD:
             yield get_text(start, end)
        return

    best_match = None
    max_sim = -1.0
    
    for cand in candidates:
        start, end = cand
        actual_size = end - start + 1
        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_size - 2)
        
        if lines_to_check > 0:
             for j in range(1, min(search_block_size - 1, actual_size - 1)):
                c_line = c_lines[start + j].strip()
                f_line = f_lines[j].strip()
                max_len = max(len(c_line), len(f_line))
                if max_len == 0: continue
                dist = _levenshtein(c_line, f_line)
                similarity += (1.0 - dist / max_len)
             similarity /= lines_to_check
        else:
            similarity = 1.0
            
        if similarity > max_sim:
            max_sim = similarity
            best_match = cand

    MULTIPLE_THRESHOLD = 0.3
    if max_sim >= MULTIPLE_THRESHOLD and best_match:
        yield get_text(best_match[0], best_match[1])

def _whitespace_normalized_replacer(content: str, find: str) -> Generator[str, None, None]:
    def normalize(s): return re.sub(r'\s+', ' ', s).strip()
    
    norm_find = normalize(find)
    c_lines = content.split('\n')
    
    for i, line in enumerate(c_lines):
        if normalize(line) == norm_find:
            yield line
        else:
            norm_line = normalize(line)
            if norm_find in norm_line:
                words = find.strip().split()
                if words:
                    pattern = r'\s+'.join(re.escape(w) for w in words)
                    try:
                        match = re.search(pattern, line)
                        if match:
                            yield match.group(0)
                    except:
                        pass
    
    f_lines = find.split('\n')
    if len(f_lines) > 1:
        for i in range(len(c_lines) - len(f_lines) + 1):
            block = c_lines[i : i+len(f_lines)]
            block_str = '\n'.join(block) 
            if normalize(block_str) == norm_find:
                yield '\n'.join(block) 

def _indentation_flexible_replacer(content: str, find: str) -> Generator[str, None, None]:
    def remove_indent(text):
        lines = text.split('\n')
        non_empty = [l for l in lines if l.strip()]
        if not non_empty: return text
        
        min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
        return '\n'.join(l[min_indent:] if l.strip() else l for l in lines)
    
    norm_find = remove_indent(find)
    c_lines = content.split('\n')
    f_lines = find.split('\n')
    
    if len(f_lines) > len(c_lines): return
    
    for i in range(len(c_lines) - len(f_lines) + 1):
        block = '\n'.join(c_lines[i : i+len(f_lines)])
        if remove_indent(block) == norm_find:
            yield block

def _escape_normalized_replacer(content: str, find: str) -> Generator[str, None, None]:
    def unescape(s):
        ret = ""
        i = 0
        while i < len(s):
            if s[i] == '\\' and i + 1 < len(s):
                c = s[i+1]
                if c == 'n': ret += '\n'
                elif c == 't': ret += '\t'
                elif c == 'r': ret += '\r'
                elif c in ["'", '"', '`', '\\', '$']: ret += c
                else: ret += '\\' + c
                i += 2
            else:
                ret += s[i]
                i += 1
        return ret

    unescaped_find = unescape(find)
    
    if unescaped_find in content:
        yield unescaped_find
        
    c_lines = content.split('\n')
    f_lines = unescaped_find.split('\n')
    
    if len(f_lines) > len(c_lines): return
    
    for i in range(len(c_lines) - len(f_lines) + 1):
        block = '\n'.join(c_lines[i : i+len(f_lines)])
        if unescape(block) == unescaped_find:
            yield block

def _trimmed_boundary_replacer(content: str, find: str) -> Generator[str, None, None]:
    trimmed_find = find.strip()
    if trimmed_find == find: return
    
    if trimmed_find in content:
        yield trimmed_find
        
    c_lines = content.split('\n')
    f_lines = find.split('\n')
    
    if len(f_lines) > len(c_lines): return
    
    for i in range(len(c_lines) - len(f_lines) + 1):
        block = '\n'.join(c_lines[i : i+len(f_lines)])
        if block.strip() == trimmed_find:
            yield block

def _context_aware_replacer(content: str, find: str) -> Generator[str, None, None]:
    f_lines = find.split('\n')
    if len(f_lines) < 3: return
    if f_lines[-1] == "": f_lines.pop()
    
    first = f_lines[0].strip()
    last = f_lines[-1].strip()
    
    c_lines = content.split('\n')
    
    offsets = [0]
    curr = 0
    for line in c_lines:
        curr += len(line) + 1
        offsets.append(curr)
        
    def get_text(start_line, end_line):
        start_idx = offsets[start_line]
        end_idx = offsets[end_line] + len(c_lines[end_line])
        return content[start_idx:end_idx]
    
    for i in range(len(c_lines)):
        if c_lines[i].strip() != first: continue
        
        for j in range(i + 2, len(c_lines)):
            if c_lines[j].strip() == last:
                block_lines = c_lines[i : j+1]
                
                if len(block_lines) == len(f_lines):
                    matching = 0
                    total_non_empty = 0
                    
                    for k in range(1, len(block_lines) - 1):
                        c_l = block_lines[k].strip()
                        f_l = f_lines[k].strip()
                        if c_l or f_l:
                            total_non_empty += 1
                            if c_l == f_l:
                                matching += 1
                    
                    if total_non_empty == 0 or (matching / total_non_empty >= 0.5):
                        yield get_text(i, j)
                        return

def _multi_occurrence_replacer(content: str, find: str) -> Generator[str, None, None]:
    start = 0
    while True:
        idx = content.find(find, start)
        if idx == -1: break
        yield find
        start = idx + len(find)

def _perform_replace(content: str, old_str: str, new_str: str, replace_all: bool = False) -> str:
    if old_str == new_str:
         raise ValueError("No changes to apply: old_str and new_str are identical.")
    
    replacers = [
        _simple_replacer,
        _line_trimmed_replacer,
        _block_anchor_replacer,
        _whitespace_normalized_replacer,
        _indentation_flexible_replacer,
        _escape_normalized_replacer,
        _trimmed_boundary_replacer,
        _context_aware_replacer,
        _multi_occurrence_replacer
    ]
    
    not_found = True
    
    for replacer in replacers:
        for search in replacer(content, old_str):
            index = content.find(search)
            if index == -1: continue
            
            not_found = False
            
            if replace_all:
                return content.replace(search, new_str)
            
            last_index = content.rfind(search)
            if index != last_index:
                continue 
                
            return content[:index] + new_str + content[index + len(search):]
            
    if not_found:
        raise ValueError("Could not find old_str in the file. It must match exactly, including whitespace, indentation, and line endings.")
    
    raise ValueError("Found multiple matches for old_str. Provide more surrounding context to make the match unique.")

def _trim_diff(diff: str) -> str:
    lines = diff.split('\n')
    content_lines = [l for l in lines if (l.startswith('+') or l.startswith('-') or l.startswith(' ')) and not l.startswith('---') and not l.startswith('+++')]
    
    if not content_lines: return diff
    
    min_indent = float('inf')
    for line in content_lines:
        content = line[1:]
        if content.strip():
            match = re.match(r'^(\s*)', content)
            if match:
                min_indent = min(min_indent, len(match.group(1)))
                
    if min_indent == float('inf') or min_indent == 0:
        return diff
        
    trimmed_lines = []
    for line in lines:
        if (line.startswith('+') or line.startswith('-') or line.startswith(' ')) and not line.startswith('---') and not line.startswith('+++'):
            prefix = line[0]
            content = line[1:]
            trimmed_lines.append(prefix + content[min_indent:])
        else:
            trimmed_lines.append(line)
            
    return '\n'.join(trimmed_lines)

@register_tool(category="Agent", name_cn="搜索替换", risk_level="high")
class SearchReplace:
    """
    Performs exact string replacements in files. 
    
    Usage:
    - You must use your `Read` tool at least once in the conversation before editing. This tool will error if you attempt an edit without reading the file. 
    - When editing text from Read tool output, ensure you preserve the exact indentation (tabs/spaces) as it appears AFTER the line number prefix. The line number prefix format is: line number + colon + space (e.g., `1: `). Everything after that space is the actual file content to match. Never include any part of the line number prefix in the oldString or newString.
    - ALWAYS prefer editing existing files in the codebase. NEVER write new files unless explicitly required.
    - Only use emojis if the user explicitly requests it. Avoid adding emojis to files unless asked.
    - The edit will FAIL if `oldString` is not found in the file with an error "oldString not found in content".
    - The edit will FAIL if `oldString` is found multiple times in the file with an error "Found multiple matches for oldString. Provide more surrounding lines in oldString to identify the correct match." Either provide a larger string with more surrounding context to make it unique or use `replaceAll` to change every instance of `oldString`. 
    - Use `replaceAll` for replacing and renaming strings across the file. This parameter is useful if you want to rename a variable for instance.
    
    Args:
        file_path: The absolute path to the file to modify
        old_str: The text to replace
        new_str: The text to replace it with (must be different from oldString)
        replace_all: Replace all occurrences of oldString (default false)
    """
    def execute(self, file_path: str, old_str: str, new_str: str, replace_all: bool = False) -> str:
        try:
            if not os.path.exists(file_path):
                return _xml_response("error", f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            new_content = _perform_replace(content, old_str, new_str, replace_all)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            # Generate diff for display
            diff_gen = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=file_path,
                tofile=file_path,
                n=3 # Context lines
            )
            diff = "".join(diff_gen)
            
            # Trim diff using the ported function
            trimmed_diff = _trim_diff(diff)
            
            return _xml_response("done", f"Edit applied successfully.\n<file_changes>\nThe toolcall made the following changes to the file `{file_path}`:\n```\n{trimmed_diff}\n```\n</file_changes>")
        except Exception as e:
            return _xml_response("error", str(e))
