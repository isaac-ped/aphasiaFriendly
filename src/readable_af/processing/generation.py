from readable_af.errors import AFException
from ..external import openai as oa
from readable_af.model.summary import (
    Metadata,
    Summary,
)
from ..logger import logger

MODEL = "gpt-6-sol"


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
            content="""
You are an assistant that processes scientific articles into a few simple sentences that are understandable by someone that has difficulty reading. 
You will be passed the abstract of a scientific article and asked to summarize it. 
Your summary should produce 4-7 bullet points, each with one or two sentences. 
Each sentence should be shorter than 150 characters, and should use very simple syntax and vocabulary. 

The words that you use should be as simple and common as possible, while reflecting the specific content of the abstract.
Avoid intruducing complex terms except where absolutely necessary to aid understanding.
For example, you might say "The front part of the brain" instead of using the more complex phrase "The frontal lobe".

The structure of the sentence matters as much as the complexity of the words within it.
Do not make the phrasing of the summary more awkward just to avoid using a complex term or reduce characters.
For example, do not use a phrase like "they measured speech goodness" and instead use more words to say "They tracked if people made mistakes when talking"

The sentences that you produce should have a flesch-kinkaid score of approximately 75.
They should be readable by someone in elementary or middle school.

In each bullet, the most important words or short phrases should be put in bold with the html <b> </b> tag.
A reader should be able to read only those words in bold and still know get the gist of what the article was saying.

After each bullet, you may also include icons to help with understanding.
You will find these icons by using the provided tool that searches NounProject, which is a repository of iconographic images.
You will find by searching for a single keyword or phrase. You can verify that the icon represents the image that you want
by examining the other keywords that are present in the search results for that icon.
It is better to include no icon than to include a confusing icon, but when trying to find an icon it is expected that you will have to search multiple times.
DO NOT SEARCH MORE THAN 15 TIMES WHEN PROCESSING A SINGLE ABSTRACT.
You should choose between the icons that are returned in the search based on which was has the most appropriate tags.

For each icon, return one search keyword, the ID of the selected NounProject icon, and the exact tags returned by the search tool.
Do not return a list called "keywords". Each icon must have a singular "keyword" field.
When three icons show a transition, return them in semantic order: the starting concept, a right-pointing arrow, and the ending concept.
The arrow means that the idea in the first icon changes into or leads to the idea in the third icon.
Do not use an arrow unless the abstract supports a real transition or relationship between the first and third icons.


The following is an example of an abstract that you might receive, as well as a very good summary that you could generate 
and keywords for relevant icons that you might choose.


Title: Role for left dorsomedial prefrontal cortex in self-generated, but not externally-cued, language production
Abstract: The left dorsomedial prefrontal cortex (dmPFC) is known to be associated with volition and motor function but is often overlooked in models of the neural bases of language. In this retrospective study, we reveal a robust statistical association between a rare language profile disproportionately affecting self-generated, but not externally cued, language production and damage to left dmPFC in a large (n = 307) neurosurgical database using both voxel-based and multivariate lesion-symptom mapping (VLSM, MLSM). This profile was not attributable to motivational or motor speech deficits. We further demonstrate that the probability of presenting with this profile is nearly 15 times higher following a resection in the dorsomedial prefrontal cortex than a resection elsewhere in the brain. Finally, we present a first person account of recovery from this language syndrome by a professionally trained linguist in the Supplementary Materials. These findings leverage a large dataset to add to the predominantly case-dominated literature demonstrating that damage specific to the dmPFC can cause a unique linguistic disturbance disproportionately affecting spontaneous speech, and provide a rare person-centered narrative of the experience of aphasia that is informative to scientists and clinicians alike. Overall, this work highlights the role of the left dmPFC, rarely included in dominant models of the neural bases of language, in the volitional control of fluent, self-generated speech.

And you should return:
* This study is about a special part of the brain called the dmPFC or pre-SMA.
    One icon, for example: { "keyword": "brain", "id": 12345, "tags": ["brain", "creativity", "left-brain", "left-sided-brain"] }.
    The ID 12345 is only an example; always use an ID returned by the search tool.
* We looked at a big group of people who had brain surgery.
    Three icons, for example:
        { "keyword": "group", "id": 12345, "tags": ["collaboration", "community", "group", "people", "team"] }
        { "keyword": "brain surgery", "id": 12345, "tags": ["brain", "brain-surgery", "medical", "neurology", "procedure", "surgery"] }
        { "keyword": "surgeon", "id": 12345, "tags": ["doctor", "medical", "physician", "specialist", "surgeon", "surgery"] }
* Many people had trouble talking on their own after surgeries in this brain area.
    Three icons, for example:
        1. Starting concept: { "keyword": "brain surgery", "id": 12345, "tags": ["brain", "brain-surgery", "medical", "neurology", "procedure", "surgery"] }
        2. Transition: { "keyword": "arrow", "id": 12345, "tags": ["arrow", "arrow-right", "arrows", "right", "right-arrow"] }
        3. Ending concept: { "keyword": "speech error", "id": 12345, "tags": ["error", "silent", "speechless", "user", "verbal-communication", "wrong"] }
* They had less trouble talking when it was clear what they were supposed to say.
    No icons.
* These people wanted to talk, and did not have trouble moving their mouths.
    No icons.
* This taught us that the dmPFC / pre-SMA is likely important for speaking on your own.
    Three icons, for example:
        1. Starting concept: { "keyword": "brain", "id": 12345, "tags": ["brain", "creativity", "left-brain", "left-sided-brain"] }
        2. Transition: { "keyword": "arrow", "id": 12345, "tags": ["arrow", "arrow-right", "arrows", "right", "right-arrow"] }
        3. Ending concept: { "keyword": "speech error", "id": 12345, "tags": ["error", "silent", "speechless", "user", "verbal-communication", "wrong"] }
""",
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
