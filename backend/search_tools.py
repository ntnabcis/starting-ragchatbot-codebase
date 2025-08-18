"""
Tool-based search architecture for extensible AI capabilities.

This module implements the tool abstraction pattern that enables the AI
to autonomously decide when and how to search for information. It provides
a framework for registering multiple tools and a concrete implementation
for course content search with intelligent filtering.
"""

from typing import Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
from vector_store import VectorStore, SearchResults


class Tool(ABC):
    """
    Abstract base class defining the tool interface.
    
    Tools represent capabilities that the AI can invoke autonomously.
    Each tool must provide its definition (for the AI to understand)
    and an execution method (to perform the action).
    
    This abstraction enables adding new capabilities without modifying
    the core AI generation logic.
    """
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Provide the tool's definition in Anthropic's format.
        
        Returns:
            Dictionary containing:
            - name: Tool identifier
            - description: What the tool does
            - input_schema: JSON schema for parameters
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        Execute the tool's functionality.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            String result for the AI to process
        """
        pass


class CourseSearchTool(Tool):
    """
    Concrete tool implementation for searching course materials.
    
    This tool provides semantic search capabilities with intelligent
    filtering by course name and lesson number. It maintains source
    tracking for UI attribution and supports fuzzy course name matching.
    
    The tool's parameters are designed to be intuitive for the AI,
    allowing natural language course references to be resolved to
    exact matches in the database.
    
    Attributes:
        store: VectorStore instance for search operations
        last_sources: Cached sources from most recent search
    """
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize the search tool with a vector store.
        
        Args:
            vector_store: Configured VectorStore for search operations
        """
        self.store = vector_store
        self.last_sources = []  # Cache for UI source attribution
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Define the tool's interface for AI understanding.
        
        The definition includes parameter descriptions that guide
        the AI in how to use the tool effectively. The descriptions
        emphasize that partial course names are supported.
        
        Returns:
            Anthropic-compatible tool definition dictionary
        """
        return {
            "name": "search_course_content",
            "description": "Search course materials with smart course name matching and lesson filtering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "What to search for in the course content"
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course title (partial matches work, e.g. 'MCP', 'Introduction')"
                    },
                    "lesson_number": {
                        "type": "integer",
                        "description": "Specific lesson number to search within (e.g. 1, 2, 3)"
                    }
                },
                "required": ["query"]  # Only query is mandatory
            }
        }
    
    def execute(self, query: str, course_name: Optional[str] = None, lesson_number: Optional[int] = None) -> str:
        """
        Perform semantic search with optional filtering.
        
        This method coordinates with the vector store to:
        1. Resolve partial course names to exact matches
        2. Apply metadata filters
        3. Format results for AI consumption
        
        Args:
            query: Semantic search query
            course_name: Optional course filter (supports partial matches)
            lesson_number: Optional lesson number filter
            
        Returns:
            Formatted search results with context headers
            Error message if search fails
            
        Side Effects:
            Updates last_sources for UI attribution
        """
        
        # Delegate to vector store for actual search
        results = self.store.search(
            query=query,
            course_name=course_name,
            lesson_number=lesson_number
        )
        
        # Return error message directly for AI to handle
        if results.error:
            return results.error
        
        # Construct informative message for empty results
        # This helps the AI understand the search scope
        if results.is_empty():
            filter_info = ""
            if course_name:
                filter_info += f" in course '{course_name}'"
            if lesson_number:
                filter_info += f" in lesson {lesson_number}"
            return f"No relevant content found{filter_info}."
        
        # Format and return results
        return self._format_results(results)
    
    def _format_results(self, results: SearchResults) -> str:
        """
        Format search results for AI consumption.
        
        Adds contextual headers to each result showing the course
        and lesson information. This context helps the AI understand
        where each piece of information comes from.
        
        Args:
            results: SearchResults from vector store
            
        Returns:
            Formatted string with context headers and content
            
        Format:
            [Course Title - Lesson N]
            Content text...
        """
        formatted = []
        sources = []  # Build source list for UI attribution
        
        for doc, meta in zip(results.documents, results.metadata):
            course_title = meta.get('course_title', 'unknown')
            lesson_num = meta.get('lesson_number')
            
            # Create informative header for each result
            header = f"[{course_title}"
            if lesson_num is not None:
                header += f" - Lesson {lesson_num}"
            header += "]"
            
            # Build source string for UI display
            source = course_title
            if lesson_num is not None:
                source += f" - Lesson {lesson_num}"
            sources.append(source)
            
            formatted.append(f"{header}\n{doc}")
        
        # Cache sources for UI to retrieve after response generation
        self.last_sources = sources
        
        return "\n\n".join(formatted)

class ToolManager:
    """
    Central registry and executor for AI tools.
    
    This class manages the collection of available tools, providing
    a unified interface for tool registration, discovery, and execution.
    It acts as the bridge between the AI generator and individual tools.
    
    The manager pattern allows for dynamic tool registration and
    future extensibility without modifying existing code.
    
    Attributes:
        tools: Dictionary mapping tool names to Tool instances
    """
    
    def __init__(self):
        """
        Initialize an empty tool registry.
        """
        self.tools = {}
    
    def register_tool(self, tool: Tool):
        """
        Register a new tool with the manager.
        
        Tools are registered by their name as defined in their
        tool definition. This name is used by the AI to invoke
        the tool during execution.
        
        Args:
            tool: Tool instance implementing the Tool interface
            
        Raises:
            ValueError: If tool doesn't provide a name
        """
        tool_def = tool.get_tool_definition()
        tool_name = tool_def.get("name")
        if not tool_name:
            raise ValueError("Tool must have a 'name' in its definition")
        self.tools[tool_name] = tool

    
    def get_tool_definitions(self) -> list:
        """
        Collect all tool definitions for AI configuration.
        
        Returns:
            List of tool definition dictionaries
            
        Used By:
            AI generator when preparing tool-enabled requests
        """
        return [tool.get_tool_definition() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """
        Execute a registered tool by name.
        
        This method is called by the AI generator when the AI
        decides to use a tool. It handles tool lookup and
        parameter passing.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result or error message
        """
        if tool_name not in self.tools:
            return f"Tool '{tool_name}' not found"
        
        return self.tools[tool_name].execute(**kwargs)
    
    def get_last_sources(self) -> list:
        """
        Retrieve source attributions from the most recent search.
        
        Searches all registered tools for cached source information.
        This is used by the RAG system to provide source citations
        in the UI alongside AI responses.
        
        Returns:
            List of source strings or empty list
            
        Design Note:
            This approach allows multiple tools to track sources
            without tight coupling to specific tool types.
        """
        # Scan all tools for source tracking capability
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources') and tool.last_sources:
                return tool.last_sources
        return []

    def reset_sources(self):
        """
        Clear cached sources from all tools.
        
        Called between queries to ensure source attributions
        don't carry over between unrelated searches.
        """
        for tool in self.tools.values():
            if hasattr(tool, 'last_sources'):
                tool.last_sources = []