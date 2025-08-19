# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.


## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
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
   
   Create a `.env` file in the root directory:
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

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Testing

### Running Tests

Use the provided test script for various testing options:

```bash
# Run all tests
./run_tests.sh

# Run with verbose output
./run_tests.sh -v

# Run with coverage report
./run_tests.sh -c

# Run with HTML coverage report
./run_tests.sh -ch

# Run specific test file
./run_tests.sh -t test_document_processor.py

# Run specific test class
./run_tests.sh -t TestChunkText

# Quick test run (minimal output)
./run_tests.sh -q

# Full test suite with all reports
./run_tests.sh -a
```

### Manual Test Execution

If you prefer to run tests manually:

```bash
cd backend
uv run pytest tests/                          # Run all tests
uv run pytest tests/ -v                       # Verbose output
uv run pytest tests/ --cov=. --cov-report=term-missing  # With coverage
```

