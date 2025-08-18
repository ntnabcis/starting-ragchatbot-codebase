# RAG System Architecture Diagrams

## 1. High-Level System Overview

This diagram shows the complete system architecture with all major components and their interactions.

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web Interface<br/>HTML/JS/CSS]
    end
    
    subgraph "API Layer"
        API[FastAPI Server<br/>app.py]
        CORS[CORS Middleware]
        STATIC[Static File Server]
    end
    
    subgraph "Core RAG System"
        RAG[RAG System<br/>Orchestrator]
        SM[Session Manager<br/>Conversation History]
        TM[Tool Manager<br/>Tool Registry]
    end
    
    subgraph "Processing Components"
        DP[Document Processor<br/>Chunking & Parsing]
        AG[AI Generator<br/>Claude Integration]
        ST[Search Tools<br/>CourseSearchTool]
    end
    
    subgraph "Storage Layer"
        VS[(Vector Store<br/>ChromaDB)]
        ENV[(.env<br/>API Keys)]
        DOCS[(Course Documents<br/>*.txt files)]
    end
    
    subgraph "External Services"
        CLAUDE[Anthropic Claude API]
        EMBED[Sentence Transformers<br/>Embedding Model]
    end
    
    UI -->|HTTP Requests| API
    API --> CORS
    API --> STATIC
    API -->|/query, /stats, /initialize| RAG
    
    RAG --> SM
    RAG --> TM
    RAG --> DP
    RAG --> AG
    RAG --> VS
    
    TM --> ST
    ST --> VS
    
    AG -->|API Calls| CLAUDE
    AG -->|Tool Execution| TM
    
    DP --> DOCS
    DP -->|Chunks| VS
    
    VS -->|Embeddings| EMBED
    
    API --> ENV
    AG --> ENV
    
    style UI fill:#e1f5fe
    style API fill:#fff3e0
    style RAG fill:#f3e5f5
    style VS fill:#e8f5e9
    style CLAUDE fill:#fce4ec
    style EMBED fill:#fce4ec
```

## 2. Component Interaction Flow

This diagram shows the detailed flow of a user query through the system.

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant FastAPI
    participant RAGSystem
    participant SessionMgr
    participant AIGenerator
    participant ToolManager
    participant SearchTool
    participant VectorStore
    participant Claude
    
    User->>Frontend: Enter query
    Frontend->>FastAPI: POST /query
    FastAPI->>RAGSystem: query(text, session_id)
    
    RAGSystem->>SessionMgr: get_conversation_history()
    SessionMgr-->>RAGSystem: history (if exists)
    
    RAGSystem->>AIGenerator: generate_response()
    Note over AIGenerator: Prepares tools & context
    
    AIGenerator->>Claude: API call with tools
    Claude-->>AIGenerator: Response (may request tool)
    
    alt Tool Use Requested
        AIGenerator->>ToolManager: execute_tool()
        ToolManager->>SearchTool: execute(query, filters)
        SearchTool->>VectorStore: search()
        Note over VectorStore: Semantic search<br/>with embeddings
        VectorStore-->>SearchTool: Search results
        SearchTool-->>ToolManager: Formatted results
        ToolManager-->>AIGenerator: Tool output
        AIGenerator->>Claude: Continue with tool results
        Claude-->>AIGenerator: Final response
    end
    
    AIGenerator-->>RAGSystem: Response text
    RAGSystem->>SessionMgr: add_exchange()
    RAGSystem->>ToolManager: get_last_sources()
    RAGSystem-->>FastAPI: (answer, sources)
    FastAPI-->>Frontend: JSON response
    Frontend-->>User: Display answer
```

## 3. RAG Subsystem Architecture

This diagram details the internal structure of the RAG system and its core components.

