"""RAG (Retrieval Augmented Generation) system with Qdrant."""
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_huggingface import HuggingFaceEmbeddings


class RAGSystem:
    """RAG system for document retrieval using Qdrant vector database (Docker)."""
    
    def __init__(
        self,
        collection_name: str = "coding_agent_docs",
        persist_directory: str = None  # Deprecated
    ):
        """Initialize RAG system with Qdrant."""
        self.collection_name = collection_name
        
        # Initialize embeddings
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

        # Initialize Qdrant Client (Strict Docker Mode)
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")

        try:
            self.client = QdrantClient(url=qdrant_url, api_key=api_key)
            print(f"✅ Connected to Qdrant at {qdrant_url}")

            # Ensure collection exists
            if not self.client.collection_exists(self.collection_name):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # miniLM-L6-v2 dimension
                        distance=models.Distance.COSINE
                    )
                )

            # Initialize LangChain Wrapper
            self.vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embeddings,
            )
            
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant at {qdrant_url}: {e}")
            print("To fix this, ensure Docker is running: `docker-compose up -d`")
            self.vector_store = None
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def load_documents_from_directory(
        self,
        directory: str,
        file_types: List[str] = [".txt", ".pdf", ".md"]
    ) -> List[Document]:
        """Load documents from a directory."""
        documents = []
        
        for file_type in file_types:
            glob_pattern = f"**/*{file_type}"
            if file_type == ".pdf":
                loader = DirectoryLoader(
                    directory,
                    glob=glob_pattern,
                    loader_cls=PyPDFLoader
                )
            else:
                loader = DirectoryLoader(
                    directory,
                    glob=glob_pattern,
                    loader_cls=TextLoader
                )
            
            try:
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"Error loading {file_type} files: {e}")
        
        return documents
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        if not self.vector_store:
            print("Vector store not available. Is Qdrant running?")
            return []
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        if not chunks:
            return []

        # Add to vector store
        try:
            ids = self.vector_store.add_documents(chunks)
            print(f"✅ Added {len(chunks)} document chunks to Qdrant")
            return ids
        except Exception as e:
            print(f"Error adding documents to Qdrant: {e}")
            return []
    
    def add_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a single text to the vector store."""
        if not self.vector_store:
            return ""
        
        doc = Document(page_content=text, metadata=metadata or {})
        ids = self.add_documents([doc])
        return ids[0] if ids else ""
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for relevant documents."""
        if not self.vector_store:
            return []
        
        try:
            return self.vector_store.similarity_search(query, k=k, filter=filter)
        except Exception as e:
            print(f"Error searching Qdrant: {e}")
            return []

    def get_context_for_query(
        self,
        query: str,
        k: int = 3,
        max_chars: int = 2000
    ) -> str:
        """Get formatted context for a query."""
        results = self.search(query, k=k)
        
        context_parts = []
        total_chars = 0
        
        for doc in results:
            content = doc.page_content
            if total_chars + len(content) > max_chars:
                # Truncate to fit
                remaining = max_chars - total_chars
                content = content[:remaining] + "..."
                context_parts.append(content)
                break
            
            context_parts.append(content)
            total_chars += len(content)
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the index."""
        if not self.vector_store or not self.client:
            return {"status": "unavailable"}
            
        try:
            count = self.client.count(self.collection_name).count
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "status": "available",
                "type": "qdrant-docker"
            }
        except Exception as e:
             return {
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e)
            }


# Export singleton instance
rag_system = RAGSystem()
