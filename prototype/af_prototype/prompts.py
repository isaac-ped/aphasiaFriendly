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

TITLE_AND_AUTHOR_ABSTRACTION = [
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
    Message("Extract the title, authors, and publication date of the article from the text in the following message. "
            "The tile should be on the first line of the response, all authors on the second line, and the date on the third line. "
            "If multiple dates are available, you should choose the latest date and output only that. "
            "If there are multiple authors, only output the first author and then 'et al.'"),
]


SUMMARY_MESSAGES = [
    Message(
        "You are an assistant that processes scientific articles into a few simple sentences "
        "that are understandable by someone that has difficulty reading. "
        "You will be passed the abstract of a scientific article and asked to summarize it. "
        "Your summary should always produce 5 bullet points, each of which use very simple syntax "
        "and vocabulary. "
        "In particular, the words that you use should be as simple and common as possible, "
        "and the sentences that you produce should have a flesch-kincaid score of less than 65.",
        role="system",
    ),
    Message(
        "Summarize the abstract from the following article"
    ),
]

ICON_MESSAGES = [
    Message(
        "For each bullet point you generated above, give one, two, or three keywords that would allow you to search "
        "for an appropriate icon that would demonstrate the concepts represented in the bullet point. "
        "The icons will be pictographic and simple. For instance, if the bullet point has "
        "to do with a staticstic getting bigger, you might return 'upward arrow'. If the bulllet point "
        "has to do with neurons, you might return 'brain' or 'thinking'. If it has to do with emotions, "
        "you might return 'happy' or 'sad'.  "
        "Each keyword should be a very common word, not a specialized word in any way. For example, instead of "
        "'neuron' you might say 'cell' or 'brain'. Keywords should not be repeated across bullet points. "
        "Your output should *only* contain these keywords - do *not* repeat the input prompt in any way, "
        "with the keywords for each bullet point on their own line. "
        "Keywords within a bullet point should be separated by a comma. "
        "You should always provide as many lines as there were inputs. If you cannot provide an appropriate "
        "keyword for a bullet point, you should return an empty line."
    )
]
