import subprocess
from ..model.request import Ctx

from readable_af.model.summary import Summary


class PPTXGenerator:
    @staticmethod
    def generate(summary: Summary, ctx: Ctx):
        out = ctx.output_file
        assert out is not None
        out.parent.mkdir(exist_ok=True, parents=True)
        md_file = out.parent / "summary.md"

        used_icons = set()
        with md_file.open("w") as f:
            f.write(f"% {summary.metadata.title} )\n")
            f.write(f"% Rating: {summary.rating}\n")
            f.write(f"% {', '.join(summary.metadata.authors)}\n")
            # f.write(f"% {summary.metadata.date}\n")
            for bullet in summary.bullets:
                print(f"**********\n{bullet.text}")
                print(f"Keywords: {', '.join([icon.keyword for icon in bullet.icons])}")
                f.write(f"\n\n###  {bullet.text.strip()}\n")
                f.write("\n:::::::::::::: {.columns}")
                for icon in bullet.icons[:2]:
                    used_icons.add(icon.id)
                    icon.write(out.parent)
                    f.write("\n\n::: {.column}")
                    f.write(f"\n![{icon.keyword}]({icon.filename})\n")
                    f.write("\n:::")
                f.write("\n::::::::::::::")

        subprocess.check_call(
            ["pandoc", "-t", "pptx", "-s", "summary.md", "-o", "summary.pptx"],
            cwd=str(out.parent),
        )
