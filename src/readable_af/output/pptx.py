import subprocess
from ..model.request import Ctx

from readable_af.model.summary import Summary
from .generator import Generator


class PPTXGenerator(Generator):

    EXTENSION = "pptx"

    @classmethod
    def generate_text(cls, summary: Summary, ctx: Ctx) -> str:
        """Returns ppt output in markdown format as a string"""
        text = ""
        # TODO: Unify this function with the one below it
        # (or just delete these -- we don't necessarily need pptxgenerator anymore)
        text += f"% {summary.metadata.title} )\n"
        text += f"% Rating: {summary.rating}\n"
        text += f"% {', '.join(summary.metadata.authors)}\n"
        # text += f"% {summary.metadata.date}\n"
        for bullet in summary.bullets:
            text += f"**********\n{bullet.text}"
            text += f"Keywords: {', '.join([icon.keyword for icon in bullet.icons])}"
            text += f"\n\n###  {bullet.text.strip()}\n"
            text += "\n:::::::::::::: {.columns}"
            for icon in bullet.icons[:2]:
                text += "\n\n::: {.column}"
                text += f"\n![{icon.keyword}]({icon.filename})\n"
                text += "\n:::"
            text += "\n::::::::::::::"
        return text
        

    @classmethod
    def generate(cls, summary: Summary, ctx: Ctx):
        out = ctx.output_file
        assert out is not None
        assert summary.metadata is not None, (
            "Summary metadata must be populated before generating output"
        )
        out.parent.mkdir(exist_ok=True, parents=True)
        md_file = out.parent / "summary.md"

        with md_file.open("w") as f:
            f.write(cls.generate_text(summary, ctx))

        subprocess.check_call(
            ["pandoc", "-t", "pptx", "-s", "summary.md", "-o", out],
            cwd=str(out.parent),
        )
