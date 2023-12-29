import json
from ..external import openai as oa
from readable_af.model.summary import Bullet, Metadata, Summary
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
    return Metadata(title.strip(), [a.strip() for a in authors.split(",")], date.strip())


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
            "Your summary should always produce 5-7 sentences of summary. "#, with each sentence "
            #"separated from other sentences by the | character."
            "Each sentence should be shorter than 150 characters, and should use very simple syntax and vocabulary. "
            "The words that you use should be as simple and common as possible, "
            "while still reflecting the specific content of the abstract. "
            "If you introduce complicated, low-frequency terms, please explicitly define them in simpler terms. "
            "Use only those simpler terms moving forward. "
            "Be specific about brain locations, "
            "for example, do not say 'brain spots', but say 'temporal lobe' or 'frontal lobe'."
            "The sentences that you produce should have a flesch-kincaid score of less than 75. "
            "Be conservative in your statement of facts. "
            "For example, do not say 'The brain does not', but say 'The brain may not.' "
            "The last bullet point should summarize the abstract in one sentence. "
            #"All messages sent to you will contain a scientific abstract, and you should return "
            #"only with the summary as specified above, without any additional text. ",
            "Return your response in json format, with the keys 'summary', containing a list of strings with the bullet points, " 
            "and 'rating', containing your rating on a scale from 1-10 of how good the summary you produced seems to be. ",
            role="system",
        ),
        oa.Message(abstract),
    ]


def generate_bullets(summary: Summary, abstract: str) -> None:
    prompt = summary_prompt(abstract)
    response = oa.completion(prompt, model=MODEL)
    logger.info(f"Generated the following summary: {summary}")
    if response.startswith("```json"):
        response = response.removesuffix("```json").removesuffix("```")
    response=json.loads(response)
    for entry in response["summary"]:
        summary.bullets.append(Bullet(entry))
    summary.rating = str(response["rating"])


def icon_prompt(summary: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that helps to choose apprioriate pictographic icons to accomany bullet points. "
            "You will be provided with a list of bullet points (one per line) and you should respond with a list of EXACTLY 5 comma-separated search terms"
            "that will be used as queries to search for icons that would demonstrate the concepts represented in the bullet point.\n"
            "Your search terms should abide by the following rules: \n "
            "- Search terms should consist of at most three words. \n"
            "- Search terms should only be very common words. \n"
            "- Only return phrases that have a CLEAR pictographic representation. For instance, use 'sick person' instead of a specific disease. \n"
            '- Avoid using any words that have homographs - for example, never use the word "change" because it might mean "affect" or "money" \n'
            "- If the bullet point includes negation (e.g. 'not', 'no', 'never'), you should always return a phrase like "
            "'Crossed out' or 'X' or 'Circle with X' to reflect this.\n\n"
            "The following are some examples of good phrases: \n"
            "- To represent a staticstic getting larger, you might return 'upward arrow'. "
            "- To represent a positive emoution you might return 'smiling faces' or 'happy people' \n"
            "- To represent a speech disorder, you may return 'speech bubble with X'. \n"
            "- To represent something not changing, you might return 'flat graph' or 'arrow with X'.\n\n"
            "Your output should ONLY contain these keywords with the keywords for each bullet point on their own line. \n"
            "Keywords within a bullet point should be separated by a comma, and should not be in quotes. \n "
            "Within a line, keywords should be sorted in order of quality, with the best keywords first.\n\n"
            "You MUST always output 5 search terms for EVERY line that was input, and no other text or formatting\n",
            role="system",
        ),
        oa.Message(summary),
    ]


def generate_icon_keywords(bullets: list[Bullet]) -> list[list[str]]:
    """For each bullet, generate a list of keywords that would be appropriate for an icon.

    :returns: A list of keywords for each bullet point. If no keywords are appropriate for a bullet, an empty list is returned.
    """
    prompt = icon_prompt("\n".join("*" + bullet.text for bullet in bullets))
    return [
        ["ok","ok"]
    ] * 5
    icons_response = oa.completion(prompt, model=MODEL)
    logger.info(f"Generated the following icons: {icons_response}")
    return [
        [kw.strip() for kw in line.split(",")]
        for line in icons_response.split("\n")
        if line.strip()
    ]
