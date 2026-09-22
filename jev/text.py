# Portions adapted from jbt95/jev-toolkit at f8792f9 (src/core/text.ts), MIT.
# Attribution and modification notice: ../NOTICE; license: ../licenses/MIT-jev-toolkit.txt.
"""Outbound state hygiene: mask credentials, drop fenced code, clip long text."""
import re

MAX_TEXT = 2000

_ASSIGNMENT = re.compile(
    r"""(\b["']?(?:authorization|x-api-key|api[_-]?key|apikey|access[_-]?token|private[_-]?key|secret[_-]?key"""
    r"""|[\w-]*(?:token|secret|password)|[\w-]+[_-]key)["']?\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\r\n"}]+)""",
    re.IGNORECASE)
_BEARER = re.compile(r"\b(Bearer\s+)[A-Za-z0-9._~+/=-]{6,}", re.IGNORECASE)
_FENCE_OPEN = re.compile(r"^\s*(?:`{3,}|~{3,})")
_FENCE_CLOSE = re.compile(r"^\s*(?:`{3,}|~{3,})\s*$")


def redact(text):
    """Mask credential assignments and standalone Bearer tokens."""
    return _BEARER.sub(r"\1[redacted]", _ASSIGNMENT.sub(r"\1[redacted]", text))


def strip_fenced_code(text):
    """Replace each fenced code block with `[code]`; inline code and prose stay."""
    kept, in_fence = [], False
    for line in text.split("\n"):
        if not in_fence and _FENCE_OPEN.match(line):
            in_fence = True
            kept.append("[code]")
        elif in_fence:
            in_fence = not _FENCE_CLOSE.match(line)
        else:
            kept.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def clip(text, limit=MAX_TEXT):
    return text if len(text) <= limit else text[:limit] + " … [clipped]"


def sanitize(value, limit=MAX_TEXT):
    """Apply all three to every string in a JSON value; keys and non-strings pass through."""
    if isinstance(value, str):
        return clip(strip_fenced_code(redact(value)), limit)
    if isinstance(value, list):
        return [sanitize(item, limit) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item, limit) for key, item in value.items()}
    return value
