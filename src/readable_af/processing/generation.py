from readable_af.errors import AFException
from ..external import openai as oa
from readable_af.model.summary import (
    Metadata,
    Summary,
)
from ..logger import logger

MODEL = "gpt-5-mini-2025-08-07"


def metadata_prompt(preamble: str) -> list[oa.Message]:
    return [
        oa.Message(
            content="You are an assistant that handles the extraction of text from scientific articles. "
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
        oa.Message(content=preamble),
    ]


def generate_metadata(preamble: str) -> Metadata:
    messages = metadata_prompt(preamble)
    response = oa.completion(messages, model=MODEL)
    title, authors, date = response.split("\n")
    logger.info(f"Generated the following metadata: {title=}, {authors=}, {date=}")
    return Metadata(
        title=title.strip(),
        authors=[a.strip() for a in authors.split(",")],
        date=date.strip(),
        simplified_title="",
    )


def abstract_prompt(messy_abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            content="You are an assistant that handles the extraction of an abstract from scientific articles.\n"
            "You will be provided with text that has been extracted from a scientific PDF and you should find and "
            "return the abstract from that text. It is possible that the text will be extracted cleanly, in which case "
            "you should just return the text in the same format that it was given to you.\n"
            "However, you may be given the text alongside some other information or metadata that was added in a "
            "messy extraction process. In that case, try to return only the part of the text that represents the abstract.\n\n"
            "You should never respond with an answer other the specified text to be extracted",
            role="system",
        ),
        oa.Message(content=messy_abstract),
    ]


def generate_abstract(messy_abstract: str) -> str:
    messages = abstract_prompt(messy_abstract)
    abstract = oa.completion(messages, model=MODEL)
    logger.info(f"Generated the following asbtract: {abstract}")
    return abstract.strip()


def summary_prompt(abstract: str) -> list[oa.Message]:
    return [
        oa.Message(
            content="You are an assistant that processes scientific articles into a few simple sentences "
            "that are understandable by someone that has difficulty reading. "
            "You will be passed the abstract of a scientific article and asked to summarize it. "
            "Your summary should produce 4-7 sentences of summary. "
            "Each sentence should be shorter than 150 characters, and should use very simple syntax and vocabulary. "
            "The words that you use should be as simple and common as possible, "
            "while reflecting the specific content of the abstract. "
            "If you introduce complex terms, please explicitly define them in simpler terms. "
            "Use only those simpler terms moving forward. "
            "Be specific about brain locations, "
            "for example, do not say 'brain spots', but say 'temporal lobe' or 'frontal lobe'. "
            "The sentences that you produce should have a flesch-kincaid score of less than 75. "
            "The two or three most important words or short phrases in each bullet MUST be put in bold with the html <b></b> tag. "
            "A reader should be able to read only those words in bold and still know get the gist of what the article was saying. "
            "For each bolded word, choose 1 icon. "
            "You will find these icons by searching NounProject, and will indicate the IDs of these icons in NounProject. "
            "Each icon should be UNIQUE. Do NOT reuse icons across different lines."
            "Use the tools provided to you to search for icons. ONLY use IDs that have been provided to you through these tools. "
            "Use the additional metadata provided by the tools to ensure that the icons you are choosing are appropriate. "
            "If you do not think the icons are appropriate, you can should out to more tool calls multiple times. "
            "I expect that you will perform approximately 10-20 searches for each summary, but it may be as many as 30. ",
            role="system",
        ),
        oa.Message(content=abstract),
    ]


def just_run_summary(abstract: str) -> Summary:
    """Generate a summary using structured output and return the validated response."""
    prompt = summary_prompt(abstract)
    response = oa.completion_structured(prompt, response_model=Summary, model=MODEL)
    logger.info(
        f"Generated the following summary: {response.model_dump_json(indent=2)}"
    )
    return response


def generate_bullets(summary: Summary, abstract: str) -> None:
    """Generate bullets for a summary using structured output from ChatGPT.

    This function uses OpenAI's structured output feature to ensure the response
    matches the expected format. The Summary structure is used directly, with Icon
    objects containing only keywords (IDs and URLs are left blank for post-processing).
    """
    prompt = summary_prompt(abstract)

    try:
        # Use structured output with Summary directly - OpenAI fills in the full Summary structure
        # This guarantees valid JSON matching our schema
        response = oa.completion_structured(prompt, response_model=Summary, model=MODEL)
        logger.info(
            f"Generated structured summary: {response.model_dump_json(indent=2)}"
        )
    except Exception as e:
        logger.exception("Failed to generate structured output from ChatGPT")
        raise AFException(
            "ChatGPT is providing an invalid response. Please try again later."
        ) from e

    # Populate the summary with the structured response
    # Use simplified_title from response metadata if provided
    assert summary.metadata is not None, (
        "Summary metadata must be populated before generating bullets"
    )
    if response.metadata and response.metadata.simplified_title:
        summary.metadata.simplified_title = response.metadata.simplified_title

    # Copy bullets directly - they already use the Summary structure with Icon objects
    # Icons will have only the keyword field populated; IDs/URLs are filled in post-processing
    summary.bullets = response.bullets
    summary.rating = response.rating
