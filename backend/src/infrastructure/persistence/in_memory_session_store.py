from typing import Dict, List, Optional
import uuid
from datetime import datetime

from ...core.interfaces.repository_interfaces import ISessionRepository, SessionData
from ...domain.entities import Session, MessageRole


class InMemorySessionStore(ISessionRepository):
    def __init__(self, max_history: int = 10):
        self.sessions: Dict[str, Session] = {}
        self.max_history = max_history
    
    async def create_session(self) -> str:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.sessions[session_id] = Session(
            session_id=session_id,
            max_history=self.max_history
        )
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return SessionData(
            session_id=session_id,
            messages=[msg.to_dict() for msg in session.messages]
        )
    
    async def save_message(self, session_id: str, role: str, content: str) -> bool:
        if session_id not in self.sessions:
            self.sessions[session_id] = Session(
                session_id=session_id,
                max_history=self.max_history
            )
        
        try:
            role_enum = MessageRole(role.lower())
            self.sessions[session_id].add_message(role_enum, content)
            return True
        except ValueError:
            return False
    
    async def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        session = self.sessions.get(session_id)
        if not session:
            return []
        
        messages = session.messages[-limit:] if limit > 0 else session.messages
        return [msg.to_dict() for msg in messages]
    
    async def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            return True
        return False