```mermaid
graph LR
    subgraph "RAG System Core"
        direction TB
        INIT[Initialization]
        QUERY[Query Handler]
        DOC_ADD[Document Adder]
        STATS[Statistics]
    end
    
    subgraph "Document Processing Pipeline"
        direction LR
        FILE[Course File<br/>*.txt]
        PARSER[Text Parser]
        CHUNKER[Chunker<br/>Size: 1500<br/>Overlap: 200]
        META[Metadata<br/>Extractor]
        COURSE[Course Object]
        CHUNKS[CourseChunk<br/>Objects]
    end
    
    subgraph "Vector Store Operations"
        direction TB
        COLL_META[(metadata<br/>Collection)]
        COLL_CONTENT[(content<br/>Collection)]
        EMBED_MODEL[all-MiniLM-L6-v2<br/>Embedding Model]
    end
    
    INIT --> DOC_ADD
    DOC_ADD --> FILE
    FILE --> PARSER
    PARSER --> CHUNKER
    PARSER --> META
    CHUNKER --> CHUNKS
    META --> COURSE
    
    COURSE --> COLL_META
    CHUNKS --> COLL_CONTENT
    COLL_META --> EMBED_MODEL
    COLL_CONTENT --> EMBED_MODEL
    
    QUERY --> COLL_META
    QUERY --> COLL_CONTENT
    
    STATS --> COLL_META
    STATS --> COLL_CONTENT
    
    style INIT fill:#e3f2fd
    style QUERY fill:#e3f2fd
    style DOC_ADD fill:#e3f2fd
    style STATS fill:#e3f2fd
    style COLL_META fill:#c8e6c9
    style COLL_CONTENT fill:#c8e6c9
    style EMBED_MODEL fill:#ffccbc
```

## 4. Query Processing Data Flow

This diagram shows how data flows through the system during query processing.

```mermaid
flowchart TB
    START([User Query])
    SESSION{Session<br/>Exists?}
    CREATE_SESSION[Create New<br/>Session]
    GET_HISTORY[Retrieve<br/>Conversation History]
    
    PREPARE[Prepare Query<br/>with Context]
    
    AI_DECISION{AI Decides:<br/>Need Search?}
    
    GENERAL[Generate from<br/>Knowledge Base]
    
    SEARCH_PARAMS[Extract Search<br/>Parameters]
    SEMANTIC[Semantic Search<br/>in ChromaDB]
    
    FILTER{Apply<br/>Filters?}
    COURSE_FILTER[Filter by<br/>Course Name]
    LESSON_FILTER[Filter by<br/>Lesson Number]
    
    RESULTS[Format Search<br/>Results]
    
    GENERATE[Generate Response<br/>with Context]
    
    SAVE[Save to<br/>Session History]
    
    RESPONSE([Return Answer<br/>+ Sources])
    
    START --> SESSION
    SESSION -->|No| CREATE_SESSION
    SESSION -->|Yes| GET_HISTORY
    CREATE_SESSION --> PREPARE
    GET_HISTORY --> PREPARE
    
    PREPARE --> AI_DECISION
    
    AI_DECISION -->|No Search| GENERAL
    AI_DECISION -->|Use Tool| SEARCH_PARAMS
    
    SEARCH_PARAMS --> SEMANTIC
    SEMANTIC --> FILTER
    
    FILTER -->|Yes| COURSE_FILTER
    FILTER -->|Yes| LESSON_FILTER
    FILTER -->|No| RESULTS
    
    COURSE_FILTER --> RESULTS
    LESSON_FILTER --> RESULTS
    
    RESULTS --> GENERATE
    GENERAL --> SAVE
    GENERATE --> SAVE
    
    SAVE --> RESPONSE
    
    style START fill:#e1f5fe
    style RESPONSE fill:#c8e6c9
    style AI_DECISION fill:#fff9c4
    style SEMANTIC fill:#ffccbc
```

## 5. Tool-Based Search Architecture

This diagram shows the tool abstraction layer and how it enables extensible search capabilities.

```mermaid
classDiagram
    class Tool {
        <<abstract>>
        +get_tool_definition() Dict
        +execute(**kwargs) str
    }
    
    class CourseSearchTool {
        -store: VectorStore
        -last_sources: List
        +get_tool_definition() Dict
        +execute(query, course_name, lesson_number) str
        -format_results(results) str
    }
    
    class ToolManager {
        -tools: Dict[str, Tool]
        +register_tool(tool)
        +get_tool_definitions() List
        +execute_tool(name, **kwargs) str
        +get_last_sources() List
        +reset_sources()
    }
    
    class VectorStore {
        -client: ChromaDB
        -metadata_collection: Collection
        -content_collection: Collection
        -embedding_function: SentenceTransformer
        +search(query, course_name, lesson_number) SearchResults
        +add_course_metadata(course)
        +add_course_content(chunks)
        +get_existing_course_titles() List
    }
    
    class SearchResults {
        +documents: List[str]
        +metadata: List[Dict]
        +error: Optional[str]
        +is_empty() bool
    }
    
    class AIGenerator {
        -client: Anthropic
        -model: str
        +generate_response(query, history, tools, tool_manager) str
        -handle_tool_execution(response, params, tool_manager) str
    }
    
    Tool <|-- CourseSearchTool : implements
    ToolManager --> Tool : manages
    ToolManager --> CourseSearchTool : registers
    CourseSearchTool --> VectorStore : uses
    VectorStore --> SearchResults : returns
    AIGenerator --> ToolManager : calls tools
    
    note for CourseSearchTool "Semantic search with\nintelligent filtering"
    note for ToolManager "Extensible tool registry\nfor future capabilities"
    note for AIGenerator "Decides when to use tools\nbased on query type"
```

