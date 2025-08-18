"""
Session management module for conversation history tracking.

This module provides stateful conversation management, maintaining message
history across multiple interactions. It implements a sliding window approach
to keep conversations within token limits while preserving context.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """
    Represents a single message in a conversation.
    
    Messages track both the speaker role and content, forming
    the conversation history that provides context for AI responses.
    
    Attributes:
        role: Speaker identifier ('user' or 'assistant')
        content: The actual message text
    """
    role: str     # Speaker: 'user' for human, 'assistant' for AI
    content: str  # Message text content

class SessionManager:
    """
    Manages conversation sessions with history tracking.
    
    This class provides session-based conversation management, allowing
    multiple concurrent users to maintain separate conversation contexts.
    It implements automatic history pruning to prevent unbounded growth
    while maintaining recent context for coherent conversations.
    
    The sliding window approach keeps the N most recent exchanges,
    balancing context preservation with token efficiency.
    
    Attributes:
        max_history: Maximum number of exchanges to retain
        sessions: Dictionary mapping session IDs to message lists
        session_counter: Auto-incrementing counter for session IDs
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize the session manager.
        
        Args:
            max_history: Number of Q&A exchanges to keep (default 5)
                        Each exchange = 2 messages (user + assistant)
        """
        self.max_history = max_history
        self.sessions: Dict[str, List[Message]] = {}
        self.session_counter = 0  # Simple incrementing ID generator
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Generates a unique session ID and initializes an empty
        message history for the new session.
        
        Returns:
            Unique session identifier string
            
        ID Format:
            "session_{counter}" for easy debugging and tracking
        """
        self.session_counter += 1
        session_id = f"session_{self.session_counter}"
        self.sessions[session_id] = []  # Initialize empty history
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a single message to a session's history.
        
        Automatically creates the session if it doesn't exist.
        Implements sliding window pruning to maintain history limits.
        
        Args:
            session_id: Target session identifier
            role: Message role ('user' or 'assistant')
            content: Message text content
            
        Side Effects:
            - Creates session if not exists
            - Prunes old messages if over limit
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []  # Auto-create session
        
        message = Message(role=role, content=content)
        self.sessions[session_id].append(message)
        
        # Sliding window: keep only recent messages
        # max_history * 2 because each exchange has 2 messages
        if len(self.sessions[session_id]) > self.max_history * 2:
            self.sessions[session_id] = self.sessions[session_id][-self.max_history * 2:]
    
    def add_exchange(self, session_id: str, user_message: str, assistant_message: str):
        """
        Add a complete Q&A exchange to the session.
        
        Convenience method for adding both user query and AI response
        as an atomic operation, ensuring they stay paired.
        
        Args:
            session_id: Target session identifier
            user_message: User's question or request
            assistant_message: AI's response
        """
        self.add_message(session_id, "user", user_message)
        self.add_message(session_id, "assistant", assistant_message)
    
    def get_conversation_history(self, session_id: Optional[str]) -> Optional[str]:
        """
        Retrieve formatted conversation history for AI context.
        
        Formats the message history as a readable conversation transcript
        that can be included in the AI's system prompt for context.
        
        Args:
            session_id: Session to retrieve history for
            
        Returns:
            Formatted conversation string or None if no history
            
        Format:
            User: [message]
            Assistant: [message]
            ...
        """
        if not session_id or session_id not in self.sessions:
            return None  # No session or invalid ID
        
        messages = self.sessions[session_id]
        if not messages:
            return None  # Empty history
        
        # Format for readability in AI context
        formatted_messages = []
        for msg in messages:
            # Capitalize role for display (user -> User)
            formatted_messages.append(f"{msg.role.title()}: {msg.content}")
        
        return "\n".join(formatted_messages)
    
    def clear_session(self, session_id: str):
        """
        Clear all messages from a session.
        
        Resets the conversation history while keeping the session active.
        Useful for "start over" functionality.
        
        Args:
            session_id: Session to clear
            
        Note:
            Session remains in registry with empty history
        """
        if session_id in self.sessions:
            self.sessions[session_id] = []  # Reset to empty list