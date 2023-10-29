"""Attempt to extract abstracts from an academic PDF"""
import re
from collections import defaultdict
from pathlib import Path

import textract

from .logger import logger


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

    for section in text.split("\n\n"):
        contents = section.strip()
        # Headings consist of one of two patterns:
        # ALL CAPS
        #  or
        # (number). ALL CAPS
        # on their own line.
        # This isn't a gret method. Or even necessarily a good method.
        # But it seems to work okay right now on like 2 examples?
        regex = r"^(?:\d+\.)?\s*[A-Z\s]+$"
        if re.match(regex, contents) and len(contents) > 3:
            # Remove the 'number.' from the front if it is there
            heading = re.sub(r"^\d+\.\s*", "", contents).strip().lower()
            section_order.append(heading)
            continue
        sections[heading] += "\n" + section

    # If "output" is provided, write each section to a file in that folder
    if output is not None:
        output.mkdir(exist_ok=True)
        for name, contents in sections.items():
            out_file = output / f"{name}.txt"
            logger.debug(f"Writing section to {out_file}")
            with out_file.open("w") as f:
                f.write(contents)

    # If we found a section labeled 'abstract', just return that
    # and hope we didn't cut off anything important
    if "abstract" in sections:
        return sections["abstract"]
    else:
        # Otherwise return the first two sections of the paper
        # (hopefully the first is the abstract)
        guess = ""
        for section in section_order[:2]:
            guess += sections[section] + "\n"
        return guess
