from typing import List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        return cls(
            role=MessageRole(data['role']),
            content=data['content'],
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
        )


@dataclass
class Session:
    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    max_history: int = 10
    
    def add_message(self, role: MessageRole, content: str) -> None:
        message = Message(role=role, content=content)
        self.messages.append(message)
        self._trim_history()
        self.updated_at = datetime.now()
    
    def add_exchange(self, user_content: str, assistant_content: str) -> None:
        self.add_message(MessageRole.USER, user_content)
        self.add_message(MessageRole.ASSISTANT, assistant_content)
    
    def _trim_history(self) -> None:
        max_messages = self.max_history * 2
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]
    
    def get_conversation_context(self) -> str:
        if not self.messages:
            return ""
        
        context_lines = []
        for message in self.messages:
            role_display = message.role.value.title()
            context_lines.append(f"{role_display}: {message.content}")
        
        return "\n".join(context_lines)
    
    def clear(self) -> None:
        self.messages.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'max_history': self.max_history
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Session':
        messages = [Message.from_dict(msg_data) for msg_data in data.get('messages', [])]
        return cls(
            session_id=data['session_id'],
            messages=messages,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat())),
            max_history=data.get('max_history', 10)
        )