"""
FastAPI router for handling User operations.

This module contains endpoints for creating, retrieving, updating, and deleting users.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/check")


@router.get("/")
async def liveness():
    """
    Checks liveness

    Returns:
        dict: Successful or Unsuccessful message.
    """

    return {"message": "Success"}
