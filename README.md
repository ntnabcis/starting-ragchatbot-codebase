# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

> **✨ Clean Architecture**: This codebase implements modular, clean architecture with SOLID principles. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.12 or higher
- uv (Python package manager) - [Installation guide](https://docs.astral.sh/uv/)
- An Anthropic API key (for Claude AI) - [Get API key](https://console.anthropic.com/)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the `backend` directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

### Database Management

Manage the ChromaDB vector database with the utility script:
```bash
cd backend
python manage_db.py                  # Load documents (skip existing)
python manage_db.py --status        # Check database status
python manage_db.py --clear         # Clear and reload all documents
python manage_db.py --path ../docs  # Load from specific directory
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

## Features

- **Semantic Search**: Find relevant course content using natural language queries
- **Context-Aware Responses**: AI generates answers using retrieved course materials
- **Session Management**: Maintains conversation history for contextual follow-ups
- **Clean Architecture**: Modular design with clear separation of concerns
- **Resource Optimization**: Efficient document processing and memory management

## Project Structure

```
.
├── backend/              # Backend application
│   ├── app.py           # Application entry point
│   ├── manage_db.py     # Database management utility
│   └── src/             # Clean architecture modules
├── frontend/            # Static web interface
├── docs/                # Course materials (*.txt files)
├── ARCHITECTURE.md      # Detailed architecture documentation
└── CLAUDE.md           # Claude Code instructions
```

## API Endpoints

- `POST /api/query` - Process user queries with RAG
- `GET /api/courses` - Get course statistics
- `GET /api/health` - Health check endpoint

## Document Format

Course documents in the `docs/` directory should follow this format:
```
Course Title: [Title]
Course Link: [URL] (optional)
Course Instructor: [Name] (optional)

Lesson 0: [Title]
Lesson Link: [URL] (optional)
[Content...]

Lesson 1: [Title]
[Content...]
```

## Troubleshooting

### Common Issues

1. **High CPU/Memory during document loading**
   - Documents are processed sequentially to prevent spikes
   - Use `manage_db.py` for manual control

2. **"Failed to load courses" error**
   - Check `.env` file exists in `backend/` with valid API key
   - Verify `docs/` directory contains `.txt` files
   - Run `python manage_db.py --status` to check database

3. **Import errors**
   - Ensure you're using Python 3.12+
   - Run `uv sync` to install all dependencies

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md)

