from typing import Any, Dict, List, Optional
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

class GoogleDriveService:
    def __init__(self, auth_service):
        self.auth = auth_service

    def download_drive_file(self, refresh_token: str, file_id: str) -> tuple[bytes, str, str] | None:
        """
        Downloads a file from Google Drive.
        Returns (content, filename, mime_type) or None if failure.
        """
        try:
            service = self.auth.build_service(refresh_token, service_name="drive", version="v3")
            # Get metadata for name and mimeType
            meta = service.files().get(fileId=file_id, fields="name,mimeType,size").execute()
            filename = meta.get("name")
            mime_type = meta.get("mimeType")
            
            # Skip google apps documents (Docs, Sheets, Slides) as they require export
            if mime_type.startswith("application/vnd.google-apps"):
                # We could export as PDF here if we wanted, but sticking to uploaded PDFs for now
                if mime_type == "application/vnd.google-apps.document":
                     # Example: export to PDF
                     # request = service.files().export_media(fileId=file_id, mimeType='application/pdf')
                     pass 
                return None

            request = service.files().get_media(fileId=file_id)
            file_io = BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return file_io.getvalue(), filename, mime_type
        except Exception as e:
            print(f"Error downloading drive file {file_id}: {e}")
            return None
