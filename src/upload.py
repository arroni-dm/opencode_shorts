import os, json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.json")
SECRETS_PATH = os.path.join(os.path.dirname(__file__), "..", "client_secrets.json")

def get_credentials():
    token_json = os.getenv("YOUTUBE_TOKEN_JSON")
    secrets_json = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON")
    if token_json:
        info = json.loads(token_json)
        creds = Credentials.from_authorized_user_info(info, SCOPES)
    elif os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    else:
        raise RuntimeError("No YouTube token found")
    if secrets_json and not creds.valid and creds.refresh_token:
        pass
    if not creds.valid and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    return creds

def upload(video_path, title, description, tags, privacy_status="private", category_id="22"):
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, chunksize=1024*1024, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress()*100)}%")
    print("Uploaded video id:", response["id"])
    return response["id"]

if __name__ == "__main__":
    print("upload module ok")
