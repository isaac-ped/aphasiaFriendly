import functools
import os
from pathlib import Path

ORGANIZATION_ID = "org-byzsYSY4AKLquKGVxYWLjnOv"

_openai_api_key_file = Path(__file__).parent.parent / ".openai-key"
_nounproject_api_key_file = Path(__file__).parent.parent / ".nounproject-key"
_nounproject_secret_file = Path(__file__).parent.parent / ".nounproject-secret"


@functools.cache
def _get_secret(env_var: str, secret_file: Path) -> str:
    secret = os.getenv(env_var)
    if not secret:
        if secret_file.exists():
            secret = secret_file.read_text().strip()
        else:
            raise ValueError(f"{env_var} not set")
    return secret


def openai_api_key() -> str:
    return _get_secret("OPENAI_API_KEY", _openai_api_key_file)


def nounproject_api_key() -> str:
    return _get_secret("NOUNPROJECT_API_KEY", _nounproject_api_key_file)


def nounproject_secret() -> str:
    return _get_secret("NOUNPROJECT_SECRET", _nounproject_secret_file)
