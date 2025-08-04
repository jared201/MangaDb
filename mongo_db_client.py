import socket
import json
import sys
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mongo_db_client')

# Constants
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 27020
BUFFER_SIZE = 4096

# Wire Protocol Message Types
MSG_TYPE_INSERT = 1
MSG_TYPE_UPDATE = 2
MSG_TYPE_DELETE = 3
MSG_TYPE_FIND = 4
MSG_TYPE_FIND_ONE = 5
MSG_TYPE_RESPONSE = 6
MSG_TYPE_ERROR = 7
MSG_TYPE_LIST_COLLECTIONS = 8

class MongoDBClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self) -> bool:
        """Connect to the MongoDB service."""
        try:
            logger.info(f"Attempting to connect to MangaDB service at {self.host}:{self.port}")

            # Close existing socket if any
            if self.socket:
                logger.debug("Closing existing socket connection")
                self.socket.close()
                self.socket = None

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.debug("Socket created")

            self.socket.settimeout(5)  # Set timeout to 5 seconds
            logger.debug("Socket timeout set to 5 seconds")

            logger.debug(f"Connecting to {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))

            self.socket.settimeout(None)  # Reset timeout to default
            logger.info(f"Successfully connected to MangaDB service at {self.host}:{self.port}")
            return True
        except socket.timeout as e:
            logger.error(f"Connection timeout to MangaDB service at {self.host}:{self.port}: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
        except socket.error as e:
            logger.error(f"Socket error connecting to MangaDB service at {self.host}:{self.port}: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MangaDB service at {self.host}:{self.port}: {e}")
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def disconnect(self):
        """Disconnect from the MongoDB service."""
        logger.info("Disconnecting from MangaDB service")
        if self.socket:
            try:
                logger.debug("Closing socket connection")
                self.socket.close()
                self.socket = None
                logger.info("Successfully disconnected from MangaDB service")
            except Exception as e:
                logger.error(f"Error disconnecting from MangaDB service: {e}")
        else:
            logger.debug("No active connection to disconnect")

    def _send_message(self, msg_type: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to the MongoDB service and return the response."""
        if not self.socket:
            logger.error("Attempted to send message but not connected to MangaDB service")
            raise ConnectionError("Not connected to MangaDB service")

        try:
            # Log message type and payload (excluding sensitive data)
            msg_type_name = {
                MSG_TYPE_INSERT: "INSERT",
                MSG_TYPE_UPDATE: "UPDATE",
                MSG_TYPE_DELETE: "DELETE",
                MSG_TYPE_FIND: "FIND",
                MSG_TYPE_FIND_ONE: "FIND_ONE",
                MSG_TYPE_RESPONSE: "RESPONSE",
                MSG_TYPE_ERROR: "ERROR",
                MSG_TYPE_LIST_COLLECTIONS: "LIST_COLLECTIONS"
            }.get(msg_type, f"UNKNOWN({msg_type})")

            logger.debug(f"Sending message type: {msg_type_name}")

            # Create message
            message = bytearray([msg_type])
            message.extend(json.dumps(payload).encode('utf-8'))

            # Send message
            logger.debug(f"Sending {len(message)} bytes to server")
            self.socket.sendall(message)

            # Receive response
            logger.debug("Waiting for response...")
            response = self.socket.recv(BUFFER_SIZE)
            logger.debug(f"Received {len(response)} bytes from server")

            if not response:
                logger.error("Received empty response from server")
                raise ConnectionError("Connection closed by server")

            # Parse response
            response_type = response[0]
            response_payload = json.loads(response[1:].decode('utf-8'))

            response_type_name = {
                MSG_TYPE_INSERT: "INSERT",
                MSG_TYPE_UPDATE: "UPDATE",
                MSG_TYPE_DELETE: "DELETE",
                MSG_TYPE_FIND: "FIND",
                MSG_TYPE_FIND_ONE: "FIND_ONE",
                MSG_TYPE_RESPONSE: "RESPONSE",
                MSG_TYPE_ERROR: "ERROR",
                MSG_TYPE_LIST_COLLECTIONS: "LIST_COLLECTIONS"
            }.get(response_type, f"UNKNOWN({response_type})")

            logger.debug(f"Response type: {response_type_name}")

            if response_type == MSG_TYPE_ERROR:
                error_msg = response_payload.get('error', 'Unknown error')
                logger.error(f"MongoDB service error: {error_msg}")
                raise Exception(f"MongoDB service error: {error_msg}")

            return response_payload

        except socket.timeout as e:
            logger.error(f"Socket timeout during communication with MangaDB service: {e}")
            raise ConnectionError(f"Communication timeout with MangaDB service: {e}")
        except socket.error as e:
            logger.error(f"Socket error during communication with MangaDB service: {e}")
            raise ConnectionError(f"Communication error with MangaDB service: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from MangaDB service: {e}")
            raise Exception(f"Invalid response from MangaDB service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during communication with MangaDB service: {e}")
            raise

    def insert(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection."""
        payload = {
            "collection": collection,
            "document": document
        }

        response = self._send_message(MSG_TYPE_INSERT, payload)

        if response.get("status") == "success":
            return response.get("_id")
        else:
            raise Exception(f"Insert failed: {response.get('message', 'Unknown error')}")

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        payload = {
            "collection": collection,
            "query": query
        }

        response = self._send_message(MSG_TYPE_FIND_ONE, payload)

        if response.get("status") == "success":
            return response.get("document")
        else:
            raise Exception(f"Find one failed: {response.get('message', 'Unknown error')}")

    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all documents matching the query."""
        payload = {
            "collection": collection,
            "query": query
        }

        response = self._send_message(MSG_TYPE_FIND, payload)

        if response.get("status") == "success":
            return response.get("documents", [])
        else:
            raise Exception(f"Find failed: {response.get('message', 'Unknown error')}")

    def update(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update documents matching the query."""
        payload = {
            "collection": collection,
            "query": query,
            "update": update
        }

        response = self._send_message(MSG_TYPE_UPDATE, payload)

        if response.get("status") == "success":
            return response.get("modified_count", 0)
        else:
            raise Exception(f"Update failed: {response.get('message', 'Unknown error')}")

    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents matching the query."""
        payload = {
            "collection": collection,
            "query": query
        }

        response = self._send_message(MSG_TYPE_DELETE, payload)

        if response.get("status") == "success":
            return response.get("deleted_count", 0)
        else:
            raise Exception(f"Delete failed: {response.get('message', 'Unknown error')}")

    def list_collections(self) -> List[str]:
        """List all available collections."""
        logger.info("Listing collections from MangaDB service")

        if not self.socket:
            logger.error("Cannot list collections: Not connected to MangaDB service")
            raise ConnectionError("Not connected to MangaDB service")

        try:
            payload = {}

            logger.debug("Sending LIST_COLLECTIONS request")
            response = self._send_message(MSG_TYPE_LIST_COLLECTIONS, payload)

            if response.get("status") == "success":
                collections = response.get("collections", [])
                logger.info(f"Successfully retrieved {len(collections)} collections")
                logger.debug(f"Collections: {collections}")
                return collections
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f"List collections failed: {error_msg}")
                raise Exception(f"List collections failed: {error_msg}")

        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            raise

def main():
    """Example usage of the MongoDB client."""
    client = MongoDBClient()

    print("Connecting to MongoDB service...")
    if not client.connect():
        print("Failed to connect to MongoDB service")
        return

    try:
        # Insert a document
        print("\nInserting document...")
        doc_id = client.insert("users", {"name": "John Doe", "email": "john@example.com", "age": 30})
        print(f"Inserted document with ID: {doc_id}")

        # Find the document
        print("\nFinding document by ID...")
        user = client.find_one("users", {"_id": doc_id})
        print(f"Found user: {user}")

        # Update the document
        print("\nUpdating document...")
        modified_count = client.update("users", {"_id": doc_id}, {"age": 31, "updated": True})
        print(f"Modified {modified_count} document(s)")

        # Find the updated document
        print("\nFinding updated document...")
        updated_user = client.find_one("users", {"_id": doc_id})
        print(f"Updated user: {updated_user}")

        # Insert more documents
        print("\nInserting more documents...")
        client.insert("users", {"name": "Jane Smith", "email": "jane@example.com", "age": 25})
        client.insert("users", {"name": "Bob Johnson", "email": "bob@example.com", "age": 35})

        # Find all users
        print("\nFinding all users...")
        all_users = client.find("users", {})
        print(f"Found {len(all_users)} users:")
        for user in all_users:
            print(f"  - {user['name']} ({user['email']})")

        # Find users by age
        print("\nFinding users by age...")
        young_users = client.find("users", {"age": 25})
        print(f"Found {len(young_users)} users with age 25:")
        for user in young_users:
            print(f"  - {user['name']} ({user['email']})")

        # Delete a document
        print("\nDeleting document...")
        deleted_count = client.delete("users", {"_id": doc_id})
        print(f"Deleted {deleted_count} document(s)")

        # Verify deletion
        print("\nVerifying deletion...")
        remaining_users = client.find("users", {})
        print(f"Remaining users: {len(remaining_users)}")
        for user in remaining_users:
            print(f"  - {user['name']} ({user['email']})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()
        print("\nDisconnected from MongoDB service")

if __name__ == "__main__":
    main()
