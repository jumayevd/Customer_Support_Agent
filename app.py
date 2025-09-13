from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import os

# Import our modules
from database import Database
from gmail_client import GmailClient
from ai_agent import AIAgent
from email_processor import EmailProcessor

load_dotenv()

app = Flask(__name__)

# Initialize components
db = Database()
gmail_client = GmailClient(db)
ai_agent = AIAgent(db)
email_processor = EmailProcessor(db, gmail_client, ai_agent)

# Load existing accounts on startup
gmail_client.load_accounts()

@app.route('/')
def index():
    cursor = db.conn.cursor()
    cursor.execute("SELECT email FROM gmail_accounts")
    accounts = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return render_template('index.html', accounts=accounts)

@app.route('/connect')
def connect():
    auth_url = gmail_client.get_auth_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        try:
            email = gmail_client.handle_callback(code)
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error: {e}"
    return "Authorization failed"

@app.route('/disconnect/<email>')
def disconnect(email):
    gmail_client.disconnect_account(email)
    return redirect(url_for('index'))

@app.route('/start-processing')
def start_processing():
    email_processor.start_processing()
    return jsonify({"status": "started"})

@app.route('/stop-processing')
def stop_processing():
    email_processor.stop_processing()
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)