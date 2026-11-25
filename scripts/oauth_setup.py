import os, json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    secrets = os.getenv("YOUTUBE_CLIENT_SECRETS_JSON")
    if secrets:
        info = json.loads(secrets)
    else:
        path = os.path.join(BASE, "client_secrets.json")
        with open(path) as f:
            info = json.load(f)
    flow = InstalledAppFlow.from_client_config(info, SCOPES)
    creds = flow.run_local_server(port=8080)
    token_path = os.path.join(BASE, "token.json")
    with open(token_path, "w") as f:
        f.write(creds.to_json())
    print("Saved", token_path)
    print("Store its contents as GitHub secret YOUTUBE_TOKEN_JSON")

if __name__ == "__main__":
    main()
