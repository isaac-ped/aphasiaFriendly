"""High-level API for summarization."""

from pathlib import Path

import yaml

from ..model.request import Ctx

from ..external import nounproject
from ..model.summary import Bullet, Icon, Metadata, Summary
from . import generation


def get_icon_contents(summary: Summary):
    for bullet in summary.bullets:
        for icon in bullet.icons:
            contents=nounproject.get_icon(icon_id=icon.id)
            assert contents is not None
            icon.populate(contents)

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
            metadata = Metadata(title=title, authors=authors.split(","), date="", simplified_title="")
    else:
        abstract = input.abstract
        assert input.title is not None
        assert input.authors is not None
        metadata = Metadata(
            title=input.title, authors=input.authors.split(","), date="", simplified_title=""
        )

    summary = Summary(metadata=metadata, bullets=[])
    generation.generate_bullets(summary, abstract)
    # icon_keywords = generation.generate_icon_keywords(summary.bullets)
    # used_ids: set[int] = set()

    get_icon_contents(summary)

    return summary


def reload(input_file: Path) -> Summary:
    with input_file.open() as f:
        input = yaml.safe_load(f)
    metadata = Metadata.fromdict(input["metadata"])
    bullets = [Bullet.fromdict(bullet) for bullet in input["bullets"]]

    # used_ids: set[int] = set()

    # for bullet in bullets:
    #    get_bullet_icons(bullet, used_ids)

    return Summary(
        metadata=metadata,
        bullets=bullets,
    )
