import time

# Task Scheduler Implementation
class Task:
    def __init__(self, task_id: str, name: str, priority: int, burst_time: float, 
                 description: str = "", created_at: float = None):
        """
        Initialize a task with given parameters
        
        Parameters:
        - task_id: Unique identifier for the task
        - name: Name/description of the task
        - priority: Priority level (higher value means higher priority)
        - burst_time: Total execution time required by the task in seconds
        - description: Optional detailed description
        - created_at: Time at which the task was created
        """
        self.task_id = task_id
        self.name = name
        self.description = description
        self.priority = priority
        self.burst_time = burst_time
        self.created_at = created_at if created_at is not None else time.time()
        self.arrival_time = 0
        self.remaining_time = burst_time
        self.waiting_time = 0
        self.turnaround_time = 0
        self.completion_time = None
        self.response_time = -1  # Will be set when task first gets CPU
        self.last_execution_time = 0  # Last time this task was executed
        self.status = "pending"  # pending, running, completed, cancelled
        self.progress = 0  # 0-100%

    def to_dict(self):
        """Convert task to dictionary for API response"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "burst_time": self.burst_time,
            "created_at": self.created_at,
            "arrival_time": self.arrival_time,
            "remaining_time": self.remaining_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "completion_time": self.completion_time if self.completion_time else 0,
            "response_time": self.response_time,
            "status": self.status,
            "progress": self.progress
        }

    def __str__(self):
        return f"Task {self.task_id}: {self.name} (Priority: {self.priority}, Remaining: {self.remaining_time:.2f}s, Status: {self.status})"
