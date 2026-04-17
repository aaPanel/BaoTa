import re
import requests
import base64
from typing import Optional
from . import register_tool
from .base import _xml_response

# Constants
MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5MB
DEFAULT_TIMEOUT = 30  # seconds
MAX_TIMEOUT = 120  # seconds

WEBFETCH_DESC = """- Fetches content from a specified URL
- Takes a URL and optional format as input
- Fetches the URL content, converts to requested format (markdown by default)
- Returns the content in the specified format
- Use this tool when you need to retrieve and analyze web content

Usage notes:
  - IMPORTANT: if another tool is present that offers better web fetching capabilities, is more targeted to the task, or has fewer restrictions, prefer using that tool instead of this one.
  - The URL must be a fully-formed valid URL
  - HTTP URLs will be automatically upgraded to HTTPS
  - Format options: "markdown" (default), "text", or "html"
  - This tool is read-only and does not modify any files
  - Results may be summarized if the content is very large"""

def simple_html_to_markdown(html: str) -> str:
    """
    A simple HTML to Markdown converter using regex.
    Since external libraries like bs4 or markdownify are not available.
    """
    # Remove script and style tags and their content
    html = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style\b[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    
    # Headers
    for i in range(1, 7):
        html = re.sub(r'<h' + str(i) + r'[^>]*>(.*?)</h' + str(i) + r'>', 
                      lambda m: '\n' + '#' * i + ' ' + m.group(1).strip() + '\n', 
                      html, flags=re.IGNORECASE)

    # Paragraphs
    html = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', html, flags=re.IGNORECASE)
    
    # Line breaks
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    
    # Bold/Strong
    html = re.sub(r'<(b|strong)[^>]*>(.*?)</\1>', r'**\2**', html, flags=re.IGNORECASE)
    
    # Italic/Em
    html = re.sub(r'<(i|em)[^>]*>(.*?)</\1>', r'*\2*', html, flags=re.IGNORECASE)
    
    # Links
    html = re.sub(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.IGNORECASE)
    
    # Images
    html = re.sub(r'<img\b[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>', r'![\2](\1)', html, flags=re.IGNORECASE)
    html = re.sub(r'<img\b[^>]*src="([^"]*)"[^>]*>', r'![](\1)', html, flags=re.IGNORECASE)
    
    # Code blocks (pre/code)
    html = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', html, flags=re.IGNORECASE)
    
    # Lists (ul/ol/li) - Simplified
    html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</?(ul|ol)[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Remove remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Decode HTML entities (basic ones)
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    
    # Collapse multiple newlines
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    return html.strip()

def extract_text_from_html(html: str) -> str:
    """
    Extract text from HTML using regex.
    """
    # Remove script and style tags and their content
    html = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style\b[^>]*>[\s\S]*?</style>', '', html, flags=re.IGNORECASE)
    
    # Replace block tags with newlines to preserve some structure
    html = re.sub(r'</?(p|div|h[1-6]|li|br|tr)[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Remove remaining tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Decode HTML entities
    html = html.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    
    # Collapse whitespace
    html = re.sub(r'\s+', ' ', html).strip()
    
    return html

@register_tool(category="网络", name_cn="网页获取", risk_level="low")
def WebFetch(url: str, format: str = "markdown", timeout: Optional[int] = None, **kwargs) -> str:
    """
    - Fetches content from a specified URL
    - Takes a URL and optional format as input
    - Fetches the URL content, converts to requested format (markdown by default)
    - Returns the content in the specified format
    - Use this tool when you need to retrieve and analyze web content

    Usage notes:
      - IMPORTANT: if another tool is present that offers better web fetching capabilities, is more targeted to the task, or has fewer restrictions, prefer using that tool instead of this one.
      - The URL must be a fully-formed valid URL
      - HTTP URLs will be automatically upgraded to HTTPS
      - Format options: "markdown" (default), "text", or "html"
      - This tool is read-only and does not modify any files
      - Results may be summarized if the content is very large
    
    Args:
        url: The URL to fetch content from.
        format: The format to return the content in (text, markdown, or html). Defaults to markdown.
        timeout: Optional timeout in seconds (max 120).
    """
    # WebFetch.__doc__ = WEBFETCH_DESC
    
    # Validate URL
    if not url.startswith("http://") and not url.startswith("https://"):
        return _xml_response("error", "URL must start with http:// or https://")
    
    # Set timeout
    request_timeout = DEFAULT_TIMEOUT
    if timeout:
        request_timeout = min(timeout, MAX_TIMEOUT)
    
    # Build headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    if format == "markdown":
        headers["Accept"] = "text/markdown;q=1.0, text/x-markdown;q=0.9, text/plain;q=0.8, text/html;q=0.7, */*;q=0.1"
    elif format == "text":
        headers["Accept"] = "text/plain;q=1.0, text/markdown;q=0.9, text/html;q=0.8, */*;q=0.1"
    elif format == "html":
        headers["Accept"] = "text/html;q=1.0, application/xhtml+xml;q=0.9, text/plain;q=0.8, */*;q=0.1"
    else:
        headers["Accept"] = "*/*"

    try:
        response = requests.get(url, headers=headers, timeout=request_timeout, stream=True)
        
        # Retry with different UA if 403 (Cloudflare check)
        # if response.status_code == 403:
        #      headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
        #      response = requests.get(url, headers=headers, timeout=request_timeout, stream=True)
        
        if not response.ok:
            return _xml_response("error", f"Request failed with status code: {response.status_code}")
        
        # Check size limit
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
             return _xml_response("error", "Response too large (exceeds 5MB limit)")
        
        # Read content with size limit
        content = b""
        for chunk in response.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > MAX_RESPONSE_SIZE:
                return _xml_response("error", "Response too large (exceeds 5MB limit)")
        
        content_type = response.headers.get("content-type", "").lower()
        
        # Handle Images
        if content_type.startswith("image/") and "svg" not in content_type:
            base64_content = base64.b64encode(content).decode('utf-8')
            output = {
                "title": f"{url} ({content_type})",
                "output": "Image fetched successfully",
                "metadata": {},
                "attachments": [
                    {
                        "type": "file",
                        "mime": content_type.split(";")[0].strip(),
                        "url": f"data:{content_type.split(';')[0].strip()};base64,{base64_content}"
                    }
                ]
            }
            # For XML serialization of tool result
            import json
            return _xml_response("done", json.dumps(output, ensure_ascii=False))

        # Text decoding
        encoding = response.encoding
        
        # Check for charset in content-type header
        if 'charset=' in content_type:
            try:
                charset = content_type.split('charset=')[-1].split(';')[0].strip()
                if charset:
                    encoding = charset
            except:
                pass
        
        # If encoding is still None or ISO-8859-1 (requests default), try to detect or default to utf-8
        if not encoding or encoding.lower() == 'iso-8859-1':
            # Try to find charset in meta tag
            import re
            meta_charset = re.search(b'<meta.*?charset=["\']*(.+?)["\'>]', content, re.I)
            if meta_charset:
                encoding = meta_charset.group(1).decode('ascii', errors='ignore')
            else:
                encoding = 'utf-8' # Default to utf-8 if detection fails

        try:
            text_content = content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback to utf-8 with replace, or gb18030 for Chinese
            try:
                text_content = content.decode('gb18030')
            except UnicodeDecodeError:
                text_content = content.decode('utf-8', errors='replace')
            
        title = f"{url} ({content_type})"
        result_output = ""

        # Format conversion
        if format == "markdown":
            if "text/html" in content_type:
                result_output = simple_html_to_markdown(text_content)
            else:
                result_output = text_content
        elif format == "text":
            if "text/html" in content_type:
                result_output = extract_text_from_html(text_content)
            else:
                result_output = text_content
        else: # html or raw
            result_output = text_content

        return _xml_response("done", result_output)

    except requests.Timeout:
        return _xml_response("error", "Request timed out")
    except requests.RequestException as e:
        return _xml_response("error", f"Request failed: {str(e)}")
    except Exception as e:
        return _xml_response("error", f"An error occurred: {str(e)}")
