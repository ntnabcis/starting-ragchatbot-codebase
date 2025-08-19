"""
Course management API endpoints.

Provides REST API routes for retrieving course statistics and metadata.
Integrates with the analytics use case to aggregate course information.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from ...application.use_cases import GetAnalyticsUseCase


class CourseStats(BaseModel):
    """
    Response model for course statistics endpoint.
    
    Attributes:
        total_courses: Number of courses in the system
        course_titles: List of all available course names
    """
    total_courses: int
    course_titles: List[str]


# Initialize router with API prefix and OpenAPI tags
course_router = APIRouter(prefix="/api", tags=["courses"])


def get_analytics_use_case() -> GetAnalyticsUseCase:
    """
    Dependency injection function for analytics use case.
    
    Returns:
        GetAnalyticsUseCase: Configured analytics use case instance
        
    Note:
        Lazy import prevents circular dependencies during module loading.
    """
    from ..dependencies import get_dependencies
    deps = get_dependencies()
    return deps['analytics_use_case']


@course_router.get("/courses", response_model=CourseStats)
async def get_course_stats(
    use_case: GetAnalyticsUseCase = Depends(get_analytics_use_case)
):
    """
    Retrieve aggregated course statistics.
    
    Args:
        use_case: Injected analytics use case for data retrieval
        
    Returns:
        CourseStats: Statistics including course count and titles
        
    Raises:
        HTTPException: 500 status on analytics retrieval failure
        
    API Usage:
        GET /api/courses
        Returns JSON with total_courses and course_titles array
    """
    try:
        # Execute analytics use case to gather course data
        response = await use_case.execute()
        
        # Handle use case errors gracefully
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        # Transform use case response to API response model
        return CourseStats(
            total_courses=response.total_courses,
            course_titles=response.course_titles
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Wrap unexpected errors in 500 response
        raise HTTPException(status_code=500, detail=str(e))