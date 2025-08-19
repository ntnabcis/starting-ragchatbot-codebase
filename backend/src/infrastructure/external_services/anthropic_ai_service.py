"""
Anthropic Claude AI service implementation.

Integrates with Anthropic's Claude API for intelligent response generation.
Supports conversation history, context injection, and tool usage.
"""

import anthropic
from typing import List, Optional, Dict, Any
import logging

from ...core.interfaces.service_interfaces import IAIService


logger = logging.getLogger(__name__)


class AnthropicAIService(IAIService):
    """
    Concrete implementation of IAIService using Anthropic's Claude.
    
    Provides AI-powered response generation with context awareness,
    conversation memory, and optional tool usage capabilities.
    
    Key Features:
        - Context-aware responses using provided documents
        - Conversation history tracking for continuity
        - Tool/function calling support for advanced interactions
        - Configurable system prompts for behavior customization
    """
    # Default prompt optimized for educational content delivery
    DEFAULT_SYSTEM_PROMPT = """You are an AI assistant specialized in course materials and educational content.
    Provide clear, concise, and educational responses. Use examples when they aid understanding."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Anthropic AI service.
        
        Args:
            api_key: Anthropic API authentication key
            model: Claude model identifier (defaults to latest sonnet)
            
        Configuration:
            - Temperature set to 0 for consistent, deterministic responses
            - Max tokens limited to 800 for concise answers
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
        self.default_params = {
            "model": self.model,
            "temperature": 0,  # Deterministic responses for educational content
            "max_tokens": 800  # Balance between completeness and conciseness
        }
    
    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate AI response for user query.
        
        Args:
            query: User's question or prompt
            context: Retrieved document context for RAG
            conversation_history: Previous messages for continuity
            tools: Optional tool definitions for function calling
            
        Returns:
            Generated response text
            
        Error Handling:
            Returns user-friendly error message on API failures
            rather than raising exceptions to maintain UX.
            
        Implementation Flow:
            1. Build system prompt with context and history
            2. Construct message array from conversation
            3. Call Claude API with parameters
            4. Handle tool use if requested
            5. Extract and return text response
        """
        try:
            # Combine system prompt with context and history
            system_content = self._build_system_content(context, conversation_history)
            
            # Prepare API call parameters
            api_params = {
                **self.default_params,
                "messages": self._build_messages(query, conversation_history),
                "system": system_content
            }
            
            # Add tool configuration if provided
            if tools:
                api_params["tools"] = tools
                api_params["tool_choice"] = {"type": "auto"}
            
            # Make API call to Claude
            response = self.client.messages.create(**api_params)
            
            # Handle tool use responses
            if response.stop_reason == "tool_use" and tools:
                return await self._handle_tool_use(response, api_params)
            
            # Extract text from response
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            # Return graceful error message instead of crashing
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        Update system prompt for AI behavior customization.
        
        Args:
            prompt: New system instructions for Claude
            
        Use Cases:
            - Adjust expertise level for different audiences
            - Change response style (formal/informal)
            - Add domain-specific instructions
        """
        self.system_prompt = prompt
    
    def _build_system_content(
        self, 
        context: Optional[str], 
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """
        Construct complete system prompt with context.
        
        Args:
            context: Retrieved document chunks for RAG
            conversation_history: Previous conversation messages
            
        Returns:
            Combined system prompt with all relevant information
            
        Structure:
            1. Base system prompt (behavior instructions)
            2. Context section (retrieved documents)
            3. Conversation history (for continuity)
        """
        parts = [self.system_prompt]
        
        # Add retrieved context if available
        if context:
            parts.append(f"\nContext:\n{context}")
        
        # Add conversation history for continuity
        if conversation_history:
            history_text = self._format_conversation_history(conversation_history)
            if history_text:
                parts.append(f"\nPrevious conversation:\n{history_text}")
        
        return "\n".join(parts)
    
    def _build_messages(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """
        Build message array for Claude API.
        
        Args:
            query: Current user question
            conversation_history: Previous messages
            
        Returns:
            Formatted messages for API call
            
        Limits:
            Only includes last 6 messages to manage context window
            and API costs while maintaining conversation flow.
        """
        messages = []
        
        # Include recent conversation history (last 6 messages)
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
    
    def _format_conversation_history(
        self, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Format conversation history for system prompt.
        
        Args:
            conversation_history: List of message dictionaries
            
        Returns:
            Formatted string representation of conversation
            
        Format:
            Role: content format for readability
            Limited to last 6 messages for context management
        """
        if not conversation_history:
            return ""
        
        formatted = []
        # Format recent messages for context
        for msg in conversation_history[-6:]:
            role = msg.get("role", "user").title()
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    async def _handle_tool_use(
        self, 
        initial_response: Any, 
        base_params: Dict[str, Any]
    ) -> str:
        """
        Handle tool use requests from Claude.
        
        Args:
            initial_response: Response with tool_use stop reason
            base_params: Original API parameters for potential retry
            
        Returns:
            Text response or tool execution result
            
        Current Implementation:
            Logs warning and returns any text content.
            Full tool execution would require tool result handling.
            
        Future Enhancement:
            Implement tool execution and result injection for
            advanced search and computation capabilities.
        """
        logger.warning("Tool use requested but tool execution not implemented in this context")
        
        # Extract any text content from response
        if initial_response.content:
            for block in initial_response.content:
                if hasattr(block, 'text'):
                    return block.text
        
        return "I need additional tools to answer this question properly."