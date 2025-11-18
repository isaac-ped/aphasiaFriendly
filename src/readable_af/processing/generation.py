from readable_af.errors import AFException
from ..external import openai as oa
from readable_af.model.summary import (
    Metadata,
    Summary,
)
from ..logger import logger

MODEL = "gpt-4o-2024-08-06"


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
            "Your summary should produce 4-7 sentences of summary. "  # , with each sentence "
            # "separated from other sentences by the | character."
            "Each sentence should be shorter than 150 characters, and should use very simple syntax and vocabulary. "
            "The words that you use should be as simple and common as possible, "
            "while reflecting the specific content of the abstract. "
            "If you introduce complex terms, please explicitly define them in simpler terms. "
            "Use only those simpler terms moving forward. "
            "Be specific about brain locations, "
            "for example, do not say 'brain spots', but say 'temporal lobe' or 'frontal lobe'. "
            "The sentences that you produce should have a flesch-kincaid score of less than 75. "
            # "Avoid medical or scientific jargon as much as possible. "
            # "The sentences should be grammatical - that is, do not say sentences like 'Found astrocytomas near eloquent regions. "
            # "Be conservative in your statement of facts. "
            # "For example, do not say 'The brain does not', but say 'The brain may not.' "
            # "The last bullet point should summarize the abstract in one sentence. "
            "The two or three most important words or short phrases in each bullet MUST be put in bold with the html <b></b> tag. "
            "A reader should be able to read only those words in bold and still know get the gist of what the article was saying. "
            # "These important words or phrases will usually be nouns, but may also be adjectives or verbs. "
            # "When there are two words separated by the word 'and', both of the words should be put in bold with the html <b></b> tag. "
            # "Function words like 'and' or 'the' or numbers like 'ten' or 'three' should never be in bold. "
            "For each of the bullet points, you will also choose 0-3 appropriate pictographic icon keywords. "
            "These icon keywords, if viewed as their most likely picographic representation, "
            "should also give the reader a general idea of what the article was about. "
            "These icon keywords should be put in order from most to least important / informative for representing the text in the bullet point. "
            # "These will be used as queries to search for icons that would demonstrate the concepts represented in that bullet point. "
            # "Often, these key words will represent the words you put inside the html <b></b> tag. "
            # "Your search terms should abide by the following rules: \n "
            # "- Search terms should consist of at most three words. \n"
            # "- Search terms should only be very common words. \n"
            # "- Search terms should be highly imageable. For instance, use 'sick person' instead of a specific disease, or 'brain with arrow' instead of a specific brain area. \n"
            # '- Avoid using any words that have homonyms - for example, never use the word "change" because it might mean "affect" or "money". \n'
            # "- The words should be semantically related to the words in the article - for example, the word 'heartbeat' should not be used if the article is about musical beats.\n"
            # "- If the bullet point includes negation (e.g. 'not', 'no', 'never'), you should always return a phrase like\n"
            # "'Crossed out' or 'X' to reflect this.\n\n"
            "Return your response in the structured format that will be provided.",
            role="system",
        ),
        oa.Message(
            content="Individuals with post-stroke aphasia tend to recover their language to some extent; however, it remains challenging to reliably predict the nature and extent of recovery that will occur in the long term. "
            "The aim of this study was to quantitatively predict language outcomes in the first year of recovery from aphasia across multiple domains of language and at multiple timepoints post-stroke. "
            "We recruited 217 patients with aphasia following acute left hemisphere ischaemic or haemorrhagic stroke and evaluated their speech and language function using the Quick Aphasia Battery acutely and then acquired longitudinal follow-up data at up to three timepoints post-stroke: 1 month (n = 102), 3 months (n = 98) and 1 year (n = 74). "
            "We used support vector regression to predict language outcomes at each timepoint using acute clinical imaging data, demographic variables and initial aphasia severity as input. "
            "We found that ∼60% of the variance in long-term (1 year) aphasia severity could be predicted using these models, with detailed information about lesion location importantly contributing to these predictions. "
            "Predictions at the 1- and 3-month timepoints were somewhat less accurate based on lesion location alone, but reached comparable accuracy to predictions at the 1-year timepoint when initial aphasia severity was included in the models. "
            "Specific subdomains of language besides overall severity were predicted with varying but often similar degrees of accuracy. "
            "Our findings demonstrate the feasibility of using support vector regression models with leave-one-out cross-validation to make personalized predictions about long-term recovery from aphasia and provide a valuable neuroanatomical baseline upon which to build future models incorporating information beyond neuroanatomical and demographic predictors.",
            role="user",
        ),
        oa.Message(
            content="""{
    "bullets": [
        {
            "text": "<b>Aphasia</b> is a <b>problem</b> with <b>language</b> that can happen after <b>stroke</b>",
            "icons": [
                {"keyword": "miscommunication"},
                {"keyword": "stroke"}
            ]
        },
        {
            "text": "Language usually <b>gets better</b>, but we can't always <b>predict how much</b>",
            "icons": [
                {"keyword": "prediction"}
            ]
        },
        {
            "text": "We looked at a <b>big group</b> of <b>people</b> with <b>aphasia</b>, their <b>brains</b>, and their <b>language</b>",
            "icons": [
                {"keyword": "brain"},
                {"keyword": "crowd"},
                {"keyword": "person talking"}
            ]
        },
        {
            "text": "We used <b>math</b> to try and <b>predict language</b> across the <b>first year</b> after stroke",
            "icons": [
                {"keyword": "regression"},
                {"keyword": "predict"}
            ]
        },
        {
            "text": "This math did a <b>pretty good job</b> making predictions (about <b>60%</b> correct)!",
            "icons": [
                {"keyword": "predict"},
                {"keyword": "test"},
                {"keyword": "check mark"}
            ]
        },
        {
            "text": "We <b>hope</b> that more math like this will <b>help</b> doctors, therapists, researchers, and people with aphasia have <b>clearer expectations</b> about <b>aphasia recovery</b>",
            "icons": []
        }
    ],
    "rating": "10",
    "metadata": {
        "title": "Example Title",
        "authors": ["Author Name"],
        "date": "2024",
        "simplified_title": "Using math and the brain to predict language recovery after stroke"
    }
}""",
            role="assistant",
        ),
        oa.Message(content=abstract),
    ]


def just_run_summary(abstract: str) -> Summary:
    """Generate a summary using structured output and return the validated response."""
    prompt = summary_prompt(abstract)
    response = oa.completion_structured(
        prompt, response_model=Summary, model=MODEL
    )
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
        response = oa.completion_structured(
            prompt, response_model=Summary, model=MODEL
        )
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
    if response.metadata and response.metadata.simplified_title:
        summary.metadata.simplified_title = response.metadata.simplified_title

    # Copy bullets directly - they already use the Summary structure with Icon objects
    # Icons will have only the keyword field populated; IDs/URLs are filled in post-processing
    summary.bullets = response.bullets
    summary.rating = response.rating
