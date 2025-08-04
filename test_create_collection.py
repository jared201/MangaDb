from mongo_db_client import MongoDBClient

def test_create_collection():
    """Test creating a new collection."""
    client = MongoDBClient()
    
    print("Connecting to MongoDB service...")
    if not client.connect():
        print("Failed to connect to MongoDB service")
        return
    
    try:
        # Create a new collection
        collection_name = "test_collection"
        print(f"Creating collection: {collection_name}")
        doc_id = client.insert(collection_name, {})
        print(f"Created collection with document ID: {doc_id}")
        
        # Verify the collection exists by querying it
        print(f"Querying collection: {collection_name}")
        documents = client.find(collection_name, {})
        print(f"Found {len(documents)} documents in collection")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    test_create_collection()