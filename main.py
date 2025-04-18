# main.py - FastAPI application entry point
from fastapi import FastAPI, HTTPException, BackgroundTasks, status, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uvicorn

import uuid
from datetime import datetime
from app.task_scheduler import TaskScheduler
from app.logger import logger
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, SchedulerStats
from app.task import Task






# Create FastAPI app
app = FastAPI(
    title="Task Scheduler API",
    description="REST API for a priority-based round-robin task scheduler",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create scheduler instance and start it
scheduler = TaskScheduler(time_quantum=2.0)

# Dependency to ensure scheduler is running
def get_scheduler():
    if not scheduler.running:
        scheduler.start()
    return scheduler


@app.on_event("startup")
def startup_event():
    """Start the scheduler when the API starts"""
    scheduler.start()
    logger.info("FastAPI application started")


@app.on_event("shutdown")
def shutdown_event():
    """Stop the scheduler when the API shuts down"""
    scheduler.stop()
    logger.info("FastAPI application shutdown")


@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """API root"""
    return {
        "message": "Task Scheduler API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }


@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate, scheduler: TaskScheduler = Depends(get_scheduler)):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    task = Task(
        task_id=task_id,
        name=task_data.name,
        description=task_data.description,
        priority=task_data.priority,
        burst_time=task_data.burst_time
    )
    task = scheduler.add_task(task)
    return task.to_dict()


@app.get("/tasks/", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None, enum=["pending", "running", "completed"]),
    priority: Optional[int] = Query(None, ge=1, le=10),
    scheduler: TaskScheduler = Depends(get_scheduler)
):
    """List all tasks with optional filtering"""
    tasks = scheduler.get_all_tasks()
    
    # Apply filters
    if status:
        tasks = [t for t in tasks if t.status == status]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    
    return [t.to_dict() for t in tasks]


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, scheduler: TaskScheduler = Depends(get_scheduler)):
    """Get a specific task by ID"""
    task = scheduler.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_data: TaskUpdate, scheduler: TaskScheduler = Depends(get_scheduler)):
    """Update an existing task"""
    # Convert Pydantic model to dict, excluding None values
    update_data = {k: v for k, v in task_data.dict().items() if v is not None}
    
    task = scheduler.update_task(task_id, **update_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, scheduler: TaskScheduler = Depends(get_scheduler)):
    """Delete a task"""
    if not scheduler.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return None


@app.get("/stats/", response_model=SchedulerStats)
def get_scheduler_stats(scheduler: TaskScheduler = Depends(get_scheduler)):
    """Get scheduler statistics"""
    return scheduler.get_stats()


@app.post("/tasks/batch/", response_model=List[TaskResponse], status_code=status.HTTP_201_CREATED)
def create_multiple_tasks(tasks: List[TaskCreate], scheduler: TaskScheduler = Depends(get_scheduler)):
    """Create multiple tasks at once"""
    created_tasks = []
    
    for task_data in tasks:
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            name=task_data.name,
            description=task_data.description,
            priority=task_data.priority,
            burst_time=task_data.burst_time
        )
        task = scheduler.add_task(task)
        created_tasks.append(task)
    
    return [t.to_dict() for t in created_tasks]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)