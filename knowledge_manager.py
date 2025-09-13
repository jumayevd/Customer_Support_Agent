#!/usr/bin/env python3
"""
Knowledge Base Management Tool
Allows you to manage the ChromaDB vector knowledge base
"""

import os
from dotenv import load_dotenv
from database import Database  
from ai_agent import AIAgent

load_dotenv()

class KnowledgeManager:
    def __init__(self):
        self.db = Database()
        self.ai_agent = AIAgent(self.db)
    
    def test_search(self, query: str):
        """Test semantic search functionality"""
        print(f"\nTesting search for: '{query}'")
        print("=" * 50)
        
        results = self.ai_agent.semantic_search(query, top_k=5)
        
        if not results:
            print("No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity: {result['similarity_score']:.3f}")
            print(f"   Category: {result['metadata']['category']}")
            print(f"   Content: {result['content'][:100]}...")
    
    def test_rag_response(self, question: str):
        """Test full RAG response generation"""
        print(f"\nTesting RAG response for: '{question}'")
        print("=" * 50)
        
        # Get relevant documents
        docs = self.ai_agent.semantic_search(question, top_k=3)
        relevant_docs = [doc for doc in docs if doc['similarity_score'] > 0.3]
        
        if not relevant_docs:
            print("No relevant documents found.")
            return
        
        print(f"Found {len(relevant_docs)} relevant documents:")
        for doc in relevant_docs:
            print(f"- {doc['metadata']['category']} (similarity: {doc['similarity_score']:.3f})")
        
        # Generate response
        response = self.ai_agent.generate_rag_response(question, relevant_docs)
        print(f"\nGenerated Response:\n{response}")
    
    def add_document(self, content: str, category: str, topic: str = "", priority: str = "medium"):
        """Add a new document to the knowledge base"""
        metadata = {
            "topic": topic,
            "priority": priority
        }
        
        self.ai_agent.add_knowledge_document(content, category, metadata)
        print(f"Added document to category: {category}")
    
    def view_collection_stats(self):
        """View statistics about the knowledge base"""
        count = self.ai_agent.knowledge_collection.count()
        print(f"\nKnowledge Base Statistics:")
        print(f"Total documents: {count}")
        
        # Get all documents to analyze categories
        if count > 0:
            all_docs = self.ai_agent.knowledge_collection.get(include=["metadatas"])
            categories = {}
            
            for metadata in all_docs['metadatas']:
                category = metadata['category']
                categories[category] = categories.get(category, 0) + 1
            
            print("\nDocuments by category:")
            for category, count in sorted(categories.items()):
                print(f"  {category}: {count}")
    
    def interactive_mode(self):
        """Interactive mode for testing and management"""
        print("Knowledge Base Manager - Interactive Mode")
        print("Commands: search, rag, add, stats, quit")
        
        while True:
            command = input("\n> ").strip().lower()
            
            if command == 'quit' or command == 'q':
                break
            elif command == 'search':
                query = input("Enter search query: ")
                self.test_search(query)
            elif command == 'rag':
                question = input("Enter question: ")
                self.test_rag_response(question)
            elif command == 'add':
                content = input("Enter document content: ")
                category = input("Enter category: ")
                topic = input("Enter topic (optional): ")
                self.add_document(content, category, topic)
            elif command == 'stats':
                self.view_collection_stats()
            else:
                print("Unknown command. Available: search, rag, add, stats, quit")

def main():
    manager = KnowledgeManager()
    
    # Show initial stats
    manager.view_collection_stats()
    
    # Run some test searches
    test_queries = [
        "How long does shipping take?",
        "Can I return an item?", 
        "What payment methods do you accept?",
        "My order is damaged",
        "How do I contact support?"
    ]
    
    print("\n" + "="*60)
    print("TESTING SEMANTIC SEARCH")
    print("="*60)
    
    for query in test_queries:
        manager.test_search(query)
    
    print("\n" + "="*60) 
    print("TESTING RAG RESPONSES")
    print("="*60)
    
    rag_questions = [
        "How long does shipping take and how much does it cost?",
        "I want to return a product, what's the process?",
        "My payment failed, what should I do?"
    ]
    
    for question in rag_questions:
        manager.test_rag_response(question)
    
    # Start interactive mode
    print("\n" + "="*60)
    manager.interactive_mode()

if __name__ == "__main__":
    main()