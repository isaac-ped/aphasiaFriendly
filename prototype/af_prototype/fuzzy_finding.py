"""Attempt to extract abstracts from an academic PDF"""
import re
from collections import defaultdict
from pathlib import Path

import textract

from .logger import logger

KNOWN_SECTIONS=(
    "abstract",
    "introduction",
    "intro",
    "methods",
    "method",
    "materials and methods",
    "results",
    "discussion",
    "limitations"
)

def section_heading(text: str) -> str | None:
    """Given a block of text, return a section heading if we can find one."""
    contents = text.strip()
    first_line = contents.split("\n")[0].strip()
    # Some journals seem to have headings with spaces between each character,
    # like: "A B S T R A C T"
    # Substitute all spaces that are between two letters with a single space
    space_re = r"((?<=\s\w)|(?<=^\w))(\s)(?=\w(\s|$))"
    first_line = re.sub(space_re, "", first_line)
    if len(first_line) < 5:
        # I don't know of any important headings with lengths less than this.
        return None

    # See if the line contains only "<number>. <1-3 words>"
    # in which Words must start with a capital letter, but then may be any case.
    regex = r"^(?:\d+\.)\s*([A-Z][a-zA-Z]+\s){1,3}$"
    match = re.match(regex, first_line)
    if match and len(first_line) > 3:
        # Remove the 'number.' from the front if it is there
        return match.group(1).strip().lower()
    
    # Otherwise, see if the line is one of the known section headings above
    for section in KNOWN_SECTIONS:
        if section in first_line.lower():
            return section

def extract_abstract(pdf_file: Path, output: Path | None = None) -> str:
    """Try to find the abstract in a PDF file.

    :param pdf_file: Path to the pdf to scan
    :param output: If provided, will create files output/<section>.txt for each guessed section
    :returns: The contents of the abstract section if found.
        Otherwise, return the first couple sections of the PDF.
    """

    text = textract.process(str(pdf_file)).decode("utf-8")

    heading = "NONE"
    section_order = [heading]
    sections = defaultdict(str)

    # We attempt to find headings for sections by looking for a word on its own line.

    heading = "NONE"
    section_order = [heading]
    sections = defaultdict(str)
    for section in text.split("\n\n"):
        possible_heading = section_heading(section)
        if possible_heading:
            heading = possible_heading
            section_order.append(heading)
        sections[heading] += "\n" + section + "\n\n"

    # If "output" is provided, write each section to a file in that folder
    if output is not None:
        output.mkdir(exist_ok=True)
        for i, (name, contents) in enumerate(sections.items()):
            out_file = output / f"{i}-{name}.txt"
            logger.debug(f"Writing section to {out_file}")
            with out_file.open("w") as f:
                f.write(contents)

    if "abstract" in sections:
        # If we find the abstract explicitly in a section, we start that point in the file
        abstract_ind = section_order.index("abstract")
    else:
        # Otherwise, we assume the abstract is near the beginning of the file
        abstract_ind = 0

    # Either way, we return that section and one more section after it,
    # Just in case we are cutting it off early
    guessed_text = "\n\n".join(
        sections[section] for section in section_order[abstract_ind : abstract_ind + 2]
    )
    return guessed_text