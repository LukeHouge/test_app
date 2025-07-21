#!/usr/bin/env python3
"""
Background worker service for processing Redis queue tasks
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
import requests
import time
import os
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Configure Dramatiq broker
redis_broker = RedisBroker(url=REDIS_URL)
dramatiq.set_broker(redis_broker)

# Shared task store (in production, this would be in Redis or a database)
task_store: Dict[str, Dict[str, Any]] = {}

@dramatiq.actor(queue_name="doubler_queue", max_retries=3)
def process_number_task(task_id: str, number: int):
    """Background worker that calls the doubler microservice"""
    logger.info(f"Worker processing task {task_id} with number {number}")
    
    try:
        # Update task status to processing
        # In production, this would update Redis or database
        logger.info(f"Task {task_id}: Starting processing")
        
        # Call the doubler microservice
        doubler_url = os.getenv("DOUBLER_SERVICE_URL", "http://doubler-service:8001")
        
        logger.info(f"Task {task_id}: Calling doubler service at {doubler_url}")
        
        response = requests.post(
            f"{doubler_url}/double",
            json={"number": number},
            timeout=60  # Increased timeout for slow service
        )
        
        if response.status_code == 200:
            result = response.json()["result"]
            logger.info(f"Task {task_id}: Successfully completed - {number} -> {result}")
        else:
            logger.error(f"Task {task_id}: Doubler service returned {response.status_code}")
            raise Exception(f"Doubler service returned {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.error(f"Task {task_id}: Timeout calling doubler service")
        raise
    except requests.exceptions.ConnectionError:
        logger.error(f"Task {task_id}: Connection error to doubler service")
        raise
    except Exception as e:
        logger.error(f"Task {task_id}: Failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting Dramatiq worker...")
    logger.info(f"Redis URL: {REDIS_URL}")
    
    # Start the worker
    # This will be done via command line in the container
    import sys
    sys.exit("Use: dramatiq worker to start the worker process")