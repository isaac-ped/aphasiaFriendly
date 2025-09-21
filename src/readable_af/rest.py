# save this as app.py
from functools import cache
import json
import os
from pathlib import Path
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    stream_with_context,
)
import flask
import requests

from readable_af.output import gdocs
from .model.request import Ctx
from .logger import setup_logging, logger
from . import api
from .config import Config
import tempfile

IS_LOCAL = os.environ.get("FLASK_RUN_FROM_CLI", "") == "true"
if IS_LOCAL:
    print("RUNNING LOCALLY")
    SCHEME = "http"
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
else:
    SCHEME = "https"


app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.config['SERVER_NAME'] = 'readable-af.fly.dev'
app.config["SESSION_TYPE"] = "filesystem"

app.config["PREFERRED_URL_SCHEME"] = SCHEME

from flask_limiter import Limiter, RequestLimit
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)  # <--------------------------------- New line
setup_logging(3)


def rate_limited(limit: RequestLimit):
    logger.warning(f"Rate limit exceeded: {limit.limit}")
    return Response(render_template("rate_limit.html"), 429)


SAMPLE_DIR = Path(__file__).parent / "templates/samples"


@app.route("/", methods=["GET"])
@limiter.limit("10 per 1 minute", on_breach=rate_limited)  # <------------ New line
def index():
    return render_template(
        "index.html.j2",
        sitekey=Config.get().recapcha_site_key,
        authenticated=gdocs.get_credentials(),
    )


@app.route("/auth", methods=["GET"])
def auth():
    if gdocs.get_credentials():
        return flask.redirect(flask.url_for("summarize"))

    return render_template(
        "auth.html.j2",
        sitekey=Config.get().recapcha_site_key,
        authenticated=gdocs.get_credentials(),
    )


@app.route("/summarize", methods=["GET"])
@limiter.limit("10 per 1 minute", on_breach=rate_limited)  # <------------ New line
def summarize():
    if not gdocs.get_credentials():
        flash("Please authenticate with Google before continuing.")
        return flask.redirect(flask.url_for("auth"))
    return render_template(
        "summarize.html.j2",
        sitekey=Config.get().recapcha_site_key,
    )


@app.route("/api/summarize", methods=["GET", "POST"])
@limiter.limit("10 per 1 minute")  # <------------ New line
def summarize_file():
    credentials = gdocs.get_credentials()
    if not credentials:
        flash("Sorry, your authentication with google has expired. Please log in again")
        return flask.redirect(flask.url_for("authorize"))

    if "g-recaptcha-response" not in request.form:
        logger.warning("No recaptcha response")
        #return "Sorry, you are not human!"
        return "Sorry, an error has occurred. Please email deborah.levy@princeton.edu to report this error."

    captcha_response = request.form["g-recaptcha-response"]
    if not is_human(captcha_response):
        logger.warning("Recapcha failed")
        #return "Sorry, you are not human!"
        return "Sorry, an error has occurred. Please email deborah.levy@princeton.edu to report this error."

    abstract = request.form["abstract"]
    title = request.form["title"]
    authors = request.form["authors"]

    try:
        ctx = Ctx()
        ctx.credentials = credentials
        ctx.input.abstract = abstract
        ctx.input.authors = authors
        ctx.input.title = title
        ctx.output_format = "gdoc"
        with tempfile.TemporaryDirectory() as tmp_out:
            ctx.output_file = Path(tmp_out) / "summary"
            api.summarize(ctx)
            assert ctx.output_link is not None
    except Exception as e:
        logger.exception(f"Error summarizing: {e}")
        return render_template(
            "result.html.j2",
            error=str(e),
        )

    return render_template(
        "result.html.j2",
        error=None,
        output_link=ctx.output_link,
    )


def is_human(captcha_response):
    """Validating recaptcha response from google server
    Returns True captcha test passed for submitted form else returns False.
    """
    logger.debug(f"Capcha response: {captcha_response}")
    secret = Config.get().recapcha_secret
    payload = {"response": captcha_response, "secret": secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    logger.debug(f"Response text: {response_text}")
    return response_text["success"]


@app.route("/authorize")
def authorize():
    logger.debug("Request to /authorize")
    flow = gdocs.get_oauth_flow()
    flow.redirect_uri = flask.url_for("oauthcallback", _external=True, _scheme=SCHEME)
    logger.debug(f"Setting redirect_uri to {flow.redirect_uri}")

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )

    # Store the state so we can retrieve it after the callback
    flask.session["state"] = state
    logger.debug(f"Redirecting to {authorization_url}")
    return flask.redirect(authorization_url)


@app.route("/oauthcallback")
def oauthcallback():
    logger.debug("Request to /oauthcallback")
    if "state" not in flask.session:
        logger.error("No state in session")
        return flask.redirect(
            flask.url_for("authorize", _external=True, _scheme=SCHEME)
        )

    flow = gdocs.get_oauth_flow(flask.session["state"])
    flow.redirect_uri = flask.url_for("oauthcallback", _external=True, _scheme=SCHEME)
    logger.debug(f"Setting redirect_uri to {flow.redirect_uri} from oauthcallback")

    # https preference isn't being encoded well...
    curr_url = flask.request.url
    if curr_url.startswith("http://"):
        curr_url = curr_url.replace("http://", "https://", 1)
    logger.debug("Current URL: " + curr_url)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = curr_url
    logger.debug(f"Fetching token for {flask.request.url}")
    flow.fetch_token(authorization_response=authorization_response)

    flask.session["credentials"] = gdocs.credentials_to_dict(flow.credentials)
    return flask.redirect(flask.url_for("index", _external=True, _scheme=SCHEME))
