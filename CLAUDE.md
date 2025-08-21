# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Retrieval-Augmented Generation (RAG) system for course materials, built with:
- **Backend**: FastAPI + ChromaDB for vector storage + Anthropic Claude for AI generation
- **Frontend**: Vanilla HTML/JS/CSS served by FastAPI with dark/light theme support
- **Python Environment**: Uses `uv` package manager (not pip/poetry)

## Essential Commands

### Running the Application
```bash
# Quick start (recommended)
./run.sh

# Manual start
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Installing Dependencies
```bash
# Install/sync dependencies (uses pyproject.toml)
uv sync

# Add new dependencies
uv add <package_name>
```

## Architecture

### Core RAG Pipeline
The system follows this flow:
1. **Document Processing** (`backend/document_processor.py`): Parses course documents into structured Course objects with Lessons, then chunks content
2. **Vector Storage** (`backend/vector_store.py`): Stores document chunks in ChromaDB with embeddings using sentence-transformers
3. **Search Tools** (`backend/search_tools.py`): Implements tool-based search that the AI can invoke to find relevant course content
4. **AI Generation** (`backend/ai_generator.py`): Uses Anthropic Claude with tool calling to search and generate responses
5. **Session Management** (`backend/session_manager.py`): Maintains conversation history per session

### Key Design Patterns
- **Tool-Based Search**: The AI uses structured tool calls to search the vector database rather than direct context injection
- **Course-Aware Chunking**: Documents are parsed to extract course structure (title, lessons) before chunking
- **Dual Collections**: ChromaDB maintains separate collections for course metadata and content chunks

### API Structure
- Main app entry: `backend/app.py` (FastAPI application)
- Static frontend served from `/frontend` directory
- Key endpoints:
  - `POST /api/query`: Process user queries with RAG
  - `GET /api/courses`: Get course catalog statistics

### Frontend Architecture
- **Theme System** (`frontend/theme.js`): Manages dark/light mode with localStorage persistence and system preference detection
- **Main Application** (`frontend/script.js`): Handles chat interactions and API communication
- **Styling** (`frontend/style.css`): CSS variables-based theming for easy customization

## Environment Setup

Required environment variable in `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

## Development Notes

- No test suite currently exists
- No linting/formatting tools configured
- Frontend files are served with no-cache headers in development
- ChromaDB data persists in `backend/chroma_db/` (gitignored)
- Documents are loaded from `docs/` folder on startup
- Theme preference stored in localStorage key `theme-preference`
- CSS uses custom properties for theming - all colors should use var() references