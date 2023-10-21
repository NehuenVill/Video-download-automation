from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload



SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'creds.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)


def upload():

    file_metadata = {
        'name': 'MyFile.txt',
    }

    media = MediaFileUpload('MyFile.txt', mimetype='text/plain')

    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print('File ID: %s' % file.get('id'))

if __name__ == '__main__':

    upload()
