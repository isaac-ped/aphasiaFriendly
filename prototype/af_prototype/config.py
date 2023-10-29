import functools
import os
from pathlib import Path

ORGANIZATION_ID = "org-byzsYSY4AKLquKGVxYWLjnOv"

_api_key_file = Path(__file__).parent.parent / ".openai-key"


@functools.cache
def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if _api_key_file.exists():
            api_key = _api_key_file.read_text().strip()
        else:
            raise ValueError("OPENAI_API_KEY not set")
    return api_key
