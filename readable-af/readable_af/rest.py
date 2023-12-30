# save this as app.py
from pathlib import Path
from flask import Flask, render_template, request, send_file, Response
from .model.request import Ctx
from .logger import setup_logging, logger
from . import api
import tempfile

app = Flask(__name__)

from flask_limiter import Limiter, RequestLimit
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app) # <--------------------------------- New line
setup_logging(3)

def rate_limited(limit: RequestLimit):
    logger.warning(f"Rate limit exceeded: {limit.limit}")
    return Response(render_template("rate_limit.html"), 429)

@app.route("/", methods=["GET"])
@limiter.limit('10 per 1 minute', on_breach=rate_limited) # <------------ New line
def index():
    logger.debug("Received request to index")
    return render_template("index.html")
    

@app.route("/api/summarize", methods=["POST"])
@limiter.limit('10 per 1 minute') # <------------ New line
def summarize_file():
    logger.debug("Received request to summarize file")
    abstract = request.form["abstract"].strip()
    title = request.form["title"].strip()
    authors = request.form["authors"].strip()
    # Create a unique temporary file to save the paper into
    with tempfile.TemporaryDirectory() as tmp_out:
        ctx = Ctx()
        ctx.input.abstract = abstract
        ctx.input.authors = authors
        ctx.input.title = title
        ctx.output_format = "pptx"
        ctx.output_file = Path(tmp_out) / "summary.pptx"
        api.summarize(ctx)
        assert ctx.output_file is not None
        return send_file(ctx.output_file)