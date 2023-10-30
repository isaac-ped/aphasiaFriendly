import dataclasses
from dataclasses import dataclass
from typing import Literal


@dataclass
class Message:
    content: str
    role: Literal["user", "assistant", "system"] = "user"

    def __post_init__(self):
        self.content = self.content.strip()
        self.content = self.content.replace("\n", " ")


def asdict(messages: list[Message]) -> list[dict]:
    return [dataclasses.asdict(message) for message in messages]


ABSTRACT_EXTRACTION = [
    Message(
        "You are an assistant that handles the extraction of text from scientific articles. "
        "You will be provided with text that has been extracte from a scientific PDF and asked for a specific section "
        "of that text. The text may be extracted cleanly, in which case you may just be able to return the text "
        "in the same format that it was given to you. "
        "However, you may be given the text alongside some other information or metadata that was added in a "
        "messy extraction process. In that case, try to return only the part of the text that represents the section "
        "that was requested. "
        "You should never respond with an answer other the specified text to be extracted",
        role="system",
    ),
    Message("Extract the abstract from the text in the following message"),
]


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

ICON_MESSAGES = [
    Message(
        "For each bullet point you generated above, give one to two keywords that would allow you to search "
        "for an appropriate icon that would demonstrate the concepts represented in the bullet point"
    )
]
