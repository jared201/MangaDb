# MangaDB

A lightweight MongoDB-like service for saving, modifying, reading, and deleting JSON objects, with both a FastAPI application and a Textualize TUI client for easy interaction. The MongoDB-like service uses a custom wire protocol and serializes JSON data to disk in *.dat files.

## Features

- Custom wire protocol for client-server communication
- Persistent storage of JSON documents in *.dat files
- CRUD operations (Create, Read, Update, Delete)
- Collection-based document organization
- Automatic document ID generation
- Multi-threaded server for handling multiple client connections
- FastAPI application for RESTful API access
- Textualize TUI client for interactive CRUD operations
- JSON editor for document creation and modification
- Query builder for searching documents
- Automatic management of the MongoDB service

## Project Components

The project consists of three main components:

1. **MongoDB-like Service**: A socket server that listens on port 27020 and handles client connections using a custom wire protocol.
2. **FastAPI Application**: A RESTful API that provides a user-friendly interface for interacting with the MongoDB-like service.
3. **Textualize TUI Client**: A text-based user interface that provides interactive CRUD operations, document editing, and query building.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- FastAPI
- Uvicorn (for running the FastAPI application)
- Textual (for the TUI client)

### Installation

```bash
pip install fastapi uvicorn textual
```

Alternatively, you can install all dependencies using the requirements.txt file:

```bash
pip install -r requirements.txt
```

### Running the Application

You can run either the FastAPI application or the Textualize TUI client:

#### FastAPI Application

To start the FastAPI application (which automatically starts the MongoDB service), run:

```bash
python main.py --api
```

Or simply:

```bash
python main.py
```

The FastAPI application will be available at http://127.0.0.1:8000, and the MongoDB service will be running on port 27020.

#### Textualize TUI Client

To start the Textualize TUI client (which automatically starts the MongoDB service), run:

```bash
python main.py --tui
```

The Textualize client provides a text-based user interface for interacting with the MongoDB service.

### Using the FastAPI Application

The FastAPI application provides the following endpoints:

- `GET /`: Get information about the API
- `GET /collections`: List all collections
- `GET /collections/{collection}`: Get all documents in a collection
- `POST /collections/{collection}`: Create a new document
- `GET /collections/{collection}/{id}`: Get a document by ID
- `PUT /collections/{collection}/{id}`: Update a document
- `DELETE /collections/{collection}/{id}`: Delete a document

Example usage:

```bash
# Create a new manga document
curl -X POST "http://127.0.0.1:8000/collections/manga" \
     -H "Content-Type: application/json" \
     -d '{"title": "One Piece", "author": "Eiichiro Oda", "chapters": 1000, "ongoing": true}'

# Get all manga documents
curl -X GET "http://127.0.0.1:8000/collections/manga"
```

See `test_main.http` for more examples.

### Using the Textualize TUI Client

The Textualize TUI client provides an interactive interface for working with the MongoDB service. It offers the following features:

#### Collection Management
- View all collections
- Create new collections
- Select and open collections

#### Document Management
- View all documents in a collection
- Create new documents
- Edit existing documents
- Delete documents
- Query documents using custom JSON queries

#### Document Editing
- JSON editor for creating and modifying documents
- Syntax highlighting
- Error validation

#### Keyboard Shortcuts
- `q`: Quit the application
- `Escape`: Go back to the previous screen
- Arrow keys: Navigate through the interface
- `Enter`: Select an item or confirm an action

#### Workflow
1. Start by selecting a collection or creating a new one
2. View the documents in the collection
3. Use the buttons to create, edit, delete, or query documents
4. When editing a document, use the JSON editor to modify the content
5. When querying, enter a JSON query to filter documents

### Using the MongoDB Client Directly

The `MongoDBClient` class provides a simple interface for interacting with the MongoDB service directly:

```python
from mongo_db_client import MongoDBClient

# Connect to the MongoDB service
client = MongoDBClient()
client.connect()

# Insert a document
doc_id = client.insert("users", {"name": "John Doe", "email": "john@example.com"})

# Find a document
user = client.find_one("users", {"_id": doc_id})

# Update a document
client.update("users", {"_id": doc_id}, {"name": "Jane Doe"})

# Delete a document
client.delete("users", {"_id": doc_id})

# Disconnect from the service
client.disconnect()
```

