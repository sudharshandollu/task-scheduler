from app.logger import logger
import threading
import time


class TaskScheduler:
    def __init__(self, time_quantum=1.0):
        """
        Initialize the task scheduler
        
        Parameters:
        - time_quantum: Time slice allocated to each task in a round (seconds)
        """
        self.tasks = {}  # Dictionary of all tasks (task_id -> Task)
        self.ready_queue = []  # Tasks that are ready to be executed
        self.time_quantum = time_quantum
        self.start_time = time.time()
        self.execution_sequence = []
        self.lock = threading.Lock()  # For thread safety
        self.running = False
        self.scheduler_thread = None
        self.completed_tasks = []  # List of completed tasks
        self.idle = True
        self.current_task = None

    def _elapsed_time(self):
        """Get elapsed time since scheduler started"""
        return time.time() - self.start_time

    def add_task(self, task):
        """Add a new task to the scheduler"""
        with self.lock:
            task.arrival_time = self._elapsed_time()
            self.tasks[task.task_id] = task
            self.ready_queue.append(task)
            # Re-sort ready queue by priority
            self.ready_queue.sort(key=lambda x: x.priority, reverse=True)
            logger.info(f"Added: {task}")
            self.idle = False  # New task added, scheduler is not idle
            return task

    def get_task(self, task_id):
        """Get a task by ID"""
        with self.lock:
            if task_id in self.tasks:
                return self.tasks[task_id]
            return None

    def update_task(self, task_id, **kwargs):
        """Update a task's attributes"""
        with self.lock:
            if task_id not in self.tasks:
                return None
            
            task = self.tasks[task_id]
            
            # Only allow updating specific fields if task is not completed
            if task.status != "completed":
                if "name" in kwargs:
                    task.name = kwargs["name"]
                if "description" in kwargs:
                    task.description = kwargs["description"]
                if "priority" in kwargs:
                    task.priority = kwargs["priority"]
                    # Re-sort the ready queue if priority changed
                    if task in self.ready_queue:
                        self.ready_queue.remove(task)
                        self.ready_queue.append(task)
                        self.ready_queue.sort(key=lambda x: x.priority, reverse=True)
                if "burst_time" in kwargs and task.status == "pending":
                    # Only allow changing burst time if task hasn't started yet
                    old_burst = task.burst_time
                    new_burst = kwargs["burst_time"]
                    task.burst_time = new_burst
                    task.remaining_time = task.remaining_time - old_burst + new_burst
            
            logger.info(f"Updated: {task}")
            return task

    def delete_task(self, task_id):
        """Delete a task by ID"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            # Remove task from appropriate list
            if task.status == "completed":
                if task in self.completed_tasks:
                    self.completed_tasks.remove(task)
            else:
                if task in self.ready_queue:
                    self.ready_queue.remove(task)
            
            # Remove from tasks dictionary
            del self.tasks[task_id]
            logger.info(f"Deleted task: {task_id}")
            return True

    def _process_task(self, task, time_slice):
        """Process a task for the given time slice"""
        if task.status == "pending":
            task.status = "running"
        
        if task.response_time == -1:
            task.response_time = self._elapsed_time() - task.arrival_time

        start_time = self._elapsed_time()
        task.last_execution_time = start_time
        
        # Calculate actual execution time
        actual_time = min(time_slice, task.remaining_time)
        logger.info(f"Executing: {task} for {actual_time:.2f} seconds")
        
        # Simulate CPU time by sleeping
        time.sleep(actual_time)
        
        # Update task's remaining time and progress
        task.remaining_time -= actual_time
        if task.burst_time > 0:
            task.progress = min(100, int((task.burst_time - task.remaining_time) / task.burst_time * 100))
        
        end_time = start_time + actual_time
        
        # Record execution
        self.execution_sequence.append({
            'task_id': task.task_id,
            'start_time': start_time,
            'end_time': end_time
        })
        
        # If task is completed
        if task.remaining_time <= 0:
            task.status = "completed"
            current_time = self._elapsed_time()
            task.completion_time = current_time
            task.turnaround_time = current_time- task.arrival_time
            task.waiting_time = task.turnaround_time - (task.burst_time - task.remaining_time)
            task.progress = 100
            logger.info(f"Completed: {task}")
            
            with self.lock:
                self.ready_queue.remove(task)
                self.completed_tasks.append(task)
            
            return True  # Task completed
        return False  # Task not completed

    def _scheduler_loop(self):
        """Main scheduler loop that runs continuously"""
        logger.info("Scheduler loop started")
        while self.running:
            # First check if there are tasks without holding the lock for too long
            has_tasks = False
            
            # Acquire lock briefly just to check queue state
            with self.lock:
                has_tasks = len(self.ready_queue) > 0
                if not has_tasks and not self.idle:
                    logger.info("Scheduler idle - waiting for tasks...")
                    self.idle = True
            
            # Sleep outside the lock if idle
            if not has_tasks:
                time.sleep(0.1)  # Sleep briefly when idle
                continue
            
            # Process next task with proper lock management
            current_task = None
            with self.lock:
                if self.ready_queue:  # Double-check as state might have changed
                    self.idle = False  # We have tasks to process, not idle
                    self.current_task = self.ready_queue[0]
                    # Round-robin within same priority level
                    # Move to the end of its priority group
                    current_priority = self.current_task.priority
                    same_priority_count = sum(1 for t in self.ready_queue if t.priority == current_priority)
                    
                    if same_priority_count > 1:
                        self.ready_queue.remove(self.current_task)
                        
                        # Find insertion point (end of same priority group)
                        insertion_idx = 0
                        for i, t in enumerate(self.ready_queue):
                            if t.priority == current_priority:
                                insertion_idx = i + 1
                        
                        # Insert at the end of the same priority group
                        if insertion_idx >= len(self.ready_queue):
                            self.ready_queue.append(self.current_task)
                        else:
                            self.ready_queue.insert(insertion_idx, self.current_task)
                    
                    current_task = self.current_task
            
            # Process the task outside the lock if we found one
            if current_task:
                task_completed = self._process_task(current_task, self.time_quantum)
                
                # If task completed, remove from ready queue and add to completed queue
                if task_completed:
                    with self.lock:
                        # Check if task is still in ready queue (might have been removed by another thread)
                        if current_task in self.ready_queue:
                            self.ready_queue.remove(current_task)
                        if current_task not in self.completed_tasks:
                            self.completed_tasks.append(current_task)
            
            # Small sleep to prevent CPU hogging in this simulation
            time.sleep(0.01)

    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.running = False
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=1.0)
            logger.info("Scheduler stopped")

    def get_all_tasks(self):
        """Get all tasks safely"""
        print("Getting all tasks")
        with self.lock:
            # Make a shallow copy of the keys first
            task_keys = list(self.tasks.keys())
            
        # Then get the values outside the lock or process them individually
        result = []
        for key in task_keys:
            try:
                with self.lock:
                    task = self.tasks.get(key)
                    if task is not None:
                        result.append(task)
            except Exception as e:
                print(f"Error retrieving task {key}: {e}")
                
        return result

    def get_stats(self):
        """Get scheduler statistics"""
        with self.lock:
            total_tasks = len(self.tasks)
            pending_tasks = sum(1 for t in self.tasks.values() if t.status == "pending")
            running_tasks = sum(1 for t in self.tasks.values() if t.status == "running")
            completed_tasks = len(self.completed_tasks)
            
            avg_waiting = 0
            avg_turnaround = 0
            avg_response = 0
            
            if completed_tasks > 0:
                avg_waiting = sum(t.waiting_time for t in self.completed_tasks) / completed_tasks
                avg_turnaround = sum(t.turnaround_time for t in self.completed_tasks) / completed_tasks
                avg_response = sum(t.response_time for t in self.completed_tasks if t.response_time >= 0) / completed_tasks
            
            return {
                "total_tasks": total_tasks,
                "pending_tasks": pending_tasks,
                "running_tasks": running_tasks,
                "completed_tasks": completed_tasks,
                "avg_waiting_time": avg_waiting,
                "avg_turnaround_time": avg_turnaround,
                "avg_response_time": avg_response,
                "scheduler_uptime": self._elapsed_time(),
                "idle": self.idle
            }

