"""High-level API for summarization."""
from pathlib import Path
from ..external import nounproject
from ..model.summary import Bullet, Summary
from . import text_extraction
from . import generation


def get_bullet_icons(bullet: Bullet, keywords: list[str], used_icons: set[int]):
    for keyword in keywords:
        if len(bullet.icons) >= 2:
            return
        icons = nounproject.search(keyword, 5)
        for icon in icons:
            if icon.id not in used_icons:
                bullet.icons.append(icon)
                used_icons.add(icon.id)
                break


def summarize(input_file: Path) -> Summary:
    abstract_contents = text_extraction.find_abstract(input_file)
    preamble_contents = text_extraction.find_preamble(input_file)

    metadata = generation.generate_metadata(preamble_contents)
    abstract = generation.generate_abstract(abstract_contents)
    bullets = generation.generate_bullets(abstract)
    icon_keywords = generation.generate_icon_keywords(bullets)

    used_ids: set[int] = set()

    for bullet, keywords in zip(bullets, icon_keywords):
        get_bullet_icons(bullet, keywords, used_ids)
        # If we couldn't get two unique icons per keyword, try again
        # allowing us to use another icon for the same keyword
        if len(bullet.icons) < 2:
            get_bullet_icons(bullet, keywords, used_ids)

    return Summary(
        metadata=metadata,
        bullets=bullets,
    )
