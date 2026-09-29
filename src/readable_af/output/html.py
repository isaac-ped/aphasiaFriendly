from base64 import b64encode
import re
from ..model.request import Ctx

from ..model.summary import Summary
from .generator import Generator


class HtmlGenerator(Generator):

    EXTENSION = "html"

    @classmethod
    def generate_text(cls, summary: Summary, ctx: Ctx) -> str:
        assert summary.metadata is not None, (
            "Summary metadata must be populated before generating output"
        )
        text = """

        <html>
        <head>
        <style>
        .icons {
            margin-top: 0;
            margin-bottom:1em;
        }
        .icons img {
            margin-top:0;
            margin-left: 2.5em;
            margin-right: 2.5em;
        }
        h2 {
            font-family:sans-serif;
            text-align:center;
        }
        .subtitle {
            text-align:center;
            font-weight:normal;
        }
        .bullet {
            font-family:sans-serif;
            font-weight:normal;
            margin-bottom:0;
        }
        .authors {
            text-align:center;
            font-weight:bold;
            font-size:12pt;
        }
        </style>

        </head>
        <body>
        """
        text += (
            f"<h1 style='text-align:center'>{summary.metadata.simplified_title}</h1>\n"
        )
        authors = ", ".join(summary.metadata.authors)
        # Remove any numeric characters from the authors list
        authors = re.sub(r"\d+", "", authors)
        authors = re.sub(r"\s+", " ", authors)
        text += f"<div class='authors'>Authors: {authors}</div><br/>\n"
        text += "<br/>" * 3
        text += f"<h2 class='subtitle'> An accessible version of: </h2><h2> {summary.metadata.title}  </h2>\n"
        text += "<hr class='pb' />"
        for bullet in summary.bullets:
            text += f"<h3 class='bullet' style='text-align:center'>{bullet.text.strip()}</h3>\n"
            text += "<div class='icons' style='text-align:center'>\n"
            for icon in bullet.icons[:2]:
                text += f"<img alt='{icon.keyword}' width=75  height=75 src='data:image/png;base64,{b64encode(icon.icon).decode('utf-8')}'/>"
            text += "</div>\n"
        text += "</body></html>"
        return text
