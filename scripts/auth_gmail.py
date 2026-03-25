import os
import sys

# Ensure Sentinal_Lee is in the python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_dir)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from config import DATA_DIR

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    token_path = os.path.join(DATA_DIR, 'token.json')
    credentials_path = os.path.join(DATA_DIR, 'credentials.json')

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired. Refreshing...")
            creds.refresh(Request())
        else:
            print(f"Loading credentials from {credentials_path}...")
            if not os.path.exists(credentials_path):
                print(f"Error: Credentials file not found at {credentials_path}")
                print("Please download it from the Google Cloud Console and save it there.")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            print(f"Saving newly generated token to {token_path}...")
            token.write(creds.to_json())
            
    print("Authentication successful! You can now use Gmail tools.")
    return True

if __name__ == '__main__':
    authenticate_gmail()
