from pydantic import BaseModel, Field
from ..model.request import Ctx

from readable_af.model.summary import Summary


class ComparisonBullet(BaseModel):
    text: str = Field(description="The text accompanying one bullet point of a summary")


class ComparisonModel(BaseModel):
    original_title: str = Field(
        description="The original title of the paper to be summarized"
    )
    original_abstract: str = Field(
        description="The original abstract of the paper to be summarized"
    )
    simplified_title: str = Field(
        description="A simplified version of the paper's title"
    )
    summary: list[ComparisonBullet] = Field(
        description="A list of bullet points summarizing the article's abstract"
    )


class ComparisonGenerator:
    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        out = ctx.output_file
        assert out is not None
        out.parent.mkdir(exist_ok=True, parents=True)

        assert ctx.input.title is not None
        assert ctx.input.abstract is not None
        assert summary.metadata is not None
        
        simplified_title = summary.metadata.simplified_title

        comparison = ComparisonModel(
            original_title=ctx.input.title,
            original_abstract=ctx.input.abstract,
            simplified_title=simplified_title,
            summary=[ComparisonBullet(text=bullet.text) for bullet in summary.bullets],
        )

        with out.with_suffix(".json").open("w") as f:
            f.write(comparison.model_dump_json(indent=2))
