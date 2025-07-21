#!/usr/bin/env python3
"""
Mock doubler microservice that takes a number and returns double
Includes artificial delay for queue demo purposes
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import time
import random
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Doubler Microservice", 
    description="Takes a number and returns double (with artificial delay for demo)"
)

class NumberRequest(BaseModel):
    number: int

class NumberResponse(BaseModel):
    number: int
    result: int
    processing_time: float

# Configurable delay for demo purposes
MIN_DELAY = float(os.getenv("MIN_DELAY_SECONDS", "2"))
MAX_DELAY = float(os.getenv("MAX_DELAY_SECONDS", "8"))

@app.get("/health")
def health_check():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "service": "doubler"}

@app.get("/")
def read_root():
    return {
        "service": "doubler-microservice",
        "version": "1.0.0",
        "description": "Doubles numbers with artificial delay for demo",
        "delay_range": f"{MIN_DELAY}-{MAX_DELAY} seconds"
    }

@app.post("/double", response_model=NumberResponse)
def double_number(request: NumberRequest):
    """
    Double the input number with artificial delay to simulate processing
    """
    start_time = time.time()
    
    logger.info(f"Received request to double: {request.number}")
    
    # Artificial delay to simulate processing time
    # This creates backpressure for queue demo
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    logger.info(f"Processing with {delay:.2f}s delay...")
    
    time.sleep(delay)
    
    # Calculate result
    result = request.number * 2
    processing_time = time.time() - start_time
    
    logger.info(f"Completed: {request.number} -> {result} (took {processing_time:.2f}s)")
    
    return NumberResponse(
        number=request.number,
        result=result,
        processing_time=processing_time
    )

@app.get("/metrics")
def get_metrics():
    """Basic metrics for monitoring"""
    return {
        "service": "doubler",
        "min_delay": MIN_DELAY,
        "max_delay": MAX_DELAY,
        "healthy": True
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    logger.info(f"Starting Doubler service on port {port}")
    logger.info(f"Delay range: {MIN_DELAY}-{MAX_DELAY} seconds")
    
    uvicorn.run("doubler_service:app", host="0.0.0.0", port=port, reload=True)