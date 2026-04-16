import os
import time
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# -------- CONFIG --------
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

FOLDER_IDS = [
    '1EeAvHS1nokOsfLOxYkIEVZv3TdkH1E6h',
    '10tnMfOleuctSn23MqLQ6OmzVep_-YOMY'
]

DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1494332113376251918/X4ZshMaQCZtJjqlrXQmWRn_YBVcNYpK-Cn3gvv8zZy_Gu9wtwMU9TNVOiucZTf9LSkwY'
CHECK_INTERVAL = 30
# ------------------------

def authenticate():
    creds = None

    # Load saved token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no valid creds → MUST use console flow (Railway-safe)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES
        )

        # ✅ FIX FOR RAILWAY (NO BROWSER)
        creds = flow.run_console()

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def send_to_discord(message):
    requests.post(DISCORD_WEBHOOK, json={"content": message})

def get_files(service):
    all_files = []

    for folder_id in FOLDER_IDS:
        results = service.files().list(
            q=f"'{folder_id}' in parents",
            fields="files(id, name, modifiedTime)"
        ).execute()

        all_files.extend(results.get('files', []))

    return all_files

def main():
    service = authenticate()
    last_state = {}
    first_run = True

    print("Monitoring started...")

    while True:
        files = get_files(service)

        for file in files:
            file_id = file['id']
            name = file['name']
            modified = file['modifiedTime']

            # 🆕 NEW FILE
            if file_id not in last_state:
                last_state[file_id] = modified

                if not first_run:
                    msg = f"🆕 New file: **{name}**"
                    send_to_discord(msg)
                    print("New:", name)

                continue

            # ✏️ UPDATE FILE
            if last_state[file_id] != modified:
                last_state[file_id] = modified

                msg = f"✏️ Updated: **{name}**"
                send_to_discord(msg)
                print("Updated:", name)

        first_run = False
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
