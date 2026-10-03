import re
import uuid
from typing import Optional


def is_valid_uuid(val: str) -> bool:
    """Validate if a string is a valid UUIDv4."""
    try:
        uuid_obj = uuid.UUID(str(val), version=4)
        return str(uuid_obj) == str(val).lower()
    except (ValueError, AttributeError):
        return False


def sanitize_prompt(prompt: Optional[str]) -> str:
    """Sanitize user input string and prevent injection/null bytes."""
    if not prompt:
        return ""
    # Strip null bytes and control chars
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', prompt)
    return clean.strip()
