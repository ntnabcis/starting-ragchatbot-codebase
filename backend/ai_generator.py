"""
AI generation module for Claude-powered response synthesis.

This module manages the interaction with Anthropic's Claude API, implementing
the "generation" component of the RAG system. It supports tool-based search,
conversation history, and optimized prompt engineering for educational content.
"""

import anthropic
from typing import List, Optional, Dict, Any


class AIGenerator:
    """
    Manages AI response generation using Claude with tool support.
    
    This class encapsulates the complexity of interacting with Claude's API,
    including tool calling, conversation context management, and response
    optimization. It implements a two-phase approach where Claude can
    optionally use tools before generating the final response.
    
    The system prompt is carefully crafted to guide Claude's behavior
    for educational content, emphasizing accuracy, brevity, and proper
    tool usage.
    
    Attributes:
        client: Anthropic API client instance
        model: Specific Claude model version to use
        base_params: Pre-configured API parameters for consistency
    """
    
    # System prompt optimized for educational content and tool usage
    # Static to avoid reconstruction overhead on each request
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to a comprehensive search tool for course information.

Search Tool Usage:
- Use the search tool **only** for questions about specific course content or detailed educational materials
- **One search per query maximum**
- Synthesize search results into accurate, fact-based responses
- If search yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without searching
- **Course-specific questions**: Search first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, search explanations, or question-type analysis
 - Do not mention "based on the search results"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the AI generator with API credentials.
        
        Args:
            api_key: Anthropic API key for authentication
            model: Model identifier (e.g., 'claude-3-haiku')
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        
        # Pre-configure common parameters for performance
        # Temperature=0 for deterministic, factual responses
        # Token limit balances response completeness with cost
        self.base_params = {
            "model": self.model,
            "temperature": 0,  # Deterministic for educational accuracy
            "max_tokens": 800  # Sufficient for detailed explanations
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate an AI response with optional tool usage.
        
        This method implements the core RAG generation logic:
        1. Prepare context with conversation history
        2. Allow Claude to optionally use tools for search
        3. Generate final response based on tool results
        
        The two-phase approach (tool use + final response) ensures
        Claude can gather information before formulating an answer.
        
        Args:
            query: User's question or request
            conversation_history: Formatted previous conversation
            tools: List of tool definitions for Claude to use
            tool_manager: ToolManager instance for executing tools
            
        Returns:
            Generated response text
            
        Performance:
            - Cached base parameters avoid reconstruction
            - Efficient string concatenation for context
            - Single API call for non-tool responses
        """
        
        # Construct system prompt with optional conversation context
        # Using conditional expression for efficiency
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Build API request with efficient parameter spreading
        api_params = {
            **self.base_params,  # Reuse pre-configured settings
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Enable tool usage if tools are provided
        # "auto" lets Claude decide whether to use tools
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}  # Claude decides
        
        # Make initial API call to Claude
        response = self.client.messages.create(**api_params)
        
        # Check if Claude wants to use tools
        # stop_reason="tool_use" indicates tool invocation request
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager)
        
        # No tools used - return direct response
        return response.content[0].text
    
    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager):
        """
        Process tool execution and generate final response.
        
        This method implements the tool execution phase:
        1. Extract tool calls from Claude's response
        2. Execute each tool through the manager
        3. Send results back to Claude for final response
        
        The conversation flow maintains context by preserving
        the message history through both API calls.
        
        Args:
            initial_response: Claude's response requesting tool use
            base_params: Original API parameters for context
            tool_manager: ToolManager for executing tools
            
        Returns:
            Final response incorporating tool results
            
        Message Flow:
            User Query -> Claude (with tools) -> Tool Execution ->
            Tool Results -> Claude (without tools) -> Final Response
        """
        # Build conversation history including tool usage
        messages = base_params["messages"].copy()  # Preserve original query
        
        # Add Claude's tool invocation to conversation
        messages.append({"role": "assistant", "content": initial_response.content})
        
        # Process each tool invocation request
        tool_results = []
        for content_block in initial_response.content:
            if content_block.type == "tool_use":
                # Execute tool with provided parameters
                tool_result = tool_manager.execute_tool(
                    content_block.name, 
                    **content_block.input
                )
                
                # Format result for Claude's expected structure
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": content_block.id,  # Links result to request
                    "content": tool_result
                })
        
        # Send tool results back to Claude
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        
        # Prepare final request without tools
        # Claude now has search results and generates final answer
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": base_params["system"]  # Maintain same context
        }
        
        # Get final synthesized response
        final_response = self.client.messages.create(**final_params)
        return final_response.content[0].text