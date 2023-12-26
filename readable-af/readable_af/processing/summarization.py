"""High-level API for summarization."""
from pathlib import Path

import yaml

from ..external import nounproject
from ..logger import logger
from ..model.summary import Bullet, Icon, Metadata, Summary
from . import generation, text_extraction


def get_bullet_icons(bullet: Bullet, keywords: list[str], used_icons: set[int]):
    for keyword in keywords:
        if len(bullet.icons) >= 2:
            return
        icon = Icon(keyword)
        if nounproject.populate(icon, used_icons):
            logger.info(f"Found icon for keyword {keyword}")
            bullet.icons.append(icon)
        else:
            logger.info(f"Could not find icon for {keyword}")


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
            logger.debug(
                f"Got only {len(bullet.icons)} icons. Trying again to get icons for bullet"
            )
            get_bullet_icons(bullet, keywords, used_ids)

    return Summary(
        metadata=metadata,
        bullets=bullets,
    )


def reload(input_file: Path) -> Summary:
    with input_file.open() as f:
        input = yaml.safe_load(f)
    metadata = Metadata.fromdict(input["metadata"])
    bullets = [Bullet.fromdict(bullet) for bullet in input["bullets"]]
    used_ids: set[int] = set()
    for bullet in bullets:
        for icon in bullet.icons:
            nounproject.populate(icon, used_ids)
    return Summary(
        metadata=metadata,
        bullets=bullets,
    )
