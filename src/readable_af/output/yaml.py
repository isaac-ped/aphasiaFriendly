import yaml
from ..model.request import Ctx
from .generator import Generator

from readable_af.model.summary import Summary


class YamlGenerator(Generator):

    EXTENSION = "yaml"

    @classmethod
    def generate_text(cls, summary: Summary, ctx: Ctx):
        return yaml.dump(summary.asdict(), sort_keys=False)
