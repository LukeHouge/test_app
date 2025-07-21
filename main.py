from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import redis
import uvicorn
import os
import uuid
import asyncio
from typing import Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(REDIS_URL)

# Configure Dramatiq broker
redis_broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(redis_broker)

app = FastAPI(title="Microservices Demo", description="FastAPI with Redis Queue and Background Workers")

# Mount a static directory for CSS, JS, images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

class NumberRequest(BaseModel):
    number: int

class TaskResponse(BaseModel):
    task_id: str
    status: str
    number: int
    result: int = None

# In-memory store for demo (in production, use Redis or database)
task_store: Dict[str, Dict[str, Any]] = {}

@dramatiq.actor(queue_name="doubler_queue", max_retries=3)
def process_number_task(task_id: str, number: int):
    """Background worker that calls the doubler microservice"""
    import requests
    import time
    
    logger.info(f"Processing task {task_id} with number {number}")
    
    try:
        # Update task status
        task_store[task_id] = {
            "status": "processing",
            "number": number,
            "result": None
        }
        
        # Call the doubler microservice (with intentional delay for demo)
        doubler_url = os.getenv("DOUBLER_SERVICE_URL", "http://doubler-service:8001")
        response = requests.post(
            f"{doubler_url}/double",
            json={"number": number},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()["result"]
            task_store[task_id] = {
                "status": "completed",
                "number": number,
                "result": result
            }
            logger.info(f"Task {task_id} completed: {number} -> {result}")
        else:
            task_store[task_id] = {
                "status": "failed",
                "number": number,
                "result": None,
                "error": f"Doubler service returned {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        task_store[task_id] = {
            "status": "failed",
            "number": number,
            "result": None,
            "error": str(e)
        }

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "Microservices Demo with Redis Queue"}
    )

@app.get("/health")
def health_check():
    """Health check endpoint for Kubernetes"""
    try:
        # Check Redis connection
        redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")

@app.get("/api/greeting")
def get_greeting():
    return {"message": "Hello! This is Luke's Microservices Demo with Redis Queue!"}

@app.post("/api/queue-number", response_model=TaskResponse)
def queue_number(request: NumberRequest):
    """Queue a number to be doubled by background worker"""
    task_id = str(uuid.uuid4())
    
    # Store initial task state
    task_store[task_id] = {
        "status": "queued",
        "number": request.number,
        "result": None
    }
    
    # Queue the task
    process_number_task.send(task_id, request.number)
    
    logger.info(f"Queued task {task_id} with number {request.number}")
    
    return TaskResponse(
        task_id=task_id,
        status="queued",
        number=request.number
    )

@app.get("/api/task/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str):
    """Get the status of a queued task"""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_store[task_id]
    return TaskResponse(
        task_id=task_id,
        status=task["status"],
        number=task["number"],
        result=task.get("result")
    )

@app.get("/api/queue-stats")
def get_queue_stats():
    """Get Redis queue statistics for monitoring"""
    try:
        # Get queue length
        queue_length = redis_client.llen("doubler_queue")
        
        # Get task status counts
        status_counts = {}
        for task in task_store.values():
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "queue_length": queue_length,
            "total_tasks": len(task_store),
            "task_status_counts": status_counts,
            "redis_connected": True
        }
    except Exception as e:
        return {
            "queue_length": 0,
            "total_tasks": 0,
            "task_status_counts": {},
            "redis_connected": False,
            "error": str(e)
        }

@app.post("/api/load-test")
def create_load_test(count: int = 10):
    """Create multiple tasks for load testing"""
    task_ids = []
    
    for i in range(count):
        number = i * 2 + 1  # Generate some test numbers
        task_id = str(uuid.uuid4())
        
        task_store[task_id] = {
            "status": "queued",
            "number": number,
            "result": None
        }
        
        process_number_task.send(task_id, number)
        task_ids.append(task_id)
    
    logger.info(f"Created {count} tasks for load testing")
    
    return {
        "message": f"Created {count} tasks",
        "task_ids": task_ids
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