For a complete example, see the `main()` function in `mongo_db_client.py`.

## Wire Protocol

The wire protocol is a simple binary protocol for communication between clients and the MongoDB service.

### Message Format

Each message consists of:
1. A single byte indicating the message type
2. A JSON payload encoded as UTF-8

### Message Types

| Type | Value | Description |
|------|-------|-------------|
| INSERT | 1 | Insert a document into a collection |
| UPDATE | 2 | Update documents in a collection |
| DELETE | 3 | Delete documents from a collection |
| FIND | 4 | Find documents in a collection |
| FIND_ONE | 5 | Find a single document in a collection |
| RESPONSE | 6 | Response from the server |
| ERROR | 7 | Error response from the server |

### Request Payloads

#### INSERT
```json
{
  "collection": "collection_name",
  "document": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

#### UPDATE
```json
{
  "collection": "collection_name",
  "query": {
    "field1": "value1"
  },
  "update": {
    "field2": "new_value"
  }
}
```

#### DELETE
```json
{
  "collection": "collection_name",
  "query": {
    "field1": "value1"
  }
}
```

#### FIND
```json
{
  "collection": "collection_name",
  "query": {
    "field1": "value1"
  }
}
```

#### FIND_ONE
```json
{
  "collection": "collection_name",
  "query": {
    "field1": "value1"
  }
}
```

### Response Payloads

#### Success Response
```json
{
  "status": "success",
  "_id": "document_id"  
}
```

```json
{
  "status": "success",
  "document": {  
    "_id": "document_id",
    "field1": "value1"
  }
}
```

```json
{
  "status": "success",
  "documents": [  
    {
      "_id": "document_id1",
      "field1": "value1"
    },
    {
      "_id": "document_id2",
      "field1": "value2"
    }
  ]
}
```

```json
{
  "status": "success",
  "modified_count": 1  
}
```

```json
{
  "status": "success",
  "deleted_count": 1  
}
```

#### Error Response
```json
{
  "status": "error",
  "message": "Error message"
}
```

## Data Storage

Documents are stored in *.dat files in the `data` directory. Each collection is stored in a separate file named `collection_name.dat`.

Each line in a .dat file represents a single JSON document. Documents are appended to the file when inserted and the entire file is rewritten when documents are updated or deleted.

## Remote Connection

### Connecting to the FastAPI Application

The FastAPI application binds to all network interfaces (0.0.0.0) on port 8000, making it accessible remotely:

1. Ensure the server is running with `python main.py --api` or simply `python main.py`
2. From a remote machine, access the API using the server's IP address or hostname:
   ```
   http://<server_ip_or_hostname>:8000
   ```
3. Example API calls from a remote client:
   ```bash
   # Get information about the API
   curl -X GET "http://<server_ip_or_hostname>:8000"

   # List all collections
   curl -X GET "http://<server_ip_or_hostname>:8000/collections"

   # Create a new document
   curl -X POST "http://<server_ip_or_hostname>:8000/collections/manga" \
        -H "Content-Type: application/json" \
        -d '{"title": "One Piece", "author": "Eiichiro Oda"}'
   ```

### Connecting to the MongoDB Service Directly

The MongoDB service binds to all network interfaces (0.0.0.0) on port 27020, allowing direct connections from remote clients:

1. Ensure the MongoDB service is running (it starts automatically with the FastAPI app or TUI client)
2. In your Python code, initialize the MongoDBClient with the server's IP address or hostname:
   ```python
   from mongo_db_client import MongoDBClient

   # Connect to the remote MongoDB service
   client = MongoDBClient(host="<server_ip_or_hostname>", port=27020)
   client.connect()

   # Use the client as usual
   doc_id = client.insert("users", {"name": "John Doe", "email": "john@example.com"})

   # Disconnect when done
   client.disconnect()
   ```

### Network Considerations

- Ensure that ports 8000 (FastAPI) and 27020 (MongoDB service) are open in any firewalls between the client and server
- For public-facing deployments, consider implementing additional security measures such as:
  - Using a reverse proxy (like Nginx) with HTTPS
  - Implementing authentication for the API
  - Setting up network-level access controls

## License

This project is licensed under the MIT License.
