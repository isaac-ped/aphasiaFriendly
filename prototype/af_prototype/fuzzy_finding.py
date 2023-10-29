"""Attempt to extract abstracts from an academic PDF"""
import re
from collections import defaultdict
from pathlib import Path

import textract

from .logger import logger


def extract_abstract(pdf_file: Path, output: Path) -> str:
    """Try to find the abstract in a PDF file.

    :param pdf_file: Path to the pdf to scan
    :param output: If provided, will create files output/<section>.txt for each guessed section
    :returns: The contents of the abstract section if found.
        Otherwise, the first section of the PDF.
    """

    text = textract.process(str(pdf_file)).decode("utf-8")

    heading = "NONE"
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
            heading = re.sub(r"^\d+\.\s*", "", contents).strip()
            continue
        sections[heading.lower()] += "\n" + section
    if output:
        output.mkdir(exist_ok=True)
        for name, contents in sections.items():
            out_file = output / f"{name}.txt"
            logger.debug(f"Writing section to {out_file}")
            with out_file.open("w") as f:
                f.write(contents)

    if "abstract" in sections:
        return sections["abstract"]
    else:
        return sections["none"]
