from ..external import openai as oa
from readable_af.model.summary import Bullet, Metadata
from ..logger import logger


def metadata_prompt(preamble: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that handles the extraction of text from scientific articles. "
            "You will be provided with text that has been extracte from a scientific PDF and asked for a specific section "
            "of that text. The text may be extracted cleanly, in which case you may just be able to return the text "
            "in the same format that it was given to you. "
            "Whenever a message is sent to you, it will contain messily extracted metadata from a scientific article. "
            "This metadata will should include the title, authors, and publication date of the article, but may also contain "
            "other extraneous information, newlines, or other formatting. "
            "You should extract the title, authors, and publication date from the metadata and return them in the following format:"
            "The tile should be on the first line of the response, all authors on the second line, and the date on the third line. "
            "If multiple dates are available, you should choose the latest date and output only that. "
            "If there are multiple authors, return up to three authors separated by commas and then 'et al.' "
            "You should never respond with an answer other the specified text to be extracted",
            role="system",
        ),
        oa.Message(preamble),
    ]


def generate_metadata(preamble: str) -> Metadata:
    messages = metadata_prompt(preamble)
    response = oa.completion(messages, model="gpt-4")
    title, authors, date = response.split("\n")
    logger.info(f"Generated the following metadata: {title=}, {authors=}, {date=}")
    return Metadata(title, authors.split(","), date)


def abstract_prompt(messy_abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that handles the extraction of text from scientific articles. "
            "You will be provided with text that has been extracted from a scientific PDF and asked for a specific section "
            "of that text. The text may be extracted cleanly, in which case you may just be able to return the text "
            "in the same format that it was given to you. "
            "However, you may be given the text alongside some other information or metadata that was added in a "
            "messy extraction process. In that case, try to return only the part of the text that represents the section "
            "that was requested. "
            "You should never respond with an answer other the specified text to be extracted",
            role="system",
        ),
        oa.Message(messy_abstract),
    ]


def generate_abstract(messy_abstract: str) -> str:
    messages = abstract_prompt(messy_abstract)
    abstract = oa.completion(messages, model="gpt-4")
    logger.info(f"Generated the following asbtract: {abstract}")
    return abstract


def summary_prompt(abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that processes scientific articles into a few simple sentences "
            "that are understandable by someone that has difficulty reading. "
            "You will be passed the abstract of a scientific article and asked to summarize it. "
            "Your summary should always produce 5 bullet points, each of which use very simple syntax "
            "and vocabulary. "
            "In particular, the words that you use should be as simple and common as possible, "
            "and the sentences that you produce should have a flesch-kincaid score of less than 65."
            "All messages sent to you will contain a scientific abstract, and you should return "
            "only with the summary as specified above, with each bullet on its own line, and never any additional text.",
            role="system",
        ),
        oa.Message(abstract),
    ]


def generate_bullets(abstract: str) -> list[Bullet]:
    prompt = summary_prompt(abstract)
    summary = oa.completion(prompt, model="gpt-4")
    logger.info(f"Generated the following summary: {summary}")
    return [Bullet(line) for line in summary.split("\n")]


def icon_prompt(summary: str) -> list[oa.Message]:
    return [
        oa.Message(
            "You are an assistant that helps to choose apprioriate pictographic icons to accomany bullet points. "
            "You will be provided with a list of bullet points (one per line) and asked to provide a list of keywords that would "
            "allow you to search for an appropriate icon that would demonstrate the concepts represented in the bullet point. "
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
            "keyword for a bullet point, you should return an empty line.",
            role="system",
        ),
        oa.Message(summary),
    ]


def generate_icon_keywords(bullets: list[Bullet]) -> list[list[str]]:
    """For each bullet, generate a list of keywords that would be appropriate for an icon.

    :returns: A list of keywords for each bullet point. If no keywords are appropriate for a bullet, an empty list is returned.
    """
    prompt = icon_prompt("\n".join(bullet.text for bullet in bullets))
    icons_response = oa.completion(prompt, model="gpt-4")
    logger.info(f"Generated the following icons: {icons_response}")
    return [line.split(",") for line in icons_response.split("\n")]
