# Use a pipeline as a high-level helper
from argparse import ArgumentParser
from pathlib import Path
from transformers import pipeline
import json

def generate(prompt: str, output_file: Path, n_tokens: int):
    print("Loading pipeline")
    generator = pipeline("text-generation", model="openchat/openchat")
    print(f"Generating {n_tokens} tokens")
    result = generator(prompt, max_new_tokens=n_tokens)
    print(result)
    with output_file.open("w") as f:
        json.dump(result, f)


def main():
    parser = ArgumentParser()
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--n-tokens", type=int, default=500)
    parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()

    prompt = args.prompt_file.read_text()
    generate(prompt, args.output, args.n_tokens)
