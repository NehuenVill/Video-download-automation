import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def insert_to_sheet(data):

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json')
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    body = {
        'values':[
            data
        ]
    }

    service = build('sheets', 'v4', credentials=creds)

    result = service.spreadsheets().values().append(spreadsheetId='1jONo_ERicgU_scGmnuO37hkcFny-bKCwwBy7zUdPt28',range = 'Sheet1!A1:D5000000',
                body=body, valueInputOption='USER_ENTERED').execute()

if __name__ == '__main__':


    insert_to_sheet(["papa", "atr"])