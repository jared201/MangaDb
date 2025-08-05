from fastapi import FastAPI, HTTPException
import subprocess
import threading
import os
import sys
import argparse
from mongo_db_client import MongoDBClient
from textualize_client import TextualizeClient

app = FastAPI(
    title="MangaDB API",
    description="API for interacting with the MongoDB-like service",
    version="1.0.0",
)

# Global MongoDB client
# Will be initialized in startup_db_client with command line arguments
mongo_client = None
mongo_service_process = None

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


@app.get("/")
async def root():
    """Root endpoint that returns information about the API."""
    return {
        "message": "Welcome to MangaDB API",
        "description": "A MongoDB-like service for storing JSON data",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "This information"},
            {"path": "/collections", "method": "GET", "description": "List all collections"},
            {"path": "/collections/{collection}", "method": "GET", "description": "Get all documents in a collection"},
            {"path": "/collections/{collection}", "method": "POST", "description": "Create a new document"},
            {"path": "/collections/{collection}/{id}", "method": "GET", "description": "Get a document by ID"},
            {"path": "/collections/{collection}/{id}", "method": "PUT", "description": "Update a document"},
            {"path": "/collections/{collection}/{id}", "method": "DELETE", "description": "Delete a document"},
        ]
    }


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
