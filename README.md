# FastAPI Task Scheduler

A RESTful API for a priority-based round-robin task scheduler built with FastAPI.

## Overview

This project implements a continuously running task scheduler that uses priority-based round-robin scheduling to process tasks. It provides a RESTful API interface to create, read, update, and delete tasks, as well as monitor task and scheduler statistics.

## Features

- **Priority-based scheduling**: Higher priority tasks execute first
- **Round-robin algorithm**: Tasks with the same priority level are executed in a circular manner
- **RESTful API**: Full CRUD operations for task management
- **Continuous execution**: Scheduler runs as a background process
- **Real-time metrics**: Track waiting time, turnaround time, response time, and more

## Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   uvicorn main:app --reload
   ```
## API Documentation

Once the application is running, you can access:
- Swagger UI documentation: http://localhost:8000/docs
