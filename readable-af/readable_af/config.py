import dataclasses
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

_openai_api_key_file = Path(__file__).parent.parent / ".openai-key"
_nounproject_api_key_file = Path(__file__).parent.parent / ".nounproject-key"
_nounproject_secret_file = Path(__file__).parent.parent / ".nounproject-secret"
_recaptcha_site_key_file = Path(__file__).parent.parent / ".recaptcha-site-key"
_recaptcha_secret_key_file = Path(__file__).parent.parent / ".recaptcha-secret"

def _get_secret(env_var: str, secret_file: Path) -> str:
    secret = os.getenv(env_var)
    if not secret:
        if secret_file.exists():
            secret = secret_file.read_text().strip()
        else:
            raise ValueError(f"{env_var} not set")
    return secret


@dataclass
class Config:
    n_icons: int = 3

    openai_org_id: str = "org-byzsYSY4AKLquKGVxYWLjnOv"

    @property
    def openai_api_key(self) -> str:
        return _get_secret("OPENAI_API_KEY", _openai_api_key_file)

    @property
    def nounproject_api_key(self) -> str:
        return _get_secret("NOUNPROJECT_API_KEY", _nounproject_api_key_file)

    @property
    def nounproject_secret(self) -> str:
        return _get_secret("NOUNPROJECT_SECRET", _nounproject_secret_file)

    @property
    def recapcha_site_key(self) -> str:
        return _get_secret("RECAPTCHA_SITE_KEY", _recaptcha_site_key_file)

    @property
    def recapcha_secret(self) -> str:
        return _get_secret("RECAPTCHA_SECRET", _recaptcha_secret_key_file)
    
    @property
    def redis_host(self) -> str | None:
        return os.getenv("REDIS_URL")
    
    @property
    def redis_password(self) -> str | None:
        return os.getenv("REDIS_PASSWORD")

    instance: ClassVar["Config| None"] = None

    def __post_init__(self):
        Config.instance = self

    @classmethod
    def get(cls) -> "Config":
        if cls.instance is None:
            cls.instance = Config()
        return cls.instance
