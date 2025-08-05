import socket
import json
import os
import threading
import uuid
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mongodb_service.log")
    ]
)
logger = logging.getLogger("MongoDBService")

# Constants
DEFAULT_PORT = 27020
DATA_DIR = "data"
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

class MongoDBService:
    def __init__(self, port: int = DEFAULT_PORT, data_dir: str = DATA_DIR):
        self.port = port
        self.data_dir = data_dir
        self.collections: Dict[str, Dict[str, Any]] = {}
        self.server_socket = None
        self.running = False

        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        # Load existing collections
        self._load_collections()

    def _load_collections(self):
        """Load all collections from disk."""
        if not os.path.exists(self.data_dir):
            return

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".dat"):
                collection_name = filename[:-4]  # Remove .dat extension
                self.collections[collection_name] = {}
                collection_path = os.path.join(self.data_dir, filename)

                try:
                    with open(collection_path, 'r') as f:
                        for line in f:
                            if line.strip():
                                doc = json.loads(line)
                                if "_id" in doc:
                                    self.collections[collection_name][doc["_id"]] = doc
                except Exception as e:
                    print(f"Error loading collection {collection_name}: {e}")

    def _save_document(self, collection_name: str, document: Dict[str, Any]):
        """Save a document to disk."""
        logger.info(f"FILE_WRITE - Collection: {collection_name} - Saving document to disk")
        
        if collection_name not in self.collections:
            logger.info(f"FILE_WRITE - Collection: {collection_name} - Creating new collection in memory")
            self.collections[collection_name] = {}

        # Ensure document has an _id
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
            logger.info(f"FILE_WRITE - Collection: {collection_name} - Generated new _id: {document['_id']}")

        # Store in memory
        self.collections[collection_name][document["_id"]] = document
        logger.info(f"FILE_WRITE - Collection: {collection_name} - Document with _id: {document['_id']} stored in memory")

        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        # Save to disk
        collection_path = os.path.join(self.data_dir, f"{collection_name}.dat")
        logger.info(f"FILE_WRITE - Collection: {collection_name} - Writing to file: {collection_path}")

        # Append to file
        try:
            with open(collection_path, 'a') as f:
                f.write(json.dumps(document) + "\n")
            logger.info(f"FILE_WRITE - Collection: {collection_name} - Document with _id: {document['_id']} successfully written to disk")
        except Exception as e:
            logger.error(f"FILE_WRITE - Collection: {collection_name} - Error writing document to disk: {e}")

    def _update_collection_file(self, collection_name: str):
        """Rewrite the entire collection file."""
        logger.info(f"FILE_UPDATE - Collection: {collection_name} - Starting collection file update")
        
        if collection_name not in self.collections:
            logger.info(f"FILE_UPDATE - Collection: {collection_name} - Collection not found, no update performed")
            return

        collection_path = os.path.join(self.data_dir, f"{collection_name}.dat")
        doc_count = len(self.collections[collection_name])
        logger.info(f"FILE_UPDATE - Collection: {collection_name} - Rewriting file with {doc_count} documents")

        try:
            with open(collection_path, 'w') as f:
                for doc in self.collections[collection_name].values():
                    f.write(json.dumps(doc) + "\n")
            logger.info(f"FILE_UPDATE - Collection: {collection_name} - Successfully rewrote collection file with {doc_count} documents")
        except Exception as e:
            logger.error(f"FILE_UPDATE - Collection: {collection_name} - Error updating collection file: {e}")

    def insert(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection."""
        logger.info(f"INSERT - Collection: {collection_name} - Starting insert operation")
        
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
            logger.info(f"INSERT - Collection: {collection_name} - Generated new _id: {document['_id']}")
        else:
            logger.info(f"INSERT - Collection: {collection_name} - Using provided _id: {document['_id']}")

        self._save_document(collection_name, document)
        logger.info(f"INSERT - Collection: {collection_name} - Document inserted successfully with _id: {document['_id']}")
        return document["_id"]

    def find_one(self, collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        if collection_name not in self.collections:
            return None

        for doc in self.collections[collection_name].values():
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break
            if matches:
                return doc

        return None

    def find(self, collection_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all documents matching the query."""
        results = []

        if collection_name not in self.collections:
            return results

        for doc in self.collections[collection_name].values():
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break
            if matches:
                results.append(doc)

        return results

    def update(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update documents matching the query."""
        logger.info(f"UPDATE - Collection: {collection_name} - Starting update operation with query: {query}")
        
        if collection_name not in self.collections:
            logger.info(f"UPDATE - Collection: {collection_name} - Collection not found, no documents updated")
            return 0

        count = 0
        updated_ids = []
        for doc_id, doc in list(self.collections[collection_name].items()):
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break

            if matches:
                logger.info(f"UPDATE - Collection: {collection_name} - Updating document with _id: {doc_id}")
                for key, value in update.items():
                    doc[key] = value
                count += 1
                updated_ids.append(doc_id)

        if count > 0:
            logger.info(f"UPDATE - Collection: {collection_name} - Updated {count} document(s) with IDs: {updated_ids}")
            logger.info(f"UPDATE - Collection: {collection_name} - Rewriting collection file")
            self._update_collection_file(collection_name)
        else:
            logger.info(f"UPDATE - Collection: {collection_name} - No documents matched the query, no updates performed")

        return count

    def delete(self, collection_name: str, query: Dict[str, Any]) -> int:
        """Delete documents matching the query."""
        logger.info(f"DELETE - Collection: {collection_name} - Starting delete operation with query: {query}")
        
        if collection_name not in self.collections:
            logger.info(f"DELETE - Collection: {collection_name} - Collection not found, no documents deleted")
            return 0

        count = 0
        to_delete = []

        for doc_id, doc in list(self.collections[collection_name].items()):
            matches = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    matches = False
                    break

            if matches:
                logger.info(f"DELETE - Collection: {collection_name} - Document with _id: {doc_id} matched query")
                to_delete.append(doc_id)
                count += 1

        logger.info(f"DELETE - Collection: {collection_name} - Found {count} document(s) to delete")
        
        for doc_id in to_delete:
            logger.info(f"DELETE - Collection: {collection_name} - Deleting document with _id: {doc_id}")
            del self.collections[collection_name][doc_id]

        if count > 0:
            logger.info(f"DELETE - Collection: {collection_name} - Deleted {count} document(s) with IDs: {to_delete}")
            logger.info(f"DELETE - Collection: {collection_name} - Rewriting collection file")
            self._update_collection_file(collection_name)
        else:
            logger.info(f"DELETE - Collection: {collection_name} - No documents matched the query, no deletions performed")

        return count

    def _parse_message(self, data: bytes) -> Tuple[int, Dict[str, Any]]:
        """Parse a message from the wire protocol."""
        try:
            # First byte is message type
            msg_type = data[0]
            # Rest is JSON payload
            payload = json.loads(data[1:].decode('utf-8'))
            return msg_type, payload
        except Exception as e:
            print(f"Error parsing message: {e}")
            return MSG_TYPE_ERROR, {"error": str(e)}

    def _create_response(self, msg_type: int, payload: Any) -> bytes:
        """Create a response message for the wire protocol."""
        try:
            # First byte is message type
            response = bytearray([msg_type])
            # Rest is JSON payload
            json_payload = json.dumps(payload).encode('utf-8')
            response.extend(json_payload)
            return bytes(response)
        except Exception as e:
            print(f"Error creating response: {e}")
            error_response = bytearray([MSG_TYPE_ERROR])
            error_response.extend(json.dumps({"error": str(e)}).encode('utf-8'))
            return bytes(error_response)

    def _handle_client(self, client_socket, address):
        """Handle a client connection."""
        print(f"New connection from {address}")

        try:
            while self.running:
                # Receive data
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    break

                # Parse message
                msg_type, payload = self._parse_message(data)
                response_payload = {"status": "error", "message": "Unknown message type"}

                # Process message
                if msg_type == MSG_TYPE_INSERT:
                    collection = payload.get("collection")
                    document = payload.get("document", {})
                    doc_id = self.insert(collection, document)
                    response_payload = {"status": "success", "_id": doc_id}

                elif msg_type == MSG_TYPE_FIND_ONE:
                    collection = payload.get("collection")
                    query = payload.get("query", {})
                    result = self.find_one(collection, query)
                    response_payload = {"status": "success", "document": result}

                elif msg_type == MSG_TYPE_FIND:
                    collection = payload.get("collection")
                    query = payload.get("query", {})
                    results = self.find(collection, query)
                    response_payload = {"status": "success", "documents": results}

                elif msg_type == MSG_TYPE_UPDATE:
                    collection = payload.get("collection")
                    query = payload.get("query", {})
                    update = payload.get("update", {})
                    count = self.update(collection, query, update)
                    response_payload = {"status": "success", "modified_count": count}

                elif msg_type == MSG_TYPE_DELETE:
                    collection = payload.get("collection")
                    query = payload.get("query", {})
                    count = self.delete(collection, query)
                    response_payload = {"status": "success", "deleted_count": count}

                elif msg_type == MSG_TYPE_LIST_COLLECTIONS:
                    collections = list(self.collections.keys())
                    response_payload = {"status": "success", "collections": collections}

                # Send response
                response = self._create_response(MSG_TYPE_RESPONSE, response_payload)
                client_socket.sendall(response)

        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            print(f"Connection from {address} closed")

    def start(self):
        """Start the MongoDB service."""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            print(f"MongoDB service listening on port {self.port}")

            while self.running:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(client_socket, address))
                client_thread.daemon = True
                client_thread.start()

        except KeyboardInterrupt:
            print("Shutting down...")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop the MongoDB service."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

if __name__ == "__main__":
    service = MongoDBService()
    service.start()
