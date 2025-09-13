import base64
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

class GmailClient:
    SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify"
    ]

    def __init__(self, db):
        self.db = db
        self.services = {}  # email -> service mapping
    
    def get_auth_url(self):
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=self.SCOPES,
            redirect_uri='http://localhost:5000/callback'
        )

        flow.oauth2session.scope = self.SCOPES
        flow.oauth2session.params['access_type'] = 'offline'
        flow.oauth2session.params['prompt'] = 'consent'


        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url
    
    def handle_callback(self, code):
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=self.SCOPES,
            redirect_uri='http://localhost:5000/callback'
        )
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get user email
        profile = service.users().getProfile(userId='me').execute()
        email = profile['emailAddress']
        
        # Store credentials in database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO gmail_accounts (email, access_token, refresh_token) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (email) DO UPDATE SET 
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token
        """, (email, credentials.token, credentials.refresh_token))
        self.db.conn.commit()
        cursor.close()
        
        self.services[email] = service
        return email
    
    def load_accounts(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT email, access_token, refresh_token FROM gmail_accounts")
        accounts = cursor.fetchall()
        cursor.close()
        
        for email, access_token, refresh_token in accounts:
            try:
                credentials = Credentials(
                    token=access_token,
                    refresh_token=refresh_token,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=os.getenv('GOOGLE_CLIENT_ID'),
                    client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
                )
                service = build('gmail', 'v1', credentials=credentials)
                self.services[email] = service
            except Exception as e:
                print(f"Failed to load account {email}: {e}")
    
    def disconnect_account(self, email):
        cursor = self.db.conn.cursor()
        cursor.execute("DELETE FROM gmail_accounts WHERE email = %s", (email,))
        self.db.conn.commit()
        cursor.close()
        
        if email in self.services:
            del self.services[email]
    
    def get_new_emails(self, email):
        if email not in self.services:
            return []
        
        service = self.services[email]
        
        # Get list of messages
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])
        
        new_emails = []
        cursor = self.db.conn.cursor()
        
        for message in messages:
            msg_id = message['id']
            
            # Check if already processed
            cursor.execute("SELECT id FROM processed_emails WHERE email_id = %s", (msg_id,))
            if cursor.fetchone():
                continue
            
            # Get full message
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            
            # Extract email data
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            # Get body
            body = self.extract_body(msg['payload'])
            
            new_emails.append({
                'id': msg_id,
                'subject': subject,
                'sender': sender,
                'body': body,
                'account': email
            })
            
            # Mark as processed
            cursor.execute(
                "INSERT INTO processed_emails (email_id) VALUES (%s)",
                (msg_id,)
            )
        
        self.db.conn.commit()
        cursor.close()
        return new_emails
    
    def extract_body(self, payload):
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
        return body
    
    def send_reply(self, to_email, subject, body, account_email):
        if account_email not in self.services:
            return False
        
        service = self.services[account_email]
        
        message = f"""To: {to_email}
Subject: Re: {subject}

{body}
"""
        encoded_message = base64.urlsafe_b64encode(message.encode()).decode()
        
        try:
            service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False