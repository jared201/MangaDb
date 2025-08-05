import sys
import time
import subprocess
import threading

from textualize_client import HTTPClient

def start_api_server():
    """Start the FastAPI server in a separate process."""
    print("Starting FastAPI server...")
    process = subprocess.Popen([sys.executable, "main.py", "--api"])
    
    # Wait for the server to start
    time.sleep(3)
    return process

def test_http_client():
    """Test the HTTPClient functionality."""
    print("Testing HTTPClient...")
    
    # Create an HTTP client for a domain name
    # Using "localhost" but treating it as a domain name for testing
    client = HTTPClient("localhost")
    
    # Connect to the API server
    print("Connecting to API server...")
    if not client.connect():
        print("Failed to connect to API server")
        return False
    
    print("Connected to API server")
    
    try:
        # List collections
        print("Listing collections...")
        collections = client.list_collections()
        print(f"Found collections: {collections}")
        
        # Create a test collection if it doesn't exist
        test_collection = "test_http_client"
        if test_collection not in collections:
            # We'll insert a document to create the collection
            pass
        
        # Insert a document
        print("Inserting document...")
        doc = {"name": "Test User", "email": "test@example.com", "timestamp": time.time()}
        doc_id = client.insert(test_collection, doc)
        print(f"Inserted document with ID: {doc_id}")
        
        # Find the document
        print("Finding document...")
        found_doc = client.find_one(test_collection, {"_id": doc_id})
        print(f"Found document: {found_doc}")
        
        if not found_doc or found_doc.get("name") != "Test User":
            print("Error: Document not found or incorrect")
            return False
        
        # Update the document
        print("Updating document...")
        update_doc = {"name": "Updated User", "updated": True}
        modified_count = client.update(test_collection, {"_id": doc_id}, update_doc)
        print(f"Modified {modified_count} document(s)")
        
        # Find the updated document
        print("Finding updated document...")
        updated_doc = client.find_one(test_collection, {"_id": doc_id})
        print(f"Updated document: {updated_doc}")
        
        if not updated_doc or updated_doc.get("name") != "Updated User":
            print("Error: Document not updated correctly")
            return False
        
        # Delete the document
        print("Deleting document...")
        deleted_count = client.delete(test_collection, {"_id": doc_id})
        print(f"Deleted {deleted_count} document(s)")
        
        # Verify deletion
        print("Verifying deletion...")
        deleted_doc = client.find_one(test_collection, {"_id": doc_id})
        if deleted_doc:
            print("Error: Document not deleted")
            return False
        
        print("All tests passed!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
    finally:
        # Disconnect
        print("Disconnecting...")
        client.disconnect()

if __name__ == "__main__":
    # Start the API server
    api_process = start_api_server()
    
    try:
        # Run the tests
        success = test_http_client()
        
        if success:
            print("HTTPClient tests completed successfully")
            sys.exit(0)
        else:
            print("HTTPClient tests failed")
            sys.exit(1)
    finally:
        # Terminate the API server
        if api_process:
            print("Terminating API server...")
            api_process.terminate()