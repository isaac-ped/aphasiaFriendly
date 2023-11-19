"""High-level API for summarization."""
from pathlib import Path
from ..external import nounproject
from ..model.summary import Summary
from . import text_extraction
from . import generation


def summarize(input_file: Path) -> Summary:
    abstract_contents = text_extraction.find_abstract(input_file)
    preamble_contents = text_extraction.find_preamble(input_file)

    metadata = generation.generate_metadata(preamble_contents)
    abstract = generation.generate_abstract(abstract_contents)
    bullets = generation.generate_bullets(abstract)
    icon_keywords = generation.generate_icon_keywords(bullets)

    for bullet, keywords in zip(bullets, icon_keywords):
        for keyword in keywords:
            icon = nounproject.search(keyword)
            if icon is not None:
                bullet.icons.append(icon)

    return Summary(
        metadata=metadata,
        bullets=bullets,
    )
