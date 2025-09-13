# Customer Support Email Agent

A simple automated customer support system that monitors Gmail accounts and categorizes incoming emails into Questions, Refund requests, or Other emails, then processes them accordingly using Google's Gemini AI.

## Features

- **Gmail Integration**: Connect multiple Gmail accounts
- **AI-Powered Email Categorization**: Uses Google Gemini API for email classification
- **Automated Responses**: 
  - Questions answered via RAG (Retrieval-Augmented Generation)
  - Refund requests processed with order validation
  - Other emails logged with importance assessment
- **PostgreSQL Storage**: Tracks orders, unhandled emails, and processing history

## Tech Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL
- **AI**: Google Gemini API (free tier)
- **Email**: Gmail API
- **Frontend**: Basic HTML templates

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Google Cloud Project with Gmail API enabled
- Google AI Studio account for Gemini API

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd customer-support-email-agent
pip install -r requirements.txt
```

### 2. Google Cloud Setup

#### Enable Gmail API:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client IDs
5. Set application type to "Web application"
6. Add `http://localhost:5000/callback` to authorized redirect URIs
7. Download the credentials JSON file and save as `credentials.json` in project root

#### Get Gemini API Key:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key for your `.env` file

### 3. Database Setup

Create a PostgreSQL database and note the connection details.

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Google API Credentials
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DB_HOST=localhost
DB_NAME=email_agent
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_PORT=5432
```

### 5. Create Templates Directory

```bash
mkdir templates
```

Copy the HTML template from the main code file into `templates/index.html`.

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### 1. Connect Gmail Account
1. Open `http://localhost:5000`
2. Click "Connect Gmail Account"
3. Authorize the application to access your Gmail
4. You'll be redirected back to the main page

### 2. Start Email Processing
1. Click "Start Email Processing" to begin monitoring emails
2. The system checks for new emails every 30 seconds
3. Click "Stop Email Processing" to pause monitoring

### 3. Email Categories and Processing

#### Questions
- Emails asking about products, shipping, returns, etc.
- Answered using simple knowledge base (RAG approach)
- If no answer found → saved as unhandled with high importance

#### Refund Requests
- Emails mentioning refunds or returns
- System looks for order IDs (format: ORD001, ORDER123, etc.)
- **No Order ID**: Asks customer to provide it
- **Valid Order ID**: Marks as refund requested, sends 3-day processing confirmation
- **Invalid Order ID**: Informs customer and logs the attempt

#### Other/Non-sense Emails
- Spam, unrelated content, etc.
- Assessed for importance level (low/medium/high)
- Saved to unhandled emails table

## Database Schema

### Tables Created Automatically:

- **orders**: Sample orders for refund processing
- **unhandled_emails**: High-importance questions and other emails
- **not_found_refunds**: Invalid refund request attempts
- **gmail_accounts**: Connected Gmail account credentials
- **processed_emails**: Prevents duplicate email processing

### Sample Data

The system automatically creates sample orders for testing:
- ORD001 - customer1@example.com - $99.99
- ORD002 - customer2@example.com - $149.50  
- ORD003 - customer3@example.com - $75.00

## Testing the System

### Test Refund Processing:
1. Send an email to your connected Gmail with "I want a refund for ORD001"
2. System should respond with refund confirmation

### Test Question Processing:
1. Send an email asking "What is your shipping policy?"
2. System should respond with shipping information

### Test Invalid Refund:
1. Send an email with "Refund for ORD999" 
2. System should ask for valid order ID

## Project Structure

```
├── app.py                 # Flask web application
├── database.py           # Database models and setup
├── gmail_client.py       # Gmail API integration
├── ai_agent.py          # Gemini AI processing
├── email_processor.py    # Main email processing logic
├── requirements.txt      # Python dependencies
├── .env                 # Environment variables
├── credentials.json     # Google OAuth credentials
└── templates/
    └── index.html       # Web interface
```

## Configuration

### Knowledge Base (RAG)
Edit the `knowledge_base` dictionary in `ai_agent.py` to add your company's FAQ:

```python
self.knowledge_base = {
    "shipping": "Your shipping policy here...",
    "returns": "Your return policy here...",
    # Add more topics
}
```

