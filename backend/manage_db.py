#!/usr/bin/env python3
"""
Database Management Utility for RAG System

Usage:
    python manage_db.py           # Load documents (skip existing)
    python manage_db.py --status  # Check database status
    python manage_db.py --clear   # Clear and reload all documents
    python manage_db.py --path /custom/path  # Load from custom path

This utility provides manual control over the ChromaDB database.
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.shared.config import AppConfig
from src.presentation.dependencies import get_dependencies


async def main():
    """
    Main entry point for database management operations.
    
    Provides command-line interface for managing ChromaDB collections,
    loading course documents, and monitoring database status.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
        
    Command-line Arguments:
        --clear: Remove all existing documents before loading
        --status: Display database statistics without modifications
        --path: Custom path to documents directory
        
    Workflow:
        1. Parse command-line arguments
        2. Load and validate configuration
        3. Initialize dependencies and services
        4. Execute requested operation (status/clear/load)
        5. Display results and statistics
    """
    # Configure command-line argument parser
    parser = argparse.ArgumentParser(
        description="Database management utility for RAG system"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing documents before loading"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show database status without loading documents"
    )
    parser.add_argument(
        "--path",
        default="../docs",
        help="Path to documents directory (default: ../docs)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Database Management Utility")
    print("=" * 60)
    
    # Load and validate application configuration
    try:
        config = AppConfig.from_env()
        config.validate()
        print("✓ Configuration loaded")
    except Exception as e:
        # Provide helpful error message for configuration issues
        print(f"✗ Configuration error: {e}")
        print("\nMake sure you have a .env file with ANTHROPIC_API_KEY set")
        return 1
    
    # Initialize dependency injection container and services
    deps = get_dependencies()
    course_service = deps['course_management_service']
    print("✓ System initialized")
    
    # Display current database status without modifications
    if args.status:
        # Retrieve course analytics from vector store
        analytics = await course_service.get_course_analytics()
        print(f"\n📊 Database Status:")
        print(f"   - Total courses: {analytics['total_courses']}")
        
        # List all available courses if any exist
        if analytics['course_titles']:
            print(f"\n📚 Available Courses:")
            for title in analytics['course_titles']:
                print(f"   - {title}")
        else:
            print("\n   No courses loaded yet.")
        return 0
    
    # Validate documents directory exists
    docs_path = Path(args.path)
    if not docs_path.exists():
        print(f"✗ Documents directory not found: {args.path}")
        return 1
    
    # Clear existing data if requested
    if args.clear:
        print("\n⚠️  Clearing existing documents...")
        # Clear both course metadata and content chunk collections
        course_store = deps['course_repository'].vector_store
        content_store = deps['document_repository'].vector_store
        await course_store.clear_collection()
        await content_store.clear_collection()
        print("✓ Database cleared")
    
    print(f"\n📁 Loading documents from {args.path}...")
    
    try:
        # Load documents from specified directory
        # Note: clear_existing=False to preserve existing courses not being reloaded
        courses, chunks = await course_service.add_course_folder(docs_path, clear_existing=False)
        print(f"\n✓ Successfully loaded:")
        print(f"   - {courses} new course(s)")
        print(f"   - {chunks} chunk(s)")
        
        # Display final database statistics after loading
        analytics = await course_service.get_course_analytics()
        print(f"\n📊 Final Database Statistics:")
        print(f"   - Total courses: {analytics['total_courses']}")
        print(f"   - Total lessons: {analytics.get('total_lessons', 0)}")
        
        # List all available courses for verification
        if analytics['course_titles']:
            print(f"\n📚 All Available Courses:")
            for title in analytics['course_titles']:
                print(f"   - {title}")
        
        return 0
        
    except Exception as e:
        # Provide detailed error information for debugging
        print(f"\n✗ Error loading documents: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Execute async main function and exit with appropriate code
    sys.exit(asyncio.run(main()))