## 6. Deployment Architecture

This diagram shows the deployment structure and runtime environment.

```mermaid
graph TB
    subgraph PythonEnv[Python Environment]
        UV[UV Package Manager]
        VENV[Virtual Environment]
        DEPS[Dependencies<br/>FastAPI, ChromaDB,<br/>Anthropic, etc.]
    end
    
    subgraph AppProcess[Application Process]
        UVICORN[Uvicorn ASGI Server<br/>Port 8000]
        WORKERS[Worker Processes<br/>--reload enabled]
    end
    
    subgraph FileSystem[File System]
        BACKEND[backend/]
        FRONTEND[frontend/]
        DOCS_DIR[docs/]
        CHROMA[chroma_data/]
    end
    
    subgraph ExtDeps[External Dependencies]
        ANTHROPIC_API[Anthropic API<br/>claude-3-5-haiku]
        HUGGING[HuggingFace Models<br/>sentence-transformers]
    end
    
    subgraph ClientAccess[Client Access]
        BROWSER[Web Browser<br/>http://localhost:8000]
        API_DOCS[Swagger UI<br/>http://localhost:8000/docs]
    end
    
    UV --> VENV
    VENV --> DEPS
    DEPS --> UVICORN
    UVICORN --> WORKERS
    
    WORKERS --> BACKEND
    WORKERS --> FRONTEND
    BACKEND --> DOCS_DIR
    BACKEND --> CHROMA
    
    BACKEND -.->|API Calls| ANTHROPIC_API
    BACKEND -.->|Model Download| HUGGING
    
    BROWSER --> UVICORN
    API_DOCS --> UVICORN
    
    style UVICORN fill:#fff3e0
    style ANTHROPIC_API fill:#fce4ec
    style BROWSER fill:#e1f5fe
```

## 7. Data Model Relationships

This diagram shows the data structures and their relationships.

```mermaid
erDiagram
    Course {
        string id PK
        string title
        string description
        int total_lessons
        list topics
        string difficulty
    }
    
    Lesson {
        int number PK
        string title
        string content
        list topics
    }
    
    CourseChunk {
        string id PK
        string course_id FK
        string course_title
        int lesson_number FK
        string lesson_title
        string content
        int chunk_index
        dict metadata
    }
    
    Message {
        string role
        string content
    }
    
    Session {
        string session_id PK
        list messages
        datetime created_at
    }
    
    QueryRequest {
        string query
        string session_id FK
    }
    
    QueryResponse {
        string answer
        list sources
        string session_id FK
    }
    
    Course ||--o{ Lesson : contains
    Course ||--o{ CourseChunk : generates
    Lesson ||--o{ CourseChunk : chunked_into
    Session ||--o{ Message : stores
    QueryRequest }o--|| Session : references
    QueryResponse }o--|| Session : references
```

## Notes on Architecture

### Scaling Considerations
- **Vector Store**: ChromaDB can be replaced with production vector databases (Pinecone, Weaviate) for scaling
- **Session Management**: Currently in-memory, should use Redis/database for production
- **API Rate Limiting**: Anthropic API has rate limits - implement queuing for production
- **Embedding Cache**: Consider caching embeddings to reduce computation

### Fault Tolerance
- **Graceful Degradation**: System can answer general questions if vector search fails
- **Session Isolation**: Each session is independent, preventing cascade failures
- **Error Handling**: All components have try-catch blocks with fallback responses

### Dependencies
- **Critical**: Anthropic API key (required for AI generation)
- **Important**: ChromaDB for vector storage (can be swapped)
- **Flexible**: Sentence-transformers model (can use different models)

### Security Considerations
- API keys stored in `.env` file (not in code)
- CORS configured for controlled access
- Input validation on all endpoints
- No direct file system access from frontend