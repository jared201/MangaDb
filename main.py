from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import datetime
import subprocess
import threading
import os
import sys
import argparse
import uuid
from typing import Optional
from mongo_db_client import MongoDBClient
from textualize_client import TextualizeClient

app = FastAPI(
    title="MangaDB API",
    description="API for interacting with the MongoDB-like service",
    version="1.0.0",
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Global MongoDB client
# Will be initialized in startup_db_client with command line arguments
mongo_client = None
mongo_service_process = None

# Define data models for the certification workflow
class ExamResult(BaseModel):
    full_name: str
    email: str
    score: int
    passed: bool
    payment_status: str = "pending"
    payment_id: Optional[str] = None
    certificate_issued: bool = False
    timestamp: str

class PaymentUpdate(BaseModel):
    email: str
    payment_id: str
    payment_status: str

@app.on_event("startup")
async def startup_db_client():
    """Start the MongoDB service and connect the client."""
    global mongo_service_process, mongo_client
    
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int)
    # Parse known args to avoid errors with other arguments
    args, _ = parser.parse_known_args()
    
    host = args.host
    port = args.port
    
    # Initialize MongoDB client with host and port
    if port is not None:
        mongo_client = MongoDBClient(host, port)
    else:
        mongo_client = MongoDBClient(host)

    # Start MongoDB service in a separate process
    if not os.path.exists("data"):
        os.makedirs("data")

    # Start the MongoDB service in a separate process
    mongo_service_process = subprocess.Popen([sys.executable, "mongo_db_service.py"])

    # Wait a moment for the service to start
    import time
    time.sleep(1)

    # Connect the client
    if not mongo_client.connect():
        print("Warning: Failed to connect to MongoDB service")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Disconnect the MongoDB client and stop the service."""
    mongo_client.disconnect()

    # Terminate the MongoDB service process
    if mongo_service_process:
        mongo_service_process.terminate()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint that serves the landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/exam", response_class=HTMLResponse)
async def exam(request: Request):
    """Serve the MangaDB Certified Developer Examination page."""
    return templates.TemplateResponse("exam.html", {"request": request})

@app.get("/certificate", response_class=HTMLResponse)
async def certificate(
    request: Request, 
    recipient_name: str = "John Doe", 
    signatory_name: str = "Jared Odulio", 
    signatory_title: str = "MangaDB Lead Developer",
    payment_id: Optional[str] = None
):
    """Generate a MangaDB Certified Developer certificate."""
    # Get current date in a nice format
    current_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    # If payment_id is provided, verify payment status
    if payment_id:
        # Find the exam result with this payment ID
        try:
            results = mongo_client.find("exam_attempts", {"payment_id": payment_id})
            if results and len(results) > 0:
                # Update the certificate issued status
                mongo_client.update("exam_attempts", {"payment_id": payment_id}, {"certificate_issued": True})
            else:
                # Payment ID not found, but we'll still show the certificate
                # In a production app, you might want to redirect to an error page
                pass
        except Exception as e:
            # Log the error but continue to show the certificate
            print(f"Error verifying payment: {str(e)}")
    
    # Render the certificate template with the provided information
    return templates.TemplateResponse(
        "certificate.html", 
        {
            "request": request,
            "recipient_name": recipient_name,
            "signatory_name": signatory_name,
            "signatory_title": signatory_title,
            "certificate_date": current_date
        }
    )

@app.get("/api")
async def api_info():
    """Endpoint that returns information about the API."""
    return {
        "message": "Welcome to MangaDB API",
        "description": "A MongoDB-like service for storing JSON data",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Landing page"},
            {"path": "/api", "method": "GET", "description": "This API information"},
            {"path": "/exam", "method": "GET", "description": "MangaDB Certified Developer Examination"},
            {"path": "/certificate", "method": "GET", "description": "Generate a MangaDB Certified Developer certificate"},
            {"path": "/api/exam-results", "method": "POST", "description": "Save examination results"},
            {"path": "/api/update-payment", "method": "POST", "description": "Update payment status"},
            {"path": "/collections", "method": "GET", "description": "List all collections"},
            {"path": "/collections/{collection}", "method": "GET", "description": "Get all documents in a collection"},
            {"path": "/collections/{collection}", "method": "POST", "description": "Create a new document"},
            {"path": "/collections/{collection}/{id}", "method": "GET", "description": "Get a document by ID"},
            {"path": "/collections/{collection}/{id}", "method": "PUT", "description": "Update a document"},
            {"path": "/collections/{collection}/{id}", "method": "DELETE", "description": "Delete a document"},
        ]
    }

@app.post("/api/exam-results")
async def save_exam_results(exam_result: ExamResult):
    """Save examination results to the database."""
    try:
        # Generate a unique ID for the exam result
        exam_result_dict = exam_result.dict()
        
        # Insert the exam result into the database
        doc_id = mongo_client.insert("exam_attempts", exam_result_dict)
        return {"status": "success", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-payment")
async def update_payment_status(payment_update: PaymentUpdate):
    """Update payment status for an examination."""
    try:
        # Find the exam result by email
        results = mongo_client.find("exam_attempts", {"email": payment_update.email})
        
        if not results or len(results) == 0:
            raise HTTPException(status_code=404, detail="Exam result not found")
        
        # Update the payment status and payment ID
        count = mongo_client.update(
            "exam_attempts", 
            {"email": payment_update.email}, 
            {
                "payment_status": payment_update.payment_status,
                "payment_id": payment_update.payment_id
            }
        )
        
        if count == 0:
            raise HTTPException(status_code=404, detail="Failed to update payment status")
            
        return {"status": "success", "modified_count": count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections")
async def get_collections():
    """Get a list of all collections."""
    try:
        # Use the list_collections method from the MongoDB client
        collections = mongo_client.list_collections()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections/{collection}")
async def get_documents(collection: str):
    """Get all documents in a collection."""
    try:
        documents = mongo_client.find(collection, {})
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/collections/{collection}")
async def create_document(collection: str, document: dict):
    """Create a new document in a collection."""
    try:
        doc_id = mongo_client.insert(collection, document)
        return {"_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collections/{collection}/{id}")
async def get_document(collection: str, id: str):
    """Get a document by ID."""
    try:
        document = mongo_client.find_one(collection, {"_id": id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/collections/{collection}/{id}")
async def update_document(collection: str, id: str, update: dict):
    """Update a document."""
    try:
        count = mongo_client.update(collection, {"_id": id}, update)
        if count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"modified_count": count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collections/{collection}/{id}")
async def delete_document(collection: str, id: str):
    """Delete a document."""
    try:
        count = mongo_client.delete(collection, {"_id": id})
        if count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"deleted_count": count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MangaDB - MongoDB-like service with API and TUI")
    parser.add_argument("--tui", action="store_true", help="Start the Textualize TUI client")
    parser.add_argument("--api", action="store_true", help="Start the FastAPI web server")
    parser.add_argument("--host", type=str, default="localhost", help="Host for MongoDB service (default: localhost)")
    parser.add_argument("--port", type=int, help="Port for MongoDB service (default: 27020, omitted for domain names)")
    args = parser.parse_args()

    # Default to API if no arguments provided
    if not args.tui and not args.api:
        args.api = True

    # Start the MongoDB service in a separate process
    if not os.path.exists("data"):
        os.makedirs("data")

    mongo_service_process = subprocess.Popen([sys.executable, "mongo_db_service.py"])

    # Wait a moment for the service to start
    import time
    time.sleep(1)

    try:
        if args.tui:
            # Start the Textualize client with host and port
            if args.port is not None:
                app = TextualizeClient(args.host, args.port)
            else:
                app = TextualizeClient(args.host)
            app.run()
        else:
            # Start the FastAPI server
            import uvicorn
            uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        # Terminate the MongoDB service process
        if mongo_service_process:
            mongo_service_process.terminate()
