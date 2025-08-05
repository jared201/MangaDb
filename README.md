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

#### Command-Line Arguments

The application supports the following command-line arguments:

- `--api`: Start the FastAPI web server (default if no arguments are provided)
- `--tui`: Start the Textualize TUI client
- `--host`: Specify the host for MongoDB service (default: localhost)
- `--port`: Specify the port for MongoDB service (default: 27020, omitted for domain names)

Examples:

```bash
# Start the API with default settings
python main.py --api

# Start the TUI with a custom host
python main.py --tui --host example.com

# Start the API with a custom host and port
python main.py --api --host localhost --port 27021

# When using a domain name as host, port is automatically omitted
# and HTTPS is used for connection
python main.py --tui --host mongodb.example.com
```

When using a domain name as the host (not localhost or an IP address):
- The port argument is ignored (if provided)
- The Textualize client automatically uses the HTTP client instead of direct MongoDB access
- All REST endpoints are called via HTTP using the FastAPI server running on port 8000

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

### Using the HTTP Client

For domain names, the Textualize client automatically uses an HTTP client that communicates with the FastAPI server instead of directly accessing the MongoDB service. This HTTP client implements the same interface as the MongoDBClient, making it transparent to the application:

```python
# This is handled automatically by the Textualize client
# when connecting to a domain name (not localhost or IP address)

from textualize_client import HTTPClient

# Connect to the API server
client = HTTPClient("example.com")
client.connect()

# Use the same methods as with MongoDBClient
doc_id = client.insert("users", {"name": "John Doe", "email": "john@example.com"})
user = client.find_one("users", {"_id": doc_id})
client.update("users", {"_id": doc_id}, {"name": "Jane Doe"})
client.delete("users", {"_id": doc_id})

# Disconnect when done
client.disconnect()
```

The HTTP client translates all operations to REST API calls to the FastAPI server running on port 8000.

## Querying Collections

You can query collections in MangaDB using several methods, depending on your preferred interface.

### Query Syntax

Queries in MangaDB are JSON objects where:
- Keys are field names
- Values are the values to match

For example, to find all documents where the "name" field equals "John Doe":
```json
{"name": "John Doe"}
```

To find documents by their ID:
```json
{"_id": "document_id"}
```

To find all documents in a collection, use an empty query:
```json
{}
```

### Using the Python Client

The MongoDB client provides two methods for querying:

1. `find_one()`: Returns a single document matching the query
2. `find()`: Returns all documents matching the query

```python
from mongo_db_client import MongoDBClient

# Connect to the MongoDB service (default: localhost:27020)
client = MongoDBClient()
client.connect()

# Or specify a custom host and port
# client = MongoDBClient("custom-host", 27020)
# client.connect()

# For domain names, you can omit the port (HTTPS will be used automatically)
# client = MongoDBClient("mongodb.example.com")
# client.connect()

# Find a single document by ID
user = client.find_one("users", {"_id": "document_id"})
print(user)

# Find all documents with a specific name
users = client.find("users", {"name": "John Doe"})
for user in users:
    print(user)

# Find all documents in a collection
all_users = client.find("users", {})
for user in all_users:
    print(user)

# Disconnect when done
client.disconnect()
```

### Using the Textualize TUI Client

The Textualize TUI client provides a user-friendly interface for querying collections:

1. Start the TUI client: `python main.py --tui`
2. Select a collection from the list
3. Click the "Query" button
4. Enter your query in JSON format in the text editor
5. Click "Execute Query" to see the results

Example queries you can enter in the query editor:

```json
{"name": "John Doe"}
```

```json
{"age": 30}
```

```json
{"_id": "document_id"}
```

### Using the FastAPI Application

You can also query collections using the FastAPI application:

```bash
# Get all documents in a collection
curl -X GET "http://127.0.0.1:8000/collections/users"

# The API doesn't directly support custom queries, but you can retrieve all documents
# and filter them client-side, or use the MongoDB client or TUI for more complex queries
```

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

   # Connect to the remote MongoDB service using host and port
   client = MongoDBClient("<server_ip_or_hostname>", 27020)
   client.connect()

   # For domain names, you can omit the port (HTTPS will be used automatically)
   # client = MongoDBClient("mongodb.example.com")
   # client.connect()

   # Alternatively, you can use the mgdb:// URI format
   # client = MongoDBClient("mgdb://<server_ip_or_hostname>:27020")
   # client.connect()

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

## Deployment on Render.com

You can deploy the MangaDB FastAPI application on Render.com by following these steps:

### Prerequisites

- A [Render.com](https://render.com) account
- Your project code in a Git repository (GitHub, GitLab, etc.)

### Deployment Steps

1. **Create a New Web Service**
   - Log in to your Render.com account
   - Click on "New +" and select "Web Service"
   - Connect your Git repository containing the MangaDB project

2. **Configure the Web Service**
   - Name: Choose a name for your service (e.g., "mangadb")
   - Environment: Select "Python 3"
   - Region: Choose the region closest to your users
   - Branch: Select the branch you want to deploy (e.g., "main" or "master")
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py --api`

3. **Configure Environment Variables**
   - No specific environment variables are required for basic functionality
   - If you need to customize the application, you can add environment variables as needed

4. **Set Up Persistent Disk for Data Storage**
   - Under the "Advanced" section, click on "Add Disk"
   - Set the mount path to `/app/data`
   - Choose an appropriate disk size (start with 1GB and scale as needed)
   - This ensures your MongoDB data persists between deployments

5. **Deploy the Service**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Once deployed, you can access your API at the provided URL (e.g., `https://mangadb.onrender.com`)

### Accessing Your Deployed API

- The FastAPI application will be available at your Render.com URL
- You can access the API documentation at `https://your-app-name.onrender.com/docs`
- Use the API endpoints as described in the "Using the FastAPI Application" section

### Limitations and Considerations

- The free tier of Render.com has limited resources and may spin down after periods of inactivity
- For production use, consider upgrading to a paid plan for better performance and reliability
- The MongoDB-like service runs in the same process as the API on Render.com, which differs from a traditional setup where MongoDB would run as a separate service
- Data is stored on the persistent disk, but it's recommended to implement a backup strategy for important data

### Troubleshooting

- If the application fails to start, check the Render.com logs for error messages
- Ensure the persistent disk is properly mounted to `/app/data`
- Verify that all dependencies are correctly specified in `requirements.txt`

## License

This project is licensed under the MIT License.
