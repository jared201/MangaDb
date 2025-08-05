#!/usr/bin/env python3
"""
Test script to verify connection to the remote MangaDB server.
"""

import sys
import logging
from textualize_client import HTTPClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_remote_connection')

def test_remote_connection(host):
    """Test connection to a remote MangaDB server."""
    logger.info(f"Testing connection to remote server: {host}")
    
    # Create HTTP client
    client = HTTPClient(host)
    
    # Try to connect
    if client.connect():
        logger.info("Connection successful!")
        
        # Test listing collections
        try:
            collections = client.list_collections()
            logger.info(f"Collections found: {collections}")
            
            # If there are collections, try to get documents from the first one
            if collections:
                collection_name = collections[0]
                logger.info(f"Testing retrieval from collection: {collection_name}")
                documents = client.find(collection_name, {})
                logger.info(f"Found {len(documents)} documents in {collection_name}")
                
                # Display first document if available
                if documents:
                    logger.info(f"First document: {documents[0]}")
            
        except Exception as e:
            logger.error(f"Error testing API functionality: {e}")
        
        # Disconnect
        client.disconnect()
        logger.info("Test completed successfully")
        return True
    else:
        logger.error("Failed to connect to the remote server")
        return False

if __name__ == "__main__":
    # Use command line argument if provided, otherwise use default
    host = sys.argv[1] if len(sys.argv) > 1 else "mangadb-bwmu.onrender.com"
    
    logger.info(f"Starting remote connection test to {host}")
    success = test_remote_connection(host)
    
    if success:
        logger.info("✅ Remote connection test passed")
        sys.exit(0)
    else:
        logger.error("❌ Remote connection test failed")
        sys.exit(1)