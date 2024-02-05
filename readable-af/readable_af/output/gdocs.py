import copy
from dataclasses import dataclass
from functools import cache
import os.path
from pathlib import Path
import tempfile
from typing import Any

from ..model.request import Ctx
from ..logger import logger
from ..config import Config
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import yaml

from ..processing.summarization import get_bullet_icons

from .html import HtmlGenerator

from ..model.summary import Bullet, Metadata, Summary
from ..external.caching import cache_af
from googleapiclient.http import MediaFileUpload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

####
# Much of this is copied from here: https://developers.google.com/identity/protocols/oauth2/web-server#python
####


def credentials_to_dict(credentials)  -> dict[str, Any]:
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

def get_oauth_flow(state: Any = None) -> Flow:
    f = Flow.from_client_secrets_file(
        Config.get().google_client_secrets_file,
        scopes=SCOPES,
        state=state
        )
    return f

def authenticate(credentials):
    return build(
      "drive", "v3", credentials=credentials)

_FOLDER_MIMETYPE = "application/vnd.google-apps.folder"

def create_folder(service, name):
    service.files()
    existing = service.files().list(q=f"name='{name}' and mimeType='{_FOLDER_MIMETYPE}'").execute()
    if existing.get("files"):
        return existing.get("files")[0].get("id")
    file_metadata = {
        "name": name,
        "mimeType": _FOLDER_MIMETYPE
    }
    folder = service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

class GoogleDocGenerator:

    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        assert ctx.credentials is not None
        service = authenticate(ctx.credentials)
        # Make a temporary file to upload
        assert ctx.output_file is not None
        folder = create_folder(service, "Readable AF")
        ctx.output_file = ctx.output_file.with_suffix(".html")
        HtmlGenerator.generate(summary, ctx)
        logger.info(f"Wrote HTML to {ctx.output_file}")
        media = MediaFileUpload(ctx.output_file, mimetype="text/html", resumable=False)
        file = (
            service.files()
            .create(
                body={
                    "name": f"TESTING: {summary.metadata.simplified_title}",
                    "parents": [folder],
                    "mimeType": "application/vnd.google-apps.document",
                },
                media_body=media,
            ).execute()
        )
        ctx.output_link = f"https://docs.google.com/document/d/{file.get('id')}/edit"
        logger.info(f"Generated google doc: {ctx.output_link}")

    # drive.files().create({}).execute()
    # drive.files().create({
    #     "resource": {
    #         "name": summary.metadata.title,
    #         "mimeType": "application/vnd.google-apps.document",
    #     },
    #     "media": {
    #         "mimeType": "text/html",
    #         "body": html_output
    #     },
    #     "fields": "id"
    #     }
    # )


# if __name__ == "__main__":
#     from ..processing import summarization
#     from ..logger import setup_logging
#     setup_logging(4)
#     summary = summarization.reload(Path("outputs/Agrammatism_and_Paragrammatism_A_Cortical_Double_D.pdf/summary.yaml"))
    
#     create_test_document(summary)
