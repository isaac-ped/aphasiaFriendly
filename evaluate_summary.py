"""Standalone evaluator for aphasia-friendly article summaries.

Given a generated bullet summary (a plain text file) and the source article
(a PDF), this rates how well the summary captures the article on four criteria
-- accuracy, coverage, simplicity, and clarity -- and prints a rating report.

This is intentionally self-contained: the only project dependency is the
OpenAI API key (read from readable_af's Config, or falling back to the
OPENAI_API_KEY environment variable / .env file). It evaluates *bullets only*;
it does not look at or score icons.

Usage:
    uv run python evaluate_summary.py SUMMARY.txt ARTICLE.pdf
    uv run python evaluate_summary.py SUMMARY.txt ARTICLE.pdf --json
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader

MODEL = "gpt-5-mini-2025-08-07"

# Truncate very long articles so we stay well within the context window. The
# full body is far more than is needed to judge accuracy/coverage of a handful
# of bullets, but we keep generously more than the abstract-only path does.
MAX_ARTICLE_CHARS = 60_000


# --------------------------------------------------------------------------- #
# Output schema
# --------------------------------------------------------------------------- #
class CriterionScore(BaseModel):
    score: int = Field(ge=1, le=10)
    justification: str = Field(
        description="One or two sentences explaining the score, citing specifics."
    )


class SummaryRating(BaseModel):
    accuracy: CriterionScore = Field(
        description="Does the summary introduce hallucinations or contradict the "
        "article? Does anything misrepresent or over-simplify the findings?"
    )
    coverage: CriterionScore = Field(
        description="Are the article's main arguments included? Are critical "
        "details missing?"
    )
    simplicity: CriterionScore = Field(
        description="Is the word choice simple enough for a reader with aphasia?"
    )
    clarity: CriterionScore = Field(
        description="Would each sentence be clear to a reader of any level who is "
        "not informed on the topic?"
    )
    overall: int = Field(
        ge=1, le=10, description="Overall holistic quality of the summary, 1-10."
    )
    summary_comment: str = Field(
        description="A short overall comment: the biggest strengths and the most "
        "important problems to fix."
    )


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #
def extract_pdf_text(pdf_file: Path, max_chars: int = MAX_ARTICLE_CHARS) -> str:
    """Extract the text of every page of the article PDF."""
    reader = PdfReader(pdf_file)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError(
            f"No extractable text found in {pdf_file}. Is it a scanned/image PDF?"
        )
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... article truncated for length ...]"
    return text


def load_bullets(summary_file: Path) -> list[str]:
    """Read a summary text file and return its bullets, one per line.

    Tolerates leading bullet markers (-, *, •) and strips <b></b> emphasis tags
    so the rater sees clean prose. Each non-empty line is treated as a bullet.
    """
    raw = summary_file.read_text(encoding="utf-8")
    bullets: list[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s*", "", line)  # drop leading bullet marker
        line = re.sub(r"</?b>", "", line)  # drop bold emphasis tags
        line = line.strip()
        if line:
            bullets.append(line)
    if not bullets:
        raise ValueError(f"No summary bullets found in {summary_file}")
    return bullets


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def _api_key() -> str:
    """Resolve the OpenAI API key from the project Config, env, or .env file."""
    try:
        from readable_af.config import Config

        return Config.get().openai_api_key
    except Exception:
        pass
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    env = Path(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(
        "Could not find OPENAI_API_KEY (checked Config, environment, and .env)."
    )


def evaluate(article_text: str, bullets: list[str]) -> SummaryRating:
    client = OpenAI(api_key=_api_key())
    bullets_text = "\n".join(f"- {b}" for b in bullets)

    system = (
        "You are an expert editor that evaluates aphasia-friendly summaries of "
        "scientific articles generated by another LLM. You will be given the "
        "source article and the generated bullet summary. Score the summary on "
        "four criteria, each from 1 (terrible) to 10 (excellent), and give a "
        "short justification for each. Be strict: rating a poor summary too "
        "highly harms readers with aphasia, while rating it too low is far less "
        "harmful.\n\n"
        "Accuracy: Does the summary hallucinate or contradict the article? Does "
        "anything misrepresent or over-simplify the findings?\n"
        "Coverage: Are the main arguments included? Are critical details missing?\n"
        "Simplicity: Is the word choice simple enough for a reader with aphasia?\n"
        "Clarity: Would each sentence be clear to a reader of any level who is not "
        "informed on the topic? Any sentence that might not make sense to an "
        "uninformed reader should greatly reduce this score.\n\n"
        "Then give an overall 1-10 score and a short overall comment."
    )
    user = f"ARTICLE:\n{article_text}\n\nSUMMARY BULLETS:\n{bullets_text}"

    response = client.responses.parse(
        model=MODEL,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        text_format=SummaryRating,
    )
    if response.output_parsed is None:
        raise RuntimeError(f"Model did not return a parseable rating: {response.error}")
    return response.output_parsed


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #
def format_report(rating: SummaryRating, n_bullets: int) -> str:
    lines = [
        "=" * 60,
        "  AphasiaFriendly Summary Evaluation",
        "=" * 60,
        f"Bullets evaluated: {n_bullets}",
        "",
    ]
    for name in ("accuracy", "coverage", "simplicity", "clarity"):
        c: CriterionScore = getattr(rating, name)
        lines.append(f"{name.capitalize():<12} {c.score:>2}/10")
        lines.append(f"             {c.justification}")
        lines.append("")
    lines.append(f"{'OVERALL':<12} {rating.overall:>2}/10")
    lines.append("")
    lines.append("Comment:")
    lines.append(f"  {rating.summary_comment}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rate an aphasia-friendly bullet summary against its source article."
    )
    parser.add_argument("summary", type=Path, help="Path to the summary .txt file")
    parser.add_argument("article", type=Path, help="Path to the article .pdf file")
    parser.add_argument(
        "--json", action="store_true", help="Print the rating as JSON instead of a report"
    )
    args = parser.parse_args(argv)

    if not args.summary.exists():
        parser.error(f"Summary file not found: {args.summary}")
    if not args.article.exists():
        parser.error(f"Article PDF not found: {args.article}")

    bullets = load_bullets(args.summary)
    article_text = extract_pdf_text(args.article)
    rating = evaluate(article_text, bullets)

    if args.json:
        print(rating.model_dump_json(indent=2))
    else:
        print(format_report(rating, len(bullets)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
