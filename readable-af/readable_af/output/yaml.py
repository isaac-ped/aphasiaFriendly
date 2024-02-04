from pathlib import Path

import yaml

from readable_af.model.summary import Summary


class YamlGenerator:

    @staticmethod
    def generate(summary: Summary, out: Path) -> None:
        out.parent.mkdir(exist_ok=True, parents=True)
        with out.open("w") as f:
            yaml.dump(summary.asdict(), f, sort_keys=False)
