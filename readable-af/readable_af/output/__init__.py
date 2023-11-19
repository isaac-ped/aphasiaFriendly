from pathlib import Path
from readable_af.model.summary import Summary


def generate_pptx(summary: Summary, out: Path):
    out.mkdir(exist_ok=True, parents=True)
    out_file = out / "summary.md"
    with out_file.open("w") as f:
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
