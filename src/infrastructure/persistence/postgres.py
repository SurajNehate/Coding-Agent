"""Memory and conversation persistence using PostgreSQL."""
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

Base = declarative_base()


class ConversationSession(Base):
    """Store conversation sessions."""
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    session_metadata = Column(JSON, default={})


class ConversationMessage(Base):
    """Store individual messages in conversations."""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    message_type = Column(String, nullable=False)  # human, ai, system, tool
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryManager:
    """Manage conversation memory with PostgreSQL persistence."""
    
    def __init__(self, db_url: str = None):
        """Initialize memory manager with PostgreSQL."""
        if db_url is None:
            # Default to PostgreSQL, fallback to SQLite for local dev
            db_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/coding_agent"
            )
            # Fallback to SQLite if PostgreSQL not available
            if "postgresql" in db_url and not os.getenv("DATABASE_URL"):
                os.makedirs("data", exist_ok=True)
                db_url = f"sqlite:///data/conversations.db"
        
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def create_session(self, session_id: str, user_id: str, metadata: Optional[Dict] = None) -> ConversationSession:
        """Create a new conversation session."""
        db = self.get_session()
        try:
            session = ConversationSession(
                id=session_id,
                user_id=user_id,
                session_metadata=metadata or {}
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        finally:
            db.close()
    
    def add_message(
        self,
        session_id: str,
        user_id: str,
        message: BaseMessage
    ) -> ConversationMessage:
        """Add a message to the conversation history."""
        db = self.get_session()
        try:
            # Determine message type
            if isinstance(message, HumanMessage):
                msg_type = "human"
            elif isinstance(message, AIMessage):
                msg_type = "ai"
            elif isinstance(message, SystemMessage):
                msg_type = "system"
            elif isinstance(message, ToolMessage):
                msg_type = "tool"
            else:
                msg_type = "unknown"
            
            # Extract metadata
            metadata = {}
            if hasattr(message, 'additional_kwargs'):
                metadata = message.additional_kwargs
            if hasattr(message, 'tool_calls') and message.tool_calls:
                metadata['tool_calls'] = message.tool_calls
            
            db_message = ConversationMessage(
                session_id=session_id,
                user_id=user_id,
                message_type=msg_type,
                content=message.content if hasattr(message, 'content') else str(message),
                message_metadata=metadata
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            return db_message
        finally:
            db.close()
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """Retrieve conversation history for a session."""
        db = self.get_session()
        try:
            query = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.created_at)
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            # Convert to LangChain messages
            langchain_messages = []
            for msg in messages:
                if msg.message_type == "human":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.message_type == "ai":
                    langchain_messages.append(AIMessage(content=msg.content))
                elif msg.message_type == "system":
                    langchain_messages.append(SystemMessage(content=msg.content))
                elif msg.message_type == "tool":
                    langchain_messages.append(ToolMessage(content=msg.content, tool_call_id=msg.message_metadata.get('tool_call_id', '')))
            
            return langchain_messages
        finally:
            db.close()
    
    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[ConversationSession]:
        """Get recent sessions for a user."""
        db = self.get_session()
        try:
            sessions = db.query(ConversationSession).filter(
                ConversationSession.user_id == user_id
            ).order_by(ConversationSession.updated_at.desc()).limit(limit).all()
            return sessions
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a conversation session and its messages."""
        db = self.get_session()
        try:
            # Delete messages
            db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).delete()
            
            # Delete session
            db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).delete()
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting session: {e}")
            return False
        finally:
            db.close()
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session."""
        db = self.get_session()
        try:
            session = db.query(ConversationSession).filter(
                ConversationSession.id == session_id
            ).first()
            
            if not session:
                return {}
            
            message_count = db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session_id
            ).count()
            
            return {
                "session_id": session.id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": message_count,
                "metadata": session.session_metadata
            }
        finally:
            db.close()


# Export singleton instance
memory_manager = MemoryManager()
