from dataclasses import dataclass
import dataclasses
import os
from pathlib import Path


_openai_api_key_file = Path(__file__).parent.parent / ".openai-key"
_nounproject_api_key_file = Path(__file__).parent.parent / ".nounproject-key"
_nounproject_secret_file = Path(__file__).parent.parent / ".nounproject-secret"


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
    out_dir: Path
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

    def __post_init__(self):
        """Set default class variables to be equal to instance variables."""
        for k, v in dataclasses.asdict(self).items():
            setattr(Config, k, v)
