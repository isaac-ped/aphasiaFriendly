# save this as app.py
import json
import os
from pathlib import Path
from flask import Flask, render_template, request, send_file, Response
import flask
import requests

from readable_af.output import gdocs
from .model.request import Ctx
from .logger import setup_logging, logger
from . import api
from .config import Config
import tempfile

IS_LOCAL = os.environ.get("HOST", "...").endswith(".local")
if IS_LOCAL:
    SCHEME="http"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
else:
    SCHEME="https"


app = Flask(__name__)
app.secret_key = os.urandom(24)
# app.config['SERVER_NAME'] = 'readable-af.fly.dev'
app.config['SESSION_TYPE'] = 'filesystem'

app.config['PREFERRED_URL_SCHEME'] = SCHEME

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
    return render_template("index.html", sitekey=Config.get().recapcha_site_key)
    

@app.route("/authorize")
def authorize():
    logger.debug("Request to oauthcallback")
    flow = gdocs.get_oauth_flow()
    flow.redirect_uri = flask.url_for('oauthcallback', _external=True, _scheme=SCHEME)
    logger.debug(f"Setting redirect_uri to {flow.redirect_uri}")

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    
    # Store the state so we can retrieve it after the callback
    flask.session['state'] = state
    logger.debug(f"Redirecting to {authorization_url}")
    return flask.redirect(authorization_url)

@app.route("/oauthcallback")
def oauthcallback():
    logger.debug("Request to oauthcallback")
    state = flask.session.get('state', '')
    flow = gdocs.get_oauth_flow(state)
    flow.redirect_uri = flask.url_for('oauthcallback', _external=True, _scheme=SCHEME)
    logger.debug(f"Setting redirect_uri to {flow.redirect_uri}")

    # https preference isn't being encoded well...
    curr_url =  flask.request.url
    if curr_url.startswith("http://"):
        curr_url = curr_url.replace("http://", "https://", 1)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = curr_url
    logger.debug(f"Fetching token for {flask.request.url}")
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    flask.session['credentials'] = gdocs.credentials_to_dict(credentials)
    return flask.redirect(flask.url_for('summarize_file', _external=True, _scheme=SCHEME))


@app.route("/api/summarize", methods=["GET","POST"])
@limiter.limit('10 per 1 minute') # <------------ New line
def summarize_file():
    inputs = flask.session.setdefault('inputs', {})
    for x in ["abstract", "title", "authors", 'g-recaptcha-response']:
        if x in request.form:
           inputs[x] = request.form[x].strip()
        if x not in inputs:
            return f"Missing required input {x}: {inputs}, {flask.session.get('state')}"
    logger.debug("Received request to summarize file")
    logger.debug(f"inputs {inputs}")
    logger.debug(f"state {flask.session.get('state')}")

    if 'credentials' not in flask.session:
        return flask.redirect(flask.url_for('authorize', _external=True, _scheme=SCHEME))

    captcha_response = inputs['g-recaptcha-response']
    if not is_human(captcha_response):
        return "Sorry, you are not human!"


    logger.debug("GOT past authorization!")
    abstract = inputs['abstract']
    title = inputs['title']
    authors = inputs['authors']
    credentials = gdocs.Credentials(**flask.session['credentials'])

    # Create a unique temporary file to save the paper into
    with tempfile.TemporaryDirectory() as tmp_out:
        ctx = Ctx()
        ctx.credentials = credentials
        ctx.input.abstract = abstract
        ctx.input.authors = authors
        ctx.input.title = title
        ctx.output_format = "gdoc"
        ctx.output_file = Path(tmp_out) / "summary"
        api.summarize(ctx)
        assert ctx.output_link is not None
        return flask.redirect(ctx.output_link)
    
def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    print(captcha_response)
    secret = Config.get().recapcha_secret
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    print(response_text)
    return response_text['success']