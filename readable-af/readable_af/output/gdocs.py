import copy
from dataclasses import dataclass
from functools import cache
import os.path
from pathlib import Path
import tempfile
from typing import Any

from ..model.request import Ctx
from ..logger import logger
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

# The ID of a sample document.
DOCUMENT_ID = "15r42eZ8fBQmEi40rxa5rkLPZXePih5Dvn99bLwDq57Y"


@cache
def build_service() -> Any:
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)
        return service
    except HttpError as err:
        print(err)

@cache_af()
def create_folder(name: str):
    service = build_service()
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    file = service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")

class GoogleDocGenerator:

    @staticmethod
    def generate(summary: Summary, ctx: Ctx) -> None:
        service = build_service()
        # Make a temporary file to upload
        assert ctx.output_file is not None
        folder = create_folder("Readable AF")
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
