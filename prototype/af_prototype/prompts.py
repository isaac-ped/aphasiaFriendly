from dataclasses import dataclass
from typing import Literal


@dataclass
class Message:
    content: str
    role: Literal["user", "assistant", "system"] = "user"

    def __post_init__(self):
        self.content = self.content.strip()
        self.content = self.content.replace("\n", " ")


SUMMARY_MESSAGES = [
    Message(
        """
        You are an assistant that processes scientific articles into a few simple sentences
        that are understandable by someone with a first grade reading level
        """,
        role="system",
    ),
    Message(
        "Summaryize the abstract from the following article, producing 5 bullet points"
    ),
]
