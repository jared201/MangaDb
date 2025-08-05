import sys
import time
from mongo_db_client import MongoDBClient

def test_write_operations():
    """Test all write operations to verify logging."""
    print("Starting logging test...")
    
    # Connect to MongoDB service
    client = MongoDBClient()
    if not client.connect():
        print("Failed to connect to MongoDB service")
        return False
    
    try:
        # Test collection name
        collection_name = "test_logging"
        
        # 1. Test INSERT
        print("\nTesting INSERT operation...")
        doc = {"name": "Test Document", "value": 42}
        doc_id = client.insert(collection_name, doc)
        print(f"Inserted document with ID: {doc_id}")
        
        # Wait a moment for logging to complete
        time.sleep(1)
        
        # 2. Test UPDATE
        print("\nTesting UPDATE operation...")
        update_result = client.update(collection_name, {"_id": doc_id}, {"value": 100, "updated": True})
        print(f"Updated {update_result} document(s)")
        
        # Wait a moment for logging to complete
        time.sleep(1)
        
        # 3. Test DELETE
        print("\nTesting DELETE operation...")
        delete_result = client.delete(collection_name, {"_id": doc_id})
        print(f"Deleted {delete_result} document(s)")
        
        print("\nAll write operations completed successfully.")
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    finally:
        # Disconnect from MongoDB service
        client.disconnect()

if __name__ == "__main__":
    # Make sure MongoDB service is running before executing this test
    print("This test assumes the MongoDB service is already running.")
    print("If not, please start it first by running: python mongo_db_service.py")
    
    input("Press Enter to continue with the test...")
    
    if test_write_operations():
        print("\nTest completed successfully. Check the mongodb_service.log file for logging output.")
    else:
        print("\nTest failed. Please check the error messages above.")