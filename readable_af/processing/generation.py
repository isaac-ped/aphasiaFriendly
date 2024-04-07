import json
from ..external import openai as oa
from readable_af.model.summary import Bullet, Metadata, Summary, Icon
from ..logger import logger

MODEL = "gpt-4-1106-preview"


def metadata_prompt(preamble: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that handles the extraction of text from scientific articles. "
            "You will be provided with text that has been extracte from a scientific PDF and asked for a specific section "
            "of that text. The text may be extracted cleanly, in which case you may just be able to return the text "
            "in the same format that it was given to you.\n"
            "Whenever a message is sent to you, it will contain messily extracted metadata from a scientific article. "
            "This metadata will should include the title, authors, and publication date of the article, but may also contain "
            "other extraneous information, newlines, or other formatting.\n"
            "You should extract the title, authors, and publication date from the metadata and return them in the following format:"
            "The tile should be on the first line of the response, all authors on the second line, and the date on the third line. "
            "If multiple dates are available, you should choose the latest date and output only that. "
            "If there are multiple authors, return up to three authors separated by commas and then 'et al.'\n\n"
            "You MUST always return EXACTLY three lines of text.",
            role="system",
        ),
        oa.Message(preamble),
    ]


def generate_metadata(preamble: str) -> Metadata:
    messages = metadata_prompt(preamble)
    response = oa.completion(messages, model=MODEL)
    title, authors, date = response.split("\n")
    logger.info(f"Generated the following metadata: {title=}, {authors=}, {date=}")
    return Metadata(
        title.strip(), [a.strip() for a in authors.split(",")], date.strip()
    )


def abstract_prompt(messy_abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that handles the extraction of an abstract from scientific articles.\n"
            "You will be provided with text that has been extracted from a scientific PDF and you should find and "
            "return the abstract from that text. It is possible that the text will be extracted cleanly, in which case "
            "you should just return the text in the same format that it was given to you.\n"
            "However, you may be given the text alongside some other information or metadata that was added in a "
            "messy extraction process. In that case, try to return only the part of the text that represents the abstract.\n\n"
            "You should never respond with an answer other the specified text to be extracted",
            role="system",
        ),
        oa.Message(messy_abstract),
    ]


def generate_abstract(messy_abstract: str) -> str:
    messages = abstract_prompt(messy_abstract)
    abstract = oa.completion(messages, model=MODEL)
    logger.info(f"Generated the following asbtract: {abstract}")
    return abstract.strip()


def summary_prompt(abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that processes scientific articles into a few simple sentences "
            "that are understandable by someone that has difficulty reading. "
            "You will be passed the abstract of a scientific article and asked to summarize it. "
            "Your summary should always produce 5-7 sentences of summary. "  # , with each sentence "
            # "separated from other sentences by the | character."
            "Each sentence should be shorter than 150 characters, and should use very simple syntax and vocabulary. "
            "The words that you use should be as simple and common as possible, "
            "while still reflecting the specific content of the abstract. "
            "If you introduce complicated, uncommonly used terms, please explicitly define them in simpler terms. "
            "Use only those simpler terms moving forward. "
            "Be specific about brain locations, "
            "for example, do not say 'brain spots', but say 'temporal lobe' or 'frontal lobe'."
            "The sentences that you produce should have a flesch-kincaid score of less than 75. "
            "Avoid medical or scientific jargon as much as possible."
            "The sentences should be grammatical - that is, do not say sentences like 'Found astrocytomas near eloquent regions."
            "Be conservative in your statement of facts. "
            "For example, do not say 'The brain does not', but say 'The brain may not.' "
            "The last bullet point should summarize the abstract in one sentence. "
            "The two or three most important words or short phrases in each bullet MUST be put in bold with the html <b></b> tag."
            "A reader should be able to read only those words in bold and still know get the gist of what the article was saying."
            "These important words or phrases will usually be nouns, but may also be adjectives or verbs."
            "When there are two words separated by the word 'and', both of the words should be put in bold with the html <b></b> tag."
            "Function words like 'and' or 'the' or numbers like 'ten' or 'three' should never be in bold."
            "For each of the bullet points, you will also help to choose up to 5 appropriate pictographic icon keywords. "
            "Those icon keywords, if read alone, should also give the reader a general idea of what the article was about."
            "These icon keywords should be put in order from most to least important / informative for representing the text in the bullet point."
            "These will be used as queries to search for icons that would demonstrate the concepts represented in that bullet point.\n"
            "Often, these key words will represent the words you put inside the html <b></b> tag."
            "Your search terms should abide by the following rules: \n "
            "- Search terms should consist of at most three words. \n"
            "- Search terms should only be very common words. \n"
            "- Search terms should be highly imageable. For instance, use 'sick person' instead of a specific disease, or 'brain with arrow' instead of a specific brain area. \n"
            '- Avoid using any words that have homonyms - for example, never use the word "change" because it might mean "affect" or "money". \n'
            "- The words should be semantically related to the words in the article - for example, the word 'heartbeat' should not be used if the article is about musical beats."
            "- If the bullet point includes negation (e.g. 'not', 'no', 'never'), you should always return a phrase like "
            "'Crossed out' or 'X' or 'Circle with X' to reflect this.\n\n"
            "Return your response in json format, matching the following schema: "
            + """
{
    "summary": [
        {
            "text": "bullet point 1",
            "icon_keywords": ["keyword1", "keyword2", ...]
        },
        {
            "text": "bullet point 2",
            "icon_keywords": ["keyword1", "keyword2", ...]
        }
    ],
    "title": "A new title for the paper that is short and simpler",
    "rating": <number between 1 and 10 rating your confidence in your response>,
}
""",
            role="system",
        ),
        oa.Message(abstract),
    ]


def just_run_summary(abstract: str) -> dict:
    prompt = summary_prompt(abstract)
    response = oa.completion(prompt, model=MODEL).strip()
    if response.startswith("```json"):
        logger.debug("Removing ```json prefix")
        # Remove all lines starting with ````
        response = "\n".join(
            [line for line in response.split("\n") if not line.startswith("```")]
        )
    logger.info(f"Generated the following summary: {response}")
    response = json.loads(response)
    return response


def generate_bullets(summary: Summary, abstract: str) -> None:
    prompt = summary_prompt(abstract)
    response = oa.completion(prompt, model=MODEL).strip()
    if response.startswith("```json"):
        logger.debug("Removing ```json prefix")
        # Remove all lines starting with ````
        response = "\n".join(
            [line for line in response.split("\n") if not line.startswith("```")]
        )
    logger.info(f"Generated the following summary: {response}")
    response = json.loads(response)
    summary.metadata.simplified_title = response["title"]
    for entry in response["summary"]:
        icons = []
        for keyword in entry['icon_keywords']:
            icons.append(Icon(keyword))
        summary.bullets.append(Bullet(entry["text"], icons))
    summary.rating = str(response["rating"])
