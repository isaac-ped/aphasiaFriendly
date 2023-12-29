"""Attempt to extract abstracts from an academic PDF"""
import re
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

from ..logger import logger

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
