"""High-level API for summarization."""

from pathlib import Path

import yaml

from ..model.request import Ctx

from ..external import nounproject
from ..model.summary import Bullet, Icon, Metadata, Summary
from . import generation


def get_bullet_icons(bullet: Bullet, used_icons: set[int]):
    bullet_icons: set[int] = set()
    successes: list[Icon] = []
    failures: list[Icon] = []
    for icon in bullet.icons:
        if nounproject.populate(icon, used_icons | bullet_icons):
            bullet_icons.add(icon.id)
            successes.append(icon)
        else:
            failures.append(icon)
        if len(successes) >= 2:
            break
    if len(successes) < 2:
        # If we can't find two unique icons, try again but allow icons from earilier bullets
        new_failures = []
        for icon in failures:
            if nounproject.populate(icon, bullet_icons):
                bullet_icons.add(icon.id)
                successes.append(icon)
            else:
                new_failures.append(icon)
            if len(successes) >= 2:
                break
        new_failures = failures
    used_icons.update(bullet_icons)
    bullet.icons = successes


def summarize(ctx: Ctx) -> Summary:
    # Get the file extension from the input file
    input = ctx.input
    if input.abstract is None:
        assert input.file is not None
        file_extension = input.file.suffix
        if file_extension == "pdf":
            raise NotImplementedError("PDF summarization not yet implemented")
        else:
            with open(input.file) as f:
                contents = f.readlines()
            title = contents[0].strip()
            authors = contents[1].strip()
            abstract = "\n".join(contents[2:])
            metadata = Metadata(title=title, authors=authors.split(","), date="")
    else:
        abstract = input.abstract
        assert input.title is not None
        assert input.authors is not None
        metadata = Metadata(
            title=input.title, authors=input.authors.split(","), date=""
        )

    summary = Summary(metadata=metadata, bullets=[])
    generation.generate_bullets(summary, abstract)
    # icon_keywords = generation.generate_icon_keywords(summary.bullets)
    used_ids: set[int] = set()

    for bullet in summary.bullets:
        get_bullet_icons(bullet, used_ids)

    return summary


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
