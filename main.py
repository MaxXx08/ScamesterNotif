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
DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1494319720483000353/-V3eYBtculecVXR3rykI1qxwDGEE2mgwahQButUijZ4rUAULGGj5DjbO__n3s5226pdG'
CHECK_INTERVAL = 30
# ------------------------

def authenticate():
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)

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

        files = results.get('files', [])
        all_files.extend(files)

    return all_files

def main():
    service = authenticate()
    last_state = {}
    first_run = True  # ✅ prevents spam on startup

    print("Monitoring started...")

    while True:
        files = get_files(service)

        for file in files:
            file_id = file['id']
            name = file['name']
            modified = file['modifiedTime']

            # 🆕 NEW FILE DETECTED
            if file_id not in last_state:
                last_state[file_id] = modified

                if not first_run:
                    link = f"https://drive.google.com/file/d/{file_id}/view"
                    msg = f"🆕 New file added: **{name}**\n🔗 {link}"

                    send_to_discord(msg)
                    print("New file:", name)

                continue

            # ✏️ FILE UPDATED
            if last_state[file_id] != modified:
                last_state[file_id] = modified

                link = f"https://drive.google.com/file/d/{file_id}/view"
                msg = f"✏️ Updated: **{name}**\n🔗 {link}"

                send_to_discord(msg)
                print("Updated:", name)

        first_run = False  # ✅ after first loop
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()