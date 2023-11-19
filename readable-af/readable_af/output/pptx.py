from pathlib import Path
import subprocess
from readable_af.model.summary import Summary


def generate(summary: Summary, out: Path) -> Path:
    out.mkdir(exist_ok=True, parents=True)
    md_file = out.parent / "summary.md"
    with md_file.open("w") as f:
        f.write(f"% {summary.metadata.title}\n")
        f.write(f"% {', '.join(summary.metadata.authors)}\n")
        f.write(f"% {summary.metadata.date}\n")
        for bullet in summary.bullets:
            print(f"**********\n{bullet.text}")
            print(f"Keywords: {', '.join([icon.keyword for icon in bullet.icons])}")
            f.write(f"\n\n###  {bullet.text.strip()}\n")
            f.write("\n:::::::::::::: {.columns}")
            for icon in bullet.icons:
                icon.save(out)
                f.write('\n\n::: {.column width="40%"}')
                f.write(f"\n![{icon.keyword}]({icon.filename})\n")
                f.write("\n:::")
            f.write("\n::::::::::::::")

    subprocess.check_call(
        ["pandoc", "-t", "pptx", "-s", "summary.md", "-o", "summary.pptx"],
        cwd=str(out.parent),
    )
    return out / "summary.pptx"
