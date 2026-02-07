import json
from typing import Any, Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.core.config import settings

# Scopes
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me.readonly",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.readonly",
    "openid"
]

class GoogleAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

    def get_flow(self, redirect_uri=None, scopes=SCOPES) -> Flow:
        return Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=scopes,
            redirect_uri=redirect_uri or self.redirect_uri
        )

    def exchange_code_for_token(self, code: str):
        """
        Exchanges an authorization code for access and refresh tokens.
        """
        # For SPA popup flow, redirect_uri must be 'postmessage'
        # We pass scopes=None to accept whatever scopes were granted by the User/Frontend
        flow = self.get_flow(redirect_uri="postmessage", scopes=None)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "id_token": credentials.id_token, # Has email, sub, etc.
        }

    def get_credentials(self, refresh_token: str) -> Credentials:
        """
        Reconstructs credentials from the stored user refresh token.
        """
        return Credentials(
            token=None, # It will refresh automatically
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=SCOPES
        )

    def build_service(self, refresh_token: str, service_name="classroom", version="v1"):
        creds = self.get_credentials(refresh_token)
        return build(service_name, version, credentials=creds)
