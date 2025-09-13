import psycopg2
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_id VARCHAR(255) UNIQUE NOT NULL,
                customer_email VARCHAR(255) NOT NULL,
                amount DECIMAL(10, 2),
                status VARCHAR(50) DEFAULT 'completed',
                refund_requested BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Unhandled emails table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unhandled_emails (
                id SERIAL PRIMARY KEY,
                email_id VARCHAR(255) NOT NULL,
                sender_email VARCHAR(255) NOT NULL,
                subject VARCHAR(500),
                body TEXT,
                category VARCHAR(50),
                importance VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Not found refund requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS not_found_refunds (
                id SERIAL PRIMARY KEY,
                email_id VARCHAR(255) NOT NULL,
                sender_email VARCHAR(255) NOT NULL,
                subject VARCHAR(500),
                body TEXT,
                attempted_order_id VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Gmail accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gmail_accounts (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                access_token TEXT,
                refresh_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Email processing history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_emails (
                id SERIAL PRIMARY KEY,
                email_id VARCHAR(255) UNIQUE NOT NULL,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        cursor.close()
        
        # Insert sample orders for testing
        self.insert_sample_data()
    
    def insert_sample_data(self):
        cursor = self.conn.cursor()
        sample_orders = [
            ('ORD001', 'customer1@example.com', 99.99),
            ('ORD002', 'customer2@example.com', 149.50),
            ('ORD003', 'customer3@example.com', 75.00),
        ]
        
        for order_id, email, amount in sample_orders:
            cursor.execute("""
                INSERT INTO orders (order_id, customer_email, amount) 
                VALUES (%s, %s, %s) ON CONFLICT (order_id) DO NOTHING
            """, (order_id, email, amount))
        
        self.conn.commit()
        cursor.close()