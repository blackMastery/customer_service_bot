"""
Knowledge Base Builder
This script processes documents and creates a vector store for RAG.
"""
import os
from pathlib import Path
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    CSVLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from config import get_settings


class KnowledgeBaseBuilder:
    """Build and manage knowledge base for the chatbot."""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.embeddings_model,
            api_key=self.settings.openai_api_key
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def load_documents(self, directory: str) -> List:
        """Load documents from a directory."""
        documents = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return documents
        
        # Supported file types and their loaders
        loaders = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.csv': CSVLoader,
            '.md': UnstructuredMarkdownLoader,
        }
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                extension = file_path.suffix.lower()
                
                if extension in loaders:
                    try:
                        logger.info(f"Loading: {file_path}")
                        loader_class = loaders[extension]
                        loader = loader_class(str(file_path))
                        docs = loader.load()
                        
                        # Add metadata
                        for doc in docs:
                            doc.metadata['source'] = str(file_path)
                            doc.metadata['file_type'] = extension
                        
                        documents.extend(docs)
                        logger.info(f"Loaded {len(docs)} documents from {file_path.name}")
                        
                    except Exception as e:
                        logger.error(f"Error loading {file_path}: {e}")
        
        return documents
    
    def build_vector_store(
        self,
        documents_dir: str = None,
        output_dir: str = None
    ):
        """Build vector store from documents."""
        docs_dir = documents_dir or self.settings.knowledge_base_path
        out_dir = output_dir or self.settings.vector_store_path
        
        # Create directories if they don't exist
        Path(docs_dir).mkdir(parents=True, exist_ok=True)
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Loading documents from: {docs_dir}")
        documents = self.load_documents(docs_dir)
        
        if not documents:
            logger.warning("No documents found. Creating sample document...")
            self._create_sample_documents(docs_dir)
            documents = self.load_documents(docs_dir)
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # Split documents
        logger.info("Splitting documents into chunks...")
        splits = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(splits)} chunks")
        
        # Create vector store
        logger.info("Creating vector store...")
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=out_dir
        )
        
        logger.info(f"Vector store created successfully at: {out_dir}")
        return vectorstore
    
    def _create_sample_documents(self, directory: str):
        """Create sample documents for testing."""
        sample_content = {
            "company_info.txt": """
Company Name: Your Company
Founded: 2020
Mission: To provide excellent customer service and innovative solutions.
            
Business Hours: Monday-Friday, 9 AM - 5 PM EST
Support Email: support@yourcompany.com
Phone: 1-800-555-0123
            
We are committed to helping our customers succeed.
""",
            "shipping_policy.txt": """
Shipping Policy
            
Standard Shipping: 5-7 business days
Express Shipping: 2-3 business days
Overnight Shipping: Next business day
            
Free shipping on orders over $50.
            
We ship to all 50 states and internationally to select countries.
Tracking information is provided once your order ships.
""",
            "return_policy.txt": """
Return Policy
            
We offer a 30-day return policy on most items.
            
To be eligible for a return:
- Item must be unused and in original packaging
- Must have receipt or proof of purchase
- Return must be initiated within 30 days of purchase
            
Refunds are processed within 5-7 business days.
            
Some items are non-returnable:
- Perishable goods
- Custom or personalized items
- Digital products
""",
            "faq.txt": """
Frequently Asked Questions
            
Q: How do I track my order?
A: You can track your order using the tracking number sent to your email.
            
Q: What payment methods do you accept?
A: We accept Visa, MasterCard, American Express, PayPal, and Apple Pay.
            
Q: Do you offer international shipping?
A: Yes, we ship to select countries. Additional fees may apply.
            
Q: How do I change or cancel my order?
A: Contact customer support within 24 hours of placing your order.
            
Q: What is your warranty policy?
A: Most products come with a 1-year manufacturer warranty.
"""
        }
        
        directory_path = Path(directory)
        for filename, content in sample_content.items():
            file_path = directory_path / filename
            file_path.write_text(content.strip())
            logger.info(f"Created sample document: {filename}")
    
    def update_vector_store(
        self,
        new_documents_dir: str,
        existing_store_dir: str = None
    ):
        """Add new documents to existing vector store."""
        store_dir = existing_store_dir or self.settings.vector_store_path
        
        # Load new documents
        new_docs = self.load_documents(new_documents_dir)
        if not new_docs:
            logger.warning("No new documents found")
            return
        
        # Split documents
        splits = self.text_splitter.split_documents(new_docs)
        
        # Load existing store and add documents
        vectorstore = Chroma(
            persist_directory=store_dir,
            embedding_function=self.embeddings
        )
        
        vectorstore.add_documents(splits)
        logger.info(f"Added {len(splits)} new chunks to vector store")
    
    def search_knowledge_base(self, query: str, k: int = 3):
        """Search the knowledge base."""
        vectorstore = Chroma(
            persist_directory=self.settings.vector_store_path,
            embedding_function=self.embeddings
        )
        
        results = vectorstore.similarity_search(query, k=k)
        
        logger.info(f"Search results for '{query}':")
        for i, doc in enumerate(results, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Content: {doc.page_content[:200]}...")
            logger.info(f"Source: {doc.metadata.get('source', 'Unknown')}")
        
        return results


def main():
    """CLI for knowledge base management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage knowledge base")
    parser.add_argument(
        "action",
        choices=["build", "update", "search"],
        help="Action to perform"
    )
    parser.add_argument(
        "--docs-dir",
        default="./data/knowledge_base",
        help="Directory containing documents"
    )
    parser.add_argument(
        "--output-dir",
        default="./data/vectorstore",
        help="Output directory for vector store"
    )
    parser.add_argument(
        "--query",
        help="Search query (for search action)"
    )
    
    args = parser.parse_args()
    
    builder = KnowledgeBaseBuilder()
    
    if args.action == "build":
        logger.info("Building knowledge base...")
        builder.build_vector_store(args.docs_dir, args.output_dir)
        logger.info("Knowledge base built successfully!")
        
    elif args.action == "update":
        logger.info("Updating knowledge base...")
        builder.update_vector_store(args.docs_dir, args.output_dir)
        logger.info("Knowledge base updated successfully!")
        
    elif args.action == "search":
        if not args.query:
            logger.error("--query is required for search action")
            return
        logger.info(f"Searching for: {args.query}")
        builder.search_knowledge_base(args.query)


if __name__ == "__main__":
    main()
