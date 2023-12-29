"""High-level API for summarization."""
from pathlib import Path

import yaml

from ..errors import AFException
from ..external import nounproject
from ..logger import logger
from ..model.summary import Bullet, Icon, Metadata, Summary
from . import generation, text_extraction


def get_bullet_icons(bullet: Bullet, used_icons: set[int]):
    successes: list[Icon] = []
    for icon in bullet.icons:
        if nounproject.populate(icon, used_icons):
            used_icons.add(icon.id)
            successes.append(icon)
        if len(successes) >= 2:
            break
    if len(successes) != 2:
        raise AFException(f"Could not find enough icons for bullet '{bullet.text}'")
    bullet.icons = successes


def summarize(input_file: Path) -> Summary:
    # Get the file extension from the input file
    file_extension = input_file.suffix
    if file_extension == "pdf":
        abstract_contents = text_extraction.find_abstract(input_file)
        preamble_contents = text_extraction.find_preamble(input_file)
        metadata = generation.generate_metadata(preamble_contents)
        abstract = generation.generate_abstract(abstract_contents)
    else:
        with open(input_file) as f:
            contents = f.readlines()
        title = contents[0].strip()
        authors = contents[1].strip()
        abstract = "\n".join(contents[2:])
        metadata = Metadata(title=title, authors=authors.split(","), date="")


    bullets = generation.generate_bullets(abstract)
    icon_keywords = generation.generate_icon_keywords(bullets)

    used_ids: set[int] = set()

    for bullet, keywords in zip(bullets, icon_keywords):
        bullet.icons = [Icon(keyword) for keyword in keywords]
        get_bullet_icons(bullet, used_ids)

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
        get_bullet_icons(bullet, used_ids)

    return Summary(
        metadata=metadata,
        bullets=bullets,
    )
