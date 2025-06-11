from base64 import b64encode
import re
import subprocess
from pathlib import Path
from ..model.request import Ctx

from readable_af.model.summary import Summary


class HtmlGenerator:

    @staticmethod
    def generate_text(summary: Summary) -> str:
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
        text += f"<h1 style='text-align:center'>{summary.metadata.simplified_title}</h1>\n"
        authors = ", ".join(summary.metadata.authors)
        # Remove any numeric characters from the authors list
        authors = re.sub(r'\d+', '', authors)
        authors = re.sub(r'\s+', ' ', authors)
        text += f"<div class='authors'>Authors: {authors}</div><br/>\n"
        text += "<br/>"*3
        text += f"<h2 class='subtitle'> An accessible version of: </h2><h2> {summary.metadata.title}  </h2>\n"
        text += f"<hr class='pb' />"
        for bullet in summary.bullets:
            text += f"<h3 class='bullet' style='text-align:center'>{bullet.text.strip()}</h3>\n"
            text += "<div class='icons' style='text-align:center'>\n"
            for icon in bullet.icons[:2]:
                text += f"<img alt='{icon.keyword}' width=75  height=75 src='data:image/png;base64,{b64encode(icon.icon).decode("utf-8")}'/>"
            text += "</div>\n"
        text += f"<h1 style='text-align:left;font-style:italic>Drafted with Article Friend</h1>
        text += "</body></html>"
        return text

    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        out = ctx.output_file
        assert out is not None
        out.parent.mkdir(exist_ok=True, parents=True)
        with out.open("w") as f:
            f.write(HtmlGenerator.generate_text(summary))
