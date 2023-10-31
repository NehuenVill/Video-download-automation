import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from time import sleep


SERVICE_ACCOUNT_FILE = 'creds.json'
SCOPE = ['https://www.googleapis.com/auth/drive.file']

def upload(video_name):

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPE)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPE)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    while True:

        try:
            service = build('drive', 'v3', credentials=creds)

            file_metadata = {
            'name': video_name,
            'parents': ["1fMezlqTno0cegWEunNNGQw2MBKLxwifc"]
            }

            media = MediaFileUpload(f"videos/{video_name}", mimetype='video/mp4', chunksize=5_000_000, resumable=True)

            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            url = f"https://drive.google.com/file/d/{file.get('id')}"

            return url

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.

            # print(f'An error occurred: {error}')

            sleep(0.2)

if __name__ == '__main__':

    print(upload('video_test.mp4'))
