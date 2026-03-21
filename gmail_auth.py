"""Gmail API Authentication Module"""
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailAuth:
    def __init__(self, credentials_file=None):
        """Initialize with credentials file path"""
        # Try multiple possible credential file names
        if credentials_file and os.path.exists(credentials_file):
            self.credentials_path = credentials_file
        elif os.path.exists('cred.json'):
            self.credentials_path = 'cred.json'
        elif os.path.exists('credentials.json'):
            self.credentials_path = 'credentials.json'
        else:
            raise FileNotFoundError(
                "Gmail credentials file not found. "
                "Please ensure 'cred.json' or 'credentials.json' exists."
            )
        
        self.service = None
        print(f"📁 Using credentials file: {self.credentials_path}")
        
    def authenticate(self):
        """Authenticate and return Gmail service"""
        creds = None
        
        # Token file stores user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def get_service(self):
        """Get authenticated Gmail service"""
        if not self.service:
            self.authenticate()
        return self.service
