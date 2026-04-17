def _xml_response(status: str, result: str) -> str:
    return f"\n<tool>\n<toolcall_status>{status}</toolcall_status>\n<toolcall_result>\n{result}\n</toolcall_result>\n</tool>\n"
