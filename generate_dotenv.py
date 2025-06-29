#!/usr/bin/env python3
"""
Inspect the config for the application,
retrieve the secrets as they are defined in fly.io,
and create a file defining them locally
"""

from pathlib import Path
import subprocess
from dataclasses import fields
from readable_af.config import Config, EnvVar, SecretFile


def copy_dev_env_vars(output: Path):
    """Fetch environment variables from fly.io."""
    # Get all of the env variables from fly.io
    try:
        result = subprocess.run(
            ["fly", "ssh", "console", "--app", "article-friend-dev", "-C", "env"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print("The dev site for article friend may not be running at the moment.")
        print(
            "Try visiting https://article-friend-dev.fly.dev and then re-running this script."
        )
        return

    secret_vars: list[str] = []
    for field in fields(Config):
        factory = field.default_factory
        if factory and (var := getattr(factory, "__self__", None)):
            if isinstance(var, (EnvVar, SecretFile)) and var.required:
                secret_vars.append(var.env)
            elif isinstance(var, SecretFile) and var.required:
                secret_vars.append(var.env)

    print(f"Fetching the following variables from fly.io: {', '.join(secret_vars)}")

    env_lines = []
    for line in result.stdout.splitlines():
        if any(line.startswith(f"{var}=") for var in secret_vars):
            env_lines.append(line.strip())

    with output.open("w") as f:
        for line in env_lines:
            f.write(f"{line}\n")
    print("Rendered secrets to ", output)


if __name__ == "__main__":
    output_path = Path(__file__).parent / ".env"
    copy_dev_env_vars(output_path)
