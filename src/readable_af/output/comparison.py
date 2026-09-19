import json
from ..model.request import Ctx

from readable_af.model.summary import Summary


class ComparisonGenerator:
    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        out = ctx.output_file
        assert out is not None
        out.parent.mkdir(exist_ok=True, parents=True)

        orig_out = out.with_suffix(".orig.json")
        with orig_out.open("w") as f:
            json.dump(
                {
                    "title": ctx.input.title,
                    "abstract": ctx.input.abstract
                },
                f,
                indent=2
            )

        if summary.metadata:
            simplified_title = summary.metadata.simplified_title
        else:
            simplified_title = ctx.input.title

        with out.with_suffix(".json").open("w") as f:
            json.dump(
                {
                    "title": simplified_title,
                    "abstract": "\n".join(bullet.text for bullet in summary.bullets) 
                },
                f,
                indent=2,
            )
