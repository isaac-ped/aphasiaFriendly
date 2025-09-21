
import yaml
from ..model.request import Ctx

from readable_af.model.summary import Summary


class YamlGenerator:

    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        out = ctx.output_file
        assert out is not None
        out.parent.mkdir(exist_ok=True, parents=True)
        with out.open("w") as f:
            yaml.dump(summary.asdict(), f, sort_keys=False)
