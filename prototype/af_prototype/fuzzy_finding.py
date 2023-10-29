import re
from collections import defaultdict
from pathlib import Path

import textract

from .logger import logger


def extract_abstract(pdf_file: Path, output: Path):
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
