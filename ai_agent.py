import google.generativeai as genai
import os
import re
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Any

class AIAgent:
    def __init__(self, db):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.db = db
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Create or get knowledge base collection
        self.knowledge_collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize knowledge base
        self.setup_knowledge_base()
    
    def setup_knowledge_base(self):
        """Initialize the vector knowledge base with company information"""
        
        # Check if collection is already populated
        if self.knowledge_collection.count() > 0:
            print("Knowledge base already initialized")
            return
        
        # Company knowledge documents
        knowledge_docs = [
            {
                "id": "shipping_001",
                "content": "We offer free shipping on all orders over $50. Standard shipping takes 3-5 business days within the continental US. Express shipping is available for $15 and takes 1-2 business days. International shipping is available to most countries and takes 7-14 business days.",
                "category": "shipping",
                "metadata": {"topic": "shipping_policy", "priority": "high"}
            },
            {
                "id": "shipping_002", 
                "content": "You can track your order using the tracking number provided in your shipping confirmation email. Visit our website and enter your tracking number in the order status page.",
                "category": "shipping",
                "metadata": {"topic": "tracking", "priority": "medium"}
            },
            {
                "id": "returns_001",
                "content": "We accept returns within 30 days of purchase for a full refund. Items must be in original condition with tags attached. Return shipping is free for defective items, otherwise customer pays return shipping costs.",
                "category": "returns", 
                "metadata": {"topic": "return_policy", "priority": "high"}
            },
            {
                "id": "returns_002",
                "content": "To initiate a return, log into your account and select the order you want to return. You can also contact customer service with your order number. We'll provide a prepaid return label for defective items.",
                "category": "returns",
                "metadata": {"topic": "return_process", "priority": "high"}
            },
            {
                "id": "warranty_001",
                "content": "All our products come with a 1-year manufacturer warranty covering defects in materials and workmanship. Electronics have a 2-year warranty. Warranty does not cover normal wear and tear or damage from misuse.",
                "category": "warranty",
                "metadata": {"topic": "warranty_terms", "priority": "medium"}
            },
            {
                "id": "payment_001",
                "content": "We accept all major credit cards (Visa, MasterCard, American Express, Discover), PayPal, Apple Pay, Google Pay, and bank transfers. All payments are processed securely using SSL encryption.",
                "category": "payment",
                "metadata": {"topic": "payment_methods", "priority": "medium"}
            },
            {
                "id": "payment_002",
                "content": "If your payment fails, please check that your card details are correct and you have sufficient funds. Contact your bank if the issue persists. You can also try a different payment method.",
                "category": "payment", 
                "metadata": {"topic": "payment_issues", "priority": "medium"}
            },
            {
                "id": "support_001",
                "content": "Our customer support team is available Monday through Friday, 9 AM to 5 PM EST. You can reach us via email at support@company.com or phone at 1-800-555-0123. Live chat is available on our website during business hours.",
                "category": "support",
                "metadata": {"topic": "contact_info", "priority": "high"}
            },
            {
                "id": "products_001",
                "content": "We offer a wide range of high-quality products including electronics, home goods, clothing, and accessories. All products go through rigorous quality testing before shipping.",
                "category": "products",
                "metadata": {"topic": "product_info", "priority": "low"}
            },
            {
                "id": "account_001",
                "content": "You can create an account on our website to track orders, save favorites, and speed up checkout. Account creation is free and your information is kept secure and private.",
                "category": "account",
                "metadata": {"topic": "account_management", "priority": "medium"}
            }
        ]
        
        # Generate embeddings and store in ChromaDB
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for doc in knowledge_docs:
            # Generate embedding for the content
            embedding = self.embedding_model.encode(doc["content"]).tolist()
            
            documents.append(doc["content"])
            embeddings.append(embedding)
            ids.append(doc["id"])
            metadatas.append({
                "category": doc["category"],
                **doc["metadata"]
            })
        
        # Add to ChromaDB collection
        self.knowledge_collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"Knowledge base initialized with {len(knowledge_docs)} documents")
    
    def semantic_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search in ChromaDB
        results = self.knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        search_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                search_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
        
        return search_results
    
    def generate_rag_response(self, question: str, context_docs: List[Dict[str, Any]]) -> str:
        """Generate response using RAG with Gemini"""
        
        if not context_docs:
            return None
        
        # Prepare context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1}: {doc['content']}" 
            for i, doc in enumerate(context_docs)
        ])
        
        # Create RAG prompt
        prompt = f"""You are a helpful customer support agent. Answer the customer's question using only the information provided in the context below. If the context doesn't contain enough information to answer the question completely, say so politely.

Context Information:
{context}

Customer Question: {question}

Instructions:
- Provide a helpful, professional response
- Use only information from the context
- If you cannot answer fully with the given context, politely explain what information is missing
- Keep the tone friendly and supportive
- Format the response as a proper customer service email

Response:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating RAG response: {e}")
            return None
    
    def categorize_email(self, subject, body):
        prompt = f"""
        Categorize this customer support email into exactly one category: QUESTION, REFUND, or OTHER
        
        Subject: {subject}
        Body: {body}
        
        Category Definitions:
        - QUESTION: Customer is asking for information about:
          * Products, services, features
          * Shipping, delivery, tracking
          * Returns, exchanges, warranties  
          * Payment methods, billing, accounts
          * How to do something or get help
          * Policies, procedures, terms
          * Technical support or troubleshooting
          * Any legitimate customer inquiry
        
        - REFUND: Customer is specifically requesting:
          * Money back, refund, reimbursement
          * Cancel order and get refund
          * Return product for money back
          
        - OTHER: Only for:
          * Spam, promotional, marketing emails
          * Completely unrelated to business
          * Nonsense or gibberish content
          * Automated/bot messages
        
        Examples:
        - "What credit cards do you accept?" → QUESTION
        - "How long does shipping take?" → QUESTION  
        - "Can I return this item?" → QUESTION
        - "I want a refund for order 123" → REFUND
        - "Please refund my money" → REFUND
        - "Buy cheap pills online" → OTHER
        
        Important: When in doubt between QUESTION and OTHER, choose QUESTION for legitimate customer inquiries.
        
        Response format: Only return the category name (QUESTION, REFUND, or OTHER).
        """
        
        try:
            response = self.model.generate_content(prompt)
            category = response.text.strip().upper()
            
            # Debug logging
            print(f"DEBUG - Categorization result: '{category}' for email: '{subject}'")
            
            # Validate and return category
            if category in ['QUESTION', 'REFUND', 'OTHER']:
                return category
            else:
                print(f"DEBUG - Invalid category '{category}', defaulting to QUESTION")
                return 'QUESTION'  # Default to QUESTION instead of OTHER
        except Exception as e:
            print(f"DEBUG - Categorization error: {e}, defaulting to QUESTION")
            return 'QUESTION'  # Default to QUESTION for errors
    
    def process_question(self, subject, body, sender, email_id, account):
        """Enhanced question processing with RAG"""
        
        # Combine subject and body for better context
        full_question = f"{subject} {body}".strip()
        
        print(f"Processing question with RAG: {subject}")
        
        # Step 1: Semantic search to find relevant documents
        relevant_docs = self.semantic_search(full_question, top_k=3)
        
        # Filter by similarity threshold (0.3 is fairly permissive)
        high_relevance_docs = [
            doc for doc in relevant_docs 
            if doc['similarity_score'] > 0.3
        ]
        
        print(f"Found {len(high_relevance_docs)} relevant documents")
        for doc in high_relevance_docs:
            print(f"- Similarity: {doc['similarity_score']:.3f}, Category: {doc['metadata']['category']}")
        
        if high_relevance_docs:
            # Step 2: Generate RAG response using Gemini
            response = self.generate_rag_response(full_question, high_relevance_docs)
            
            if response:
                # Format as customer service email
                formatted_response = f""" 
{response}"""
                
                return formatted_response
        
        # No relevant information found - save as unhandled
        print("No relevant information found, saving as unhandled")
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO unhandled_emails (email_id, sender_email, subject, body, category, importance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email_id, sender, subject, body, 'QUESTION', 'high'))
        self.db.conn.commit()
        cursor.close()
        
        return None
    
    def add_knowledge_document(self, content: str, category: str, metadata: Dict[str, Any] = None):
        """Add a new document to the knowledge base"""
        
        doc_id = f"{category}_{self.knowledge_collection.count() + 1:03d}"
        embedding = self.embedding_model.encode(content).tolist()
        
        doc_metadata = {"category": category}
        if metadata:
            doc_metadata.update(metadata)
        
        self.knowledge_collection.add(
            documents=[content],
            embeddings=[embedding], 
            ids=[doc_id],
            metadatas=[doc_metadata]
        )
        
        print(f"Added new knowledge document: {doc_id}")
    
    def process_refund(self, subject, body, sender, email_id, account):
        # Extract order ID from email
        order_pattern = r'\b(ORD\d+|ORDER\d+|\d{6,})\b'
        matches = re.findall(order_pattern, body.upper())
        
        if not matches:
            # Ask for order ID
            response = """Hello,

