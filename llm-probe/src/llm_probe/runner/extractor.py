"""Extract Python code blocks from LLM markdown responses."""

import re

# Matches ```python, ``` python, ``` (no tag), case-insensitive
_FENCED_PYTHON = re.compile(
    r"```[ \t]*(?:python)?[ \t]*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def extract_code(text: str) -> str:
    """Extract the first Python code block from markdown text.

    Returns empty string if no code block found — never raises.
    """
    if not text:
        return ""
    matches = _FENCED_PYTHON.findall(text)
    if not matches:
        # Fallback: try the whole text if it looks like raw code
        stripped = text.strip()
        if stripped.startswith(("def ", "class ", "import ", "#")):
            return stripped
        return ""
    # Prefer the longest block (most complete implementation)
    return max(matches, key=len).strip()
