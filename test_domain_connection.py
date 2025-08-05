"""
Test script to verify domain name handling in MongoDBClient.
"""
import sys
import logging
from mongo_db_client import MongoDBClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_domain_connection')

def test_domain_connection():
    """Test connecting with different host types."""
    # Test with localhost (should use port)
    logger.info("Testing with localhost...")
    client1 = MongoDBClient("mgdb://localhost:27020")
    logger.info(f"Client1 host: {client1.host}, port: {client1.port}")
    
    # Test with IP address (should use port)
    logger.info("Testing with IP address...")
    client2 = MongoDBClient("mgdb://127.0.0.1:27020")
    logger.info(f"Client2 host: {client2.host}, port: {client2.port}")
    
    # Test with domain name (should not use port)
    logger.info("Testing with domain name...")
    client3 = MongoDBClient("mgdb://example.com:27020")
    logger.info(f"Client3 host: {client3.host}, port: {client3.port}")
    
    # Test with domain name without port
    logger.info("Testing with domain name without port...")
    client4 = MongoDBClient("mgdb://example.com")
    logger.info(f"Client4 host: {client4.host}, port: {client4.port}")
    
    # Test with direct hostname (not URI)
    logger.info("Testing with direct hostname...")
    client5 = MongoDBClient("example.com", 27020)
    logger.info(f"Client5 host: {client5.host}, port: {client5.port}")
    
    # Test connection attempts
    logger.info("\nTesting connection attempts...")
    
    # Only attempt to connect to localhost since we know the service is running there
    logger.info("Attempting to connect to localhost...")
    try:
        if client1.connect():
            logger.info("Successfully connected to localhost")
            client1.disconnect()
        else:
            logger.warning("Failed to connect to localhost")
    except Exception as e:
        logger.error(f"Error connecting to localhost: {e}")
    
    # Test connection logic with a domain name (will likely fail but shows the logic works)
    logger.info("Attempting to connect to example.com (will likely fail but shows the logic)...")
    try:
        # This will likely fail since example.com doesn't run our service
        # But it will show that the connection logic works correctly
        if client3.connect():
            logger.info("Successfully connected to example.com")
            client3.disconnect()
        else:
            logger.warning("Failed to connect to example.com (expected)")
    except Exception as e:
        logger.error(f"Error connecting to example.com: {e}")
    
    logger.info("All tests completed.")

if __name__ == "__main__":
    test_domain_connection()