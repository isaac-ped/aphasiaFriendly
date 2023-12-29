"""Attempt to extract abstracts from an academic PDF"""
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

from ..logger import logger
from ..model.request import Ctx

KNOWN_SECTIONS = (
    "abstract",
    "summary",
    "introduction",
    "intro",
    "methods",
    "method",
    "materials and methods",
    "results",
    "discussion",
    "limitations",
)

N_PAGES = 3

# Cache only the most recent file
@lru_cache(maxsize=1)
def _extract_pdf_text(pdf_file: Path) -> str:
    reader = PdfReader(pdf_file)
    pages = []
    for page in reader.pages[:N_PAGES]:
        pages.append(page.extract_text())
    return " ".join(pages)

def find_section_index(text: str, section: str, start_idx = 0) -> int:
    """Given a block of text, find the starting index of a section with heuristics"""

    # Look for the section name in all caps
    logger.debug(f"Looking for {section.upper()}")
    idx = text.find(section.upper(), start_idx)
    if idx != -1:
        return idx
    # Try to find it with spaces between each character
    for section_name in [section, section.upper()]:
        spaced_section = " ".join(section_name)
        logger.debug(f"Looking for {section_name}")
        idx = text.find(spaced_section, start_idx)
        if idx != -1:
            return idx
    # Try to find it with a '<number>. before it'
    regex = r"^\d+\.\s*" + section + r"\s*"
    logger.debug(f"Looking for {regex}")
    match = re.search(regex, text[start_idx:], re.MULTILINE | re.IGNORECASE)
    if match:
        return match.start() + start_idx
    
    # If all else fails, try to find it at the end of a line in title-case
    regex = section.title() + r"\s*\n"
    logger.debug(f"Looking for {regex}")
    match = re.search(regex, text[start_idx:], re.MULTILINE | re.IGNORECASE)
    if match:
        return match.start() + start_idx
    return -1


def _section_heading(text: str) -> str | None:
    """Given a block of text, return a section heading if we can find one."""
    contents = text.strip()
    first_line = contents.split("\n")[0].strip()
    # Some journals seem to have headings with spaces between each character,
    # like: "A B S T R A C T"
    # Substitute all spaces that are between two letters with a single space
    space_re = r"((?<=\s\w)|(?<=^\w))(\s)(?=\w(\s|$))"
    # ^^ This regex is nasty.
    # You can see it in detail here: https://www.regexr.com/7mhgh
    first_line = re.sub(space_re, "", first_line)
    if len(first_line) < 5:
        # I don't know of any important headings with lengths less than this.
        return None

    # See if the line contains only "<number>. <1-3 words>"
    # in which Words must start with a capital letter, but then may be any case.
    regex = r"^(?:\d+\.)\s*([A-Z][a-zA-Z]+\s?){1,3}$"
    match = re.match(regex, first_line)
    if match and len(first_line) > 3:
        # Remove the 'number.' from the front if it is there
        return match.group(1).strip().lower()

    # Otherwise, see if the line is one of the known section headings above
    for section in KNOWN_SECTIONS:
        if section in first_line.lower():
            return section


def find_abstract(input_file: Path) -> str:
    """Return a portion of the article that likely contains the abstract"""
    logger.info(f"Attempting to find abstract in {input_file}")
    paper_text = _extract_pdf_text(input_file)
    abstract_ind = find_section_index(paper_text, "abstract")
    if abstract_ind == -1:
        logger.warn("Could not find abstract in paper. Attempting to find 'summary' instead")
        abstract_ind = find_section_index(paper_text, "summary")
    if abstract_ind == -1:
        logger.warn("Could not find summary in paper either. Attempting to find introduction.")
        intro_ind = find_section_index(paper_text, "introduction")
        if intro_ind == -1:
            logger.warn("Could not find introduction in paper either. Giving up.")
            raise ValueError("Could not find abstract")
        logger.info("Returning everything prior to introduction as abstract")
        if intro_ind > 4192:
            logger.error("Abstruct is impossibly long. Refusing to process!")
            raise ValueError("Abstract is too long")
        return paper_text[:intro_ind]
            
            
    # Find the next section heading after the abstract
    next_ind = len(paper_text)
    for section in KNOWN_SECTIONS:
        section_ind = find_section_index(paper_text, section, abstract_ind)
        if section_ind > abstract_ind and section_ind < next_ind:
            next_ind = section_ind

    if next_ind - abstract_ind > 4192:
        logger.error("Abstract is impossibly long. Refusing to process!")
        raise ValueError("Abstract is too long")
    return paper_text[abstract_ind:next_ind]

    sections = find_sections(input_file)
    section_order = list(sections.keys())
    if "abstract" in sections:
        # If we find the abstract explicitly in a section, we start that point in the file
        abstract_ind = section_order.index("abstract")
    elif "summary" in sections:
        abstract_ind = section_order.index("summary")
    else:
        # Otherwise, we assume the abstract is near the beginning of the file
        abstract_ind = 0

    # Either way, we return that section and one more section after it,
    # Just in case we are cutting it off early
    guessed_text = "\n\n".join(
        sections[section] for section in section_order[abstract_ind : abstract_ind + 2]
    )
    return guessed_text
    # If the guessed text is too long, just use the located section instead
    if len(guessed_text) > 4192:
        logger.warn(f"Broad heuristic for abstract location is too long ({len(guessed_text)} characters). Using single section instead.")
        guessed_text = sections[section_order[abstract_ind]]
    if len(guessed_text) > 4192:
        raise ValueError("Possible abstract is too long. Sorry!")
    logger.info(f"Found abstract of length {len(guessed_text)}")
    return guessed_text


def find_preamble(input_file: Path) -> str:
    """Return a portion of the article that hopefully includes title, authors, and date"""
    sections = find_sections(input_file)
    section_order = list(sections.keys())
    return sections[section_order[0]]


def find_sections(pdf_file: Path) -> dict[str, str]:
    """Try to find the abstract in a PDF file.

    :param pdf_file: Path to the pdf to scan
    :param output: If provided, will create files output/<section>.txt for each guessed section
    :returns: The contents of the abstract section if found.
        Otherwise, return the first couple sections of the PDF.
    """
    text = _extract_pdf_text(pdf_file)
    heading = "NONE"
    sections = defaultdict(str)

    # First heading defaults to "NONE"
    # This section is where anything before an auto-detected section will show up
    heading = "NONE"
    sections = defaultdict(str)
    for section in text.split("\n\n"):
        possible_heading = _section_heading(section)
        if possible_heading:
            heading = possible_heading
        # Replace any sets of 3 or more newlines with just two newlines
        section = re.sub(r"\n{2,}", "\n\n", section)
        sections[heading] += "\n" + section + "\n\n"

    return sections
