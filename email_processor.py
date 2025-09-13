import time
import threading

class EmailProcessor:
    def __init__(self, db, gmail_client, ai_agent):
        self.db = db
        self.gmail_client = gmail_client
        self.ai_agent = ai_agent
        self.running = False
    
    def start_processing(self):
        self.running = True
        thread = threading.Thread(target=self._process_loop)
        thread.daemon = True
        thread.start()
        print("Email processing started...")
    
    def stop_processing(self):
        self.running = False
        print("Email processing stopped...")
    
    def _process_loop(self):
        while self.running:
            try:
                # Check all connected accounts
                for email in self.gmail_client.services.keys():
                    new_emails = self.gmail_client.get_new_emails(email)
                    
                    for email_data in new_emails:
                        self.process_email(email_data)
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                print(f"Error in processing loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def process_email(self, email_data):
        print(f"Processing email: {email_data['subject']}")
        print(f"DEBUG - Email body received:\n{email_data['body']}")
        
        # Categorize email
        category = self.ai_agent.categorize_email(
            email_data['subject'], 
            email_data['body']
        )
        
        print(f"Category: {category}")
        
        # Process based on category
        response = None
        if category == 'QUESTION':
            print("DEBUG - Processing as QUESTION with RAG")
            response = self.ai_agent.process_question(
                email_data['subject'],
                email_data['body'],
                email_data['sender'],
                email_data['id'],
                email_data['account']
            )
        elif category == 'REFUND':
            print("DEBUG - Processing as REFUND")
            response = self.ai_agent.process_refund(
                email_data['subject'],
                email_data['body'],
                email_data['sender'],
                email_data['id'],
                email_data['account']
            )
        else:  # OTHER
            print("DEBUG - Processing as OTHER (no auto-reply)")
            self.ai_agent.process_other(
                email_data['subject'],
                email_data['body'],
                email_data['sender'],
                email_data['id'],
                email_data['account']
            )
        
        # Send response if generated
        if response:
            print(f"DEBUG - Generated response:\n{response[:200]}...")
            success = self.gmail_client.send_reply(
                email_data['sender'],
                email_data['subject'],
                response,
                email_data['account']
            )
            print(f"Response sent: {success}")
        else:
            print("DEBUG - No response generated")