Thank you for contacting us regarding your refund request. 

To process your refund, please provide your order ID (e.g., ORD001).

Best regards,
Customer Support"""
            return response
        
        order_id = matches[0]
        
        # Check if order exists
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, refund_requested FROM orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()
        
        if result:
            # Order found
            cursor.execute(
                "UPDATE orders SET refund_requested = TRUE WHERE order_id = %s",
                (order_id,)
            )
            self.db.conn.commit()
            cursor.close()
            
            response = f"""Hello,

Your refund request for order {order_id} has been received and approved.

The refund will be processed within 3 business days and will appear on your original payment method.

Best regards,
Customer Support"""
            return response
        else:
            # Order not found - check if this is a repeat invalid ID
            cursor.execute("""
                SELECT COUNT(*) FROM not_found_refunds 
                WHERE sender_email = %s AND attempted_order_id = %s
            """, (sender, order_id))
            
            count = cursor.fetchone()[0]
            
            # Log the invalid request
            cursor.execute("""
                INSERT INTO not_found_refunds (email_id, sender_email, subject, body, attempted_order_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (email_id, sender, subject, body, order_id))
            
            self.db.conn.commit()
            cursor.close()
            
            response = f"""Hello,

We could not find order {order_id} in our system. Please double-check your order ID and try again.

You can find your order ID in your purchase confirmation email.

Best regards,
Customer Support"""
            return response
    
    def process_other(self, subject, body, sender, email_id, account):
        # Assess importance level using Gemini
        prompt = f"""
        Rate the importance of this email as: low, medium, high
        
        Subject: {subject}
        Body: {body}
        
        Consider:
        - Urgent complaints or issues: high
        - General inquiries that seem legitimate: medium  
        - Spam, nonsense, or clearly unrelated: low
        - Angry or frustrated customers: high
        - Technical issues or problems: high
        
        Respond with only the importance level.
        """
        
        try:
            response = self.model.generate_content(prompt)
            importance = response.text.strip().lower()
            importance = importance if importance in ['low', 'medium', 'high'] else 'low'
        except:
            importance = 'low'
        
        # Save to unhandled emails
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO unhandled_emails (email_id, sender_email, subject, body, category, importance)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email_id, sender, subject, body, 'OTHER', importance))
        self.db.conn.commit()
        cursor.close()
        
        return None  # No auto-reply for OTHER category