import dataclasses
from functools import cache, cached_property
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

_HERE = Path(__file__).parent
_DEFAULT_ENV_FILE = Path(".env")


def _read_dotenv(env_var: str, file_path: Path = _DEFAULT_ENV_FILE) -> str:
    """Read a specific environment variable from a .env file"""
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")

    with file_path.open("r") as f:
        for line in f:
            if line.startswith(env_var):
                return line.split("=", 1)[1].strip().strip('"')
    raise ValueError(f"{env_var} not found in {file_path}")


@dataclass(frozen=True)
class EnvVar:
    """Container to hold a single config variable defined in the environment or a .env file."""

    env: str
    required: ClassVar[bool] = False

    @cache
    def get(self) -> str | None:
        """Retrieve the value of the env var.
        :returns: Value, or None if not set
        """
        env_value = os.getenv(self.env)
        if env_value is not None:
            return env_value
        try:
            return _read_dotenv(self.env)
        except (FileNotFoundError, ValueError) as e:
            if self.required:
                raise e
            return None


@dataclass(frozen=True)
class RequiredEnvVar(EnvVar):
    """Overload of EnvVar that is required for the application to run."""

    required: ClassVar[bool] = True

    @cache
    def get(self) -> str:
        """Return the value of the env var, raising an exception if not set"""
        value = super().get()
        # This next line should never raise because 'required' is True above
        assert value is not None, f"Required secret {self.env} is not set."
        return value


@dataclass
class SecretFile:
    """Holds a reference to config variable that must be written to a file."""

    env: str  # An environment variable that may hold the file contents
    file_path: Path  # The path to the file that will be created

    # Required by default, until we have a need for an optional secret file
    required: ClassVar[bool] = True

    def get(self) -> Path:
        """Get the path to a file containing the secret contents."""
        if self.file_path.exists():
            return self.file_path
        contents = self.contents
        with self.file_path.open("w") as f:
            f.write(contents)
        return self.file_path

    @cached_property
    def contents(self) -> str:
        """Get the contents of the secret from env or file path."""
        if self.file_path.exists():
            return self.file_path.read_text().strip()
        return RequiredEnvVar(self.env).get()


@dataclass
class Config:
    """Define all configuration variables for the application here.

    Class should be instatiated with `Config.get()` to avoid repeatedly reading from the environment.
    """

    n_icons: int = 3

    openai_org_id: str = "org-byzsYSY4AKLquKGVxYWLjnOv"

    google_client_secrets_file: Path = dataclasses.field(
        default_factory=SecretFile(
            "CREDENTIALS_JSON",
            _HERE.parent.parent / "credentials.json",
        ).get
    )
    openai_api_key: str = dataclasses.field(
        default_factory=RequiredEnvVar("OPENAI_API_KEY").get
    )
    nounproject_api_key: str = dataclasses.field(
        default_factory=RequiredEnvVar("NOUNPROJECT_API_KEY").get
    )
    nounproject_secret: str = dataclasses.field(
        default_factory=RequiredEnvVar("NOUNPROJECT_SECRET").get
    )
    recapcha_site_key: str = dataclasses.field(
        default_factory=RequiredEnvVar("RECAPTCHA_SITE_KEY").get
    )
    recapcha_secret: str = dataclasses.field(
        default_factory=RequiredEnvVar("RECAPTCHA_SECRET").get
    )
    redis_host: str | None = dataclasses.field(
        default_factory=EnvVar("REDIS_URL").get,
    )
    redis_password: str | None = dataclasses.field(
        default_factory=EnvVar("REDIS_PASSWORD").get
    )

    _instance: ClassVar["Config| None"] = None

    def __post_init__(self):
        Config._instance = self

    @classmethod
    def get(cls) -> "Config":
        """Retrieve the singleton instance of Config."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance
