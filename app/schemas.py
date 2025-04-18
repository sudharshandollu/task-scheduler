from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any


# FastAPI models
class TaskCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    priority: int = Field(..., ge=1, le=10, description="Priority from 1 (lowest) to 10 (highest)")
    burst_time: float = Field(..., gt=0, le=300, description="Execution time in seconds (max 5 minutes)")

    class Config:
        schema_extra = {
            "example": {
                "name": "Database Backup",
                "description": "Backup the user database",
                "priority": 5,
                "burst_time": 10.5
            }
        }


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    priority: Optional[int] = Field(None, ge=1, le=10, description="Priority from 1 (lowest) to 10 (highest)")
    burst_time: Optional[float] = Field(None, gt=0, le=300, description="Execution time in seconds (max 5 minutes)")

    @validator('*')
    def check_at_least_one_field(cls, v, values):
        if not any(values.values()) and v is None:
            raise ValueError("At least one field must be provided for update")
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Database Backup",
                "priority": 7
            }
        }


class TaskResponse(BaseModel):
    task_id: str
    name: str
    description: str
    priority: int
    burst_time: float
    created_at: float
    remaining_time: float
    status: str
    progress: int
    response_time: float = None
    waiting_time: float = None
    turnaround_time: float = None
    completion_time: float = None

    class Config:
        schema_extra = {
            "example": {
                "task_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Database Backup",
                "description": "Backup the user database",
                "priority": 5,
                "burst_time": 10.5,
                "created_at": 1650123456.789,
                "remaining_time": 8.3,
                "status": "running",
                "progress": 20,
                "response_time": 1.2,
                "waiting_time": None,
                "turnaround_time": None,
                "completion_time": None
            }
        }


class SchedulerStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    scheduler_uptime: float
    idle: bool
