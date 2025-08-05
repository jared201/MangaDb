try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Header, Footer, Button, Input, Label, Select, DataTable, TextArea, Static
    from textual.screen import Screen
    from textual.binding import Binding
    from textual.reactive import reactive
except ImportError as e:
    print(f"Error importing textual package: {e}")
    print("Please make sure textual is installed by running: pip install textual==0.52.1")
    import sys
    sys.exit(1)
import json
import os
import sys
import subprocess
import time
import logging
import requests
from typing import Dict, List, Any, Optional
from mongo_db_client import MongoDBClient

class HTTPClient:
    """HTTP client that implements the same interface as MongoDBClient but uses REST endpoints."""
    
    def __init__(self, host: str, port: int = None):
        """Initialize the HTTP client with host.
        
        Note: For remote servers like mangadb-bwmu.onrender.com, port is not needed
        as the server uses standard HTTP/HTTPS ports.
        """
        self.host = host
        logger.info(f"Connecting to MongoDB at {host}")
        self.port = None  # Not used for HTTP client
        
        # Handle different server configurations
        if "onrender.com" in host or "." in host:
            # For render.com or other domain-based deployments, use HTTPS without specifying port
            self.base_url = f"https://{host}"
            logger.info(f"Using HTTPS for remote server: {self.base_url}")
        else:
            # For localhost or IP addresses, use HTTP with port 8000
            self.base_url = f"http://{host}:8000"  # FastAPI server runs on port 8000
            logger.info(f"Using HTTP with port 8000: {self.base_url}")
            
        self.connected = False
        # Initialize socket to None for compatibility with MongoDBClient interface
        # MongoDBClient uses 'if not self.socket:' to check connection status
        self.socket = None
        
    def connect(self) -> bool:
        """Connect to the API server."""
        try:
            # Test connection by making a request to the root endpoint
            logger.info(f"Attempting to connect to API server at {self.base_url}")
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully connected to API server at {self.base_url}")
                self.connected = True
                # Set socket to a non-None value when connected to maintain compatibility with MongoDBClient interface
                # MongoDBClient checks 'if not self.socket:' to determine connection status
                self.socket = True
                return True
            else:
                logger.error(f"Failed to connect to API server. Status code: {response.status_code}")
                self.connected = False
                self.socket = None
                return False
                
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error connecting to API server: {e}")
            self.connected = False
            self.socket = None
            return False
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to API server: {e}")
            self.connected = False
            self.socket = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to API server: {e}")
            self.connected = False
            self.socket = None
            return False
            
    def disconnect(self):
        """Disconnect from the API server."""
        self.connected = False
        self.socket = None
        
    def list_collections(self) -> List[str]:
        """List all available collections."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        response = requests.get(f"{self.base_url}/collections")
        if response.status_code == 200:
            return response.json().get("collections", [])
        else:
            raise Exception(f"List collections failed: {response.text}")
            
    def find(self, collection: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find all documents matching the query."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        response = requests.get(f"{self.base_url}/collections/{collection}")
        if response.status_code == 200:
            documents = response.json().get("documents", [])
            # Filter documents based on query if it's not empty
            if query:
                filtered_docs = []
                for doc in documents:
                    match = True
                    for key, value in query.items():
                        if key not in doc or doc[key] != value:
                            match = False
                            break
                    if match:
                        filtered_docs.append(doc)
                return filtered_docs
            return documents
        else:
            raise Exception(f"Find failed: {response.text}")
            
    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document matching the query."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        # If query has _id, use the direct endpoint
        if "_id" in query:
            doc_id = query["_id"]
            response = requests.get(f"{self.base_url}/collections/{collection}/{doc_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"Find one failed: {response.text}")
        else:
            # Otherwise, get all documents and filter
            documents = self.find(collection, query)
            return documents[0] if documents else None
            
    def insert(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        response = requests.post(f"{self.base_url}/collections/{collection}", json=document)
        if response.status_code == 200:
            return response.json().get("_id")
        else:
            raise Exception(f"Insert failed: {response.text}")
            
    def update(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update documents matching the query."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        # Currently only supports updating by _id
        if "_id" in query:
            doc_id = query["_id"]
            response = requests.put(f"{self.base_url}/collections/{collection}/{doc_id}", json=update)
            if response.status_code == 200:
                return response.json().get("modified_count", 0)
            elif response.status_code == 404:
                return 0
            else:
                raise Exception(f"Update failed: {response.text}")
        else:
            # For other queries, we'd need to implement a more complex solution
            # This is a simplified implementation
            raise NotImplementedError("Update with non-_id queries is not implemented for HTTP client")
            
    def delete(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete documents matching the query."""
        if not self.connected:
            raise ConnectionError("Not connected to API server")
            
        # Currently only supports deleting by _id
        if "_id" in query:
            doc_id = query["_id"]
            response = requests.delete(f"{self.base_url}/collections/{collection}/{doc_id}")
            if response.status_code == 200:
                return response.json().get("deleted_count", 0)
            elif response.status_code == 404:
                return 0
            else:
                raise Exception(f"Delete failed: {response.text}")
        else:
            # For other queries, we'd need to implement a more complex solution
            # This is a simplified implementation
            raise NotImplementedError("Delete with non-_id queries is not implemented for HTTP client")

# Configure logging for textualize client
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('textualize_client')

class CollectionSelect(Screen):
    """Screen for selecting a collection."""

    def __init__(self, client: MongoDBClient):
        super().__init__()
        self.client = client
        self.collections = []

    def compose(self) -> ComposeResult:
        """Compose the collection selection screen."""
        yield Header(show_clock=True)
        yield Container(
            Label("Select a Collection", id="title"),
            Select(id="collection-select", options=[]),
            Button("View Collection", id="view-btn", disabled=True),
            Button("Create New Collection", id="create-btn"),
            Button("Quit", id="quit-btn"),
            id="collection-screen"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load collections when the screen is mounted."""
        self.load_collections()

    def load_collections(self) -> None:
        """Load collections from the MongoDB service."""
        logger.info("Loading collections from MongoDB service")
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Check if client is connected
                if not self.client.socket:
                    logger.warning("Client socket is not connected, attempting to connect")
                    if not self.client.connect():
                        logger.error("Failed to connect to MongoDB service")
                        self.notify("Failed to connect to MongoDB service. UI will continue with limited functionality.", severity="warning")
                        self.collections = []
                        break

                # Get collections
                logger.debug("Calling list_collections()")
                try:
                    self.collections = self.client.list_collections()
                    logger.info(f"Successfully loaded {len(self.collections)} collections")
                except Exception as e:
                    logger.error(f"Error calling list_collections: {e}")
                    self.notify(f"Error loading collections. UI will continue with limited functionality.", severity="error")
                    self.collections = []
                break  # Exit the retry loop

            except ConnectionError as e:
                retry_count += 1
                logger.error(f"Connection error loading collections (attempt {retry_count}/{max_retries}): {e}")

                if retry_count < max_retries:
                    # Try to reconnect
                    logger.info(f"Attempting to reconnect (retry {retry_count}/{max_retries})")
                    self.client.disconnect()  # Ensure clean disconnect before reconnecting
                    time.sleep(1)  # Wait before retry
                else:
                    # All retries failed
                    self.notify(f"Error loading collections. UI will continue with limited functionality.", severity="warning")
                    self.collections = []
            except Exception as e:
                logger.error(f"Unexpected error loading collections: {e}", exc_info=True)
                self.notify(f"Error loading collections. UI will continue with limited functionality.", severity="warning")
                self.collections = []
                break  # Don't retry on non-connection errors

        # Update UI
        logger.debug("Updating collection select options")
        select = self.query_one("#collection-select", Select)
        logger.debug(self.collections)

        select.set_options((option, option) for option in self.collections)

        # Disable view button if no collections
        view_btn = self.query_one("#view-btn", Button)
        view_btn.disabled = len(self.collections) == 0
        logger.debug(f"View button disabled: {view_btn.disabled}")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Enable the view button when a collection is selected."""
        view_btn = self.query_one("#view-btn", Button)
        view_btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "view-btn":
            select = self.query_one("#collection-select", Select)
            if select.value:
                self.app.push_screen(DocumentListScreen(self.client, select.value))

        elif button_id == "create-btn":
            self.app.push_screen(CreateCollectionScreen(self.client))

        elif button_id == "quit-btn":
            self.app.exit()


class CreateCollectionScreen(Screen):
    """Screen for creating a new collection."""

    def __init__(self, client: MongoDBClient):
        super().__init__()
        self.client = client

    def compose(self) -> ComposeResult:
        """Compose the create collection screen."""
        yield Header(show_clock=True)
        yield Container(
            Label("Create New Collection", id="title"),
            Input(placeholder="Collection Name", id="collection-name"),
            Horizontal(
                Button("Create", id="create-btn"),
                Button("Cancel", id="cancel-btn"),
                id="buttons"
            ),
            id="create-collection-screen"
        )
        yield Footer()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key press in the input field."""
        if event.input.id == "collection-name":
            self.create_collection()

    def create_collection(self) -> None:
        """Create a new collection with the given name."""
        collection_name = self.query_one("#collection-name", Input).value
        if collection_name:
            # Check if client is connected
            if not self.client.socket:
                logger.warning("Client socket is not connected, attempting to connect")
                if not self.client.connect():
                    logger.error("Failed to connect to MongoDB service")
                    self.notify("Failed to connect to MongoDB service. Cannot create collection.", severity="error")
                    return
            
            # Create an empty document to initialize the collection
            try:
                self.client.insert(collection_name, {})
                self.notify(f"Collection '{collection_name}' created successfully", severity="success")
                self.app.pop_screen()
                # Refresh the collection list
                collection_screen = self.app.query_one(CollectionSelect)
                collection_screen.load_collections()
            except ConnectionError as e:
                logger.error(f"Connection error creating collection: {e}")
                self.notify("Failed to connect to MongoDB service. Cannot create collection.", severity="error")
            except Exception as e:
                logger.error(f"Error creating collection: {e}", exc_info=True)
                self.notify(f"Error creating collection: {e}", severity="error")
        else:
            self.notify("Please enter a collection name", severity="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "create-btn":
            self.create_collection()
        elif button_id == "cancel-btn":
            self.app.pop_screen()


class DocumentListScreen(Screen):
    """Screen for listing documents in a collection."""

    def __init__(self, client: MongoDBClient, collection: str):
        super().__init__()
        self.client = client
        self.collection = collection
        self.documents = []

    def compose(self) -> ComposeResult:
        """Compose the document list screen."""
        yield Header(show_clock=True)
        yield Container(
            Label(f"Collection: {self.collection}", id="title"),
            DataTable(id="document-table", cursor_type="row"),
            Horizontal(
                Button("View/Edit", id="view-btn", disabled=True),
                Button("Create New", id="create-btn"),
                Button("Delete", id="delete-btn", disabled=True),
                Button("Query", id="query-btn"),
                Button("Back", id="back-btn"),
                id="buttons"
            ),
            id="document-list-screen"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load documents when the screen is mounted."""
        self.load_documents()

    def load_documents(self) -> None:
        """Load documents from the collection."""
        # Disable view and delete buttons when loading documents
        view_btn = self.query_one("#view-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        view_btn.disabled = True
        delete_btn.disabled = True
        
        table = self.query_one("#document-table", DataTable)
        table.clear(columns=True)
        
        # Check if client is connected
        if not self.client.socket:
            logger.warning("Client socket is not connected, attempting to connect")
            if not self.client.connect():
                logger.error("Failed to connect to MongoDB service")
                self.notify("Failed to connect to MongoDB service. UI will continue with limited functionality.", severity="error")
                table.add_column("Status")
                table.add_row("MongoDB connection failed. Cannot load documents.")
                self.documents = []
                return
        
        try:
            self.documents = self.client.find(self.collection, {})
            
            # If no documents, show a message
            if not self.documents:
                table.add_column("Message")
                table.add_row("No documents found in this collection")
                return

            # Get all unique keys from all documents
            all_keys = set()
            for doc in self.documents:
                all_keys.update(doc.keys())

            # Ensure _id is the first column
            columns = ["_id"] + sorted([k for k in all_keys if k != "_id"])

            # Add columns to the table
            for column in columns:
                table.add_column(column)

            # Add rows to the table
            for doc in self.documents:
                row = [str(doc.get(column, "")) for column in columns]
                table.add_row(*row)

        except ConnectionError as e:
            logger.error(f"Connection error loading documents: {e}")
            self.notify("Failed to connect to MongoDB service. UI will continue with limited functionality.", severity="error")
            table.add_column("Status")
            table.add_row("MongoDB connection failed. Cannot load documents.")
            self.documents = []
        except Exception as e:
            logger.error(f"Error loading documents: {e}", exc_info=True)
            self.notify(f"Error loading documents: {e}", severity="error")
            table.add_column("Status")
            table.add_row(f"Error: {str(e)}")
            self.documents = []

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Enable buttons when a row is selected."""
        view_btn = self.query_one("#view-btn", Button)
        delete_btn = self.query_one("#delete-btn", Button)
        view_btn.disabled = False
        delete_btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "view-btn":
            table = self.query_one("#document-table", DataTable)
            if table.cursor_row is not None:
                doc_id = table.get_cell_at((table.cursor_row, 0))
                document = next((d for d in self.documents if str(d.get("_id")) == doc_id), None)
                if document:
                    self.app.push_screen(DocumentEditScreen(self.client, self.collection, document))

        elif button_id == "create-btn":
            self.app.push_screen(DocumentEditScreen(self.client, self.collection, {}))

        elif button_id == "delete-btn":
            table = self.query_one("#document-table", DataTable)
            if table.cursor_row is not None:
                doc_id = table.get_cell_at((table.cursor_row, 0))
                self.confirm_delete(doc_id)

        elif button_id == "query-btn":
            self.app.push_screen(QueryScreen(self.client, self.collection))

        elif button_id == "back-btn":
            self.app.pop_screen()

    def confirm_delete(self, doc_id: str) -> None:
        """Confirm document deletion."""
        def delete_document(confirmed: bool) -> None:
            if confirmed:
                try:
                    count = self.client.delete(self.collection, {"_id": doc_id})
                    self.notify(f"Deleted {count} document(s)")
                    self.load_documents()
                except Exception as e:
                    self.notify(f"Error deleting document: {e}", severity="error")

        self.app.push_screen(
            ConfirmScreen(
                f"Are you sure you want to delete document with ID: {doc_id}?",
                delete_document
            )
        )


class DocumentEditScreen(Screen):
    """Screen for editing a document."""

    def __init__(self, client: MongoDBClient, collection: str, document: Dict[str, Any]):
        super().__init__()
        self.client = client
        self.collection = collection
        self.document = document
        self.is_new = "_id" not in document

    def compose(self) -> ComposeResult:
        """Compose the document edit screen."""
        yield Header(show_clock=True)
        yield Container(
            Label(f"{'Create' if self.is_new else 'Edit'} Document", id="title"),
            TextArea(id="document-editor"),
            Horizontal(
                Button("Save", id="save-btn"),
                Button("Cancel", id="cancel-btn"),
                id="buttons"
            ),
            id="document-edit-screen"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the editor with the document JSON."""
        editor = self.query_one("#document-editor", TextArea)
        editor.text = json.dumps(self.document, indent=2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "save-btn":
            editor = self.query_one("#document-editor", TextArea)
            try:
                updated_doc = json.loads(editor.text)
                
                # Check if client is connected
                if not self.client.socket:
                    logger.warning("Client socket is not connected, attempting to connect")
                    if not self.client.connect():
                        logger.error("Failed to connect to MongoDB service")
                        self.notify("Failed to connect to MongoDB service. Cannot save document.", severity="error")
                        return

                if self.is_new:
                    # Insert new document
                    try:
                        doc_id = self.client.insert(self.collection, updated_doc)
                        self.notify(f"Document created with ID: {doc_id}")
                        
                        # Go back to document list and refresh
                        self.app.pop_screen()
                        document_list = self.app.query_one(DocumentListScreen)
                        document_list.load_documents()
                    except ConnectionError as e:
                        logger.error(f"Connection error inserting document: {e}")
                        self.notify("Failed to connect to MongoDB service. Cannot save document.", severity="error")
                    except Exception as e:
                        logger.error(f"Error inserting document: {e}", exc_info=True)
                        self.notify(f"Error saving document: {e}", severity="error")
                else:
                    # Update existing document
                    try:
                        doc_id = self.document.get("_id")
                        count = self.client.update(self.collection, {"_id": doc_id}, updated_doc)
                        self.notify(f"Updated {count} document(s)")
                        
                        # Go back to document list and refresh
                        self.app.pop_screen()
                        document_list = self.app.query_one(DocumentListScreen)
                        document_list.load_documents()
                    except ConnectionError as e:
                        logger.error(f"Connection error updating document: {e}")
                        self.notify("Failed to connect to MongoDB service. Cannot update document.", severity="error")
                    except Exception as e:
                        logger.error(f"Error updating document: {e}", exc_info=True)
                        self.notify(f"Error updating document: {e}", severity="error")

            except json.JSONDecodeError:
                self.notify("Invalid JSON format", severity="error")
            except Exception as e:
                logger.error(f"Unexpected error in document edit: {e}", exc_info=True)
                self.notify(f"Error: {e}", severity="error")

        elif button_id == "cancel-btn":
            self.app.pop_screen()


class QueryScreen(Screen):
    """Screen for querying documents."""

    def __init__(self, client: MongoDBClient, collection: str):
        super().__init__()
        self.client = client
        self.collection = collection

    def compose(self) -> ComposeResult:
        """Compose the query screen."""
        yield Header(show_clock=True)
        yield Container(
            Label(f"Query Collection: {self.collection}", id="title"),
            Label("Enter Query (JSON format):", id="query-label"),
            TextArea(id="query-editor", language="json"),
            Button("Execute Query", id="execute-btn"),
            Label("Results:", id="results-label"),
            DataTable(id="results-table", cursor_type="row"),
            Button("Back", id="back-btn"),
            id="query-screen"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the query editor."""
        editor = self.query_one("#query-editor", TextArea)
        editor.text = "{}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "execute-btn":
            editor = self.query_one("#query-editor", TextArea)
            table = self.query_one("#results-table", DataTable)
            table.clear(columns=True)
            
            try:
                query = json.loads(editor.text)
                
                # Check if client is connected
                if not self.client.socket:
                    logger.warning("Client socket is not connected, attempting to connect")
                    if not self.client.connect():
                        logger.error("Failed to connect to MongoDB service")
                        self.notify("Failed to connect to MongoDB service. Cannot execute query.", severity="error")
                        table.add_column("Status")
                        table.add_row("MongoDB connection failed. Cannot execute query.")
                        return
                
                try:
                    results = self.client.find(self.collection, query)
                    
                    # If no results, show a message
                    if not results:
                        table.add_column("Message")
                        table.add_row("No documents found matching the query")
                        return

                    # Get all unique keys from all documents
                    all_keys = set()
                    for doc in results:
                        all_keys.update(doc.keys())

                    # Ensure _id is the first column
                    columns = ["_id"] + sorted([k for k in all_keys if k != "_id"])

                    # Add columns to the table
                    for column in columns:
                        table.add_column(column)

                    # Add rows to the table
                    for doc in results:
                        row = [str(doc.get(column, "")) for column in columns]
                        table.add_row(*row)
                
                except ConnectionError as e:
                    logger.error(f"Connection error executing query: {e}")
                    self.notify("Failed to connect to MongoDB service. Cannot execute query.", severity="error")
                    table.add_column("Status")
                    table.add_row("MongoDB connection failed. Cannot execute query.")
                except Exception as e:
                    logger.error(f"Error executing query: {e}", exc_info=True)
                    self.notify(f"Error executing query: {e}", severity="error")
                    table.add_column("Error")
                    table.add_row(f"Error executing query: {str(e)}")

            except json.JSONDecodeError:
                self.notify("Invalid JSON format", severity="error")
                table.add_column("Error")
                table.add_row("Invalid JSON format in query")
            except Exception as e:
                logger.error(f"Unexpected error in query execution: {e}", exc_info=True)
                self.notify(f"Error: {e}", severity="error")
                table.add_column("Error")
                table.add_row(f"Error: {str(e)}")

        elif button_id == "back-btn":
            self.app.pop_screen()


class ConfirmScreen(Screen):
    """Screen for confirming actions."""

    def __init__(self, message: str, callback):
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        """Compose the confirmation screen."""
        yield Container(
            Label(self.message, id="confirm-message"),
            Horizontal(
                Button("Yes", id="yes-btn", variant="primary"),
                Button("No", id="no-btn", variant="error"),
                id="confirm-buttons"
            ),
            id="confirm-screen"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "yes-btn":
            self.app.pop_screen()
            self.callback(True)

        elif button_id == "no-btn":
            self.app.pop_screen()
            self.callback(False)


class TextualizeClient(App):
    """Main Textualize client application."""

    TITLE = "MangaDB"

    CSS = """
    #title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    #collection-screen {
        width: 80;
        height: 35;
        margin: 1 1;
        padding: 1;
        border: solid green;
    }

    #create-collection-screen {
        width: 60;
        height: 10;
        margin: 1 1;
        padding: 1;
        border: solid green;
    }

    #document-list-screen {
        width: 100%;
        height: 100%;
        margin: 1 1;
        padding: 1;
        border: solid green;
    }

    #document-edit-screen {
        width: 100%;
        height: 100%;
        margin: 1 1;
        padding: 1;
        border: solid green;
    }

    #query-screen {
        width: 100%;
        height: 100%;
        margin: 1 1;
        padding: 1;
        border: solid green;
    }

    #confirm-screen {
        width: 60;
        height: 15;
        margin: 1 1;
        padding: 1;
        border: solid red;
        background: $surface;
    }

    #confirm-message {
        text-align: center;
        padding: 1;
    }

    #buttons {
        align: center middle;
        padding: 1;
    }

    Button {
        margin: 2 3;
        padding: 1 2;
    }

    #quit-btn {
        background: $error;
        color: $text;                
        border: heavy $error-lighten-2;
        text-style: bold underline;
    }

    #document-editor {
        height: 20;
        margin: 1;
    }

    #query-editor {
        height: 10;
        margin: 1;
    }

    #results-table {
        height: 20;
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("escape", "pop_screen", "Back", priority=True),
    ]

    def __init__(self, host="localhost", port=27020):
        super().__init__()
        # For domain names (not localhost or IP), use HTTP client
        if host != "localhost" and not self._is_ip_address(host):
            self.client = HTTPClient(host)  # Don't use port when host is a domain
            print(f"Using HTTP client for domain name: {host}")
        else:
            # For localhost or IP addresses, use direct MongoDB client
            if port is not None:
                self.client = MongoDBClient(host, port)
            else:
                self.client = MongoDBClient(host)
            print(f"Using direct MongoDB client for: {host}")
            
    def _is_ip_address(self, host):
        """Check if the host is an IP address."""
        import re
        return re.match(r"^\d+\.\d+\.\d+\.\d+$", host) is not None

    def _ensure_mongo_service_running(self):
        """Check if the service is running by attempting to connect.
        This method handles both MongoDB direct connections and HTTP API connections."""
        logger.info("Checking if service is running")

        # Create data directory if it doesn't exist (for local MongoDB service)
        data_dir = "data"
        if not os.path.exists(data_dir):
            logger.info(f"Creating data directory: {data_dir}")
            os.makedirs(data_dir)

        # Determine if we're using HTTP client or direct MongoDB client
        is_http_client = isinstance(self.client, HTTPClient)
        
        if is_http_client:
            # For HTTP clients (remote servers), just try to connect directly
            logger.info(f"Verifying connection to remote API server at {self.client.base_url}...")
            connection_retries = 3
            
            for i in range(connection_retries):
                logger.debug(f"Connection verification attempt {i+1}/{connection_retries}")
                if self.client.connect():
                    logger.info("Successfully verified connection to remote API server")
                    return True
                else:
                    logger.warning(f"Connection verification attempt {i+1} failed")
                    time.sleep(1)  # Wait before retrying
            
            logger.error(f"Could not connect to remote API server at {self.client.base_url}")
            return False
        else:
            # For direct MongoDB clients, create a test client
            logger.info("Verifying connection to MongoDB service...")
            # Create a test client with the same host and port as the main client
            if hasattr(self.client, 'port') and self.client.port is not None:
                test_client = MongoDBClient(self.client.host, self.client.port)
            else:
                test_client = MongoDBClient(self.client.host)
            connection_retries = 3

            for i in range(connection_retries):
                logger.debug(f"Connection verification attempt {i+1}/{connection_retries}")
                if test_client.connect():
                    logger.info("Successfully verified connection to MongoDB service")
                    test_client.disconnect()
                    logger.info("MongoDB service is running")
                    return True
                else:
                    logger.warning(f"Connection verification attempt {i+1} failed")
                    time.sleep(1)  # Wait before retrying

            if hasattr(self.client, 'port') and self.client.port is not None:
                logger.error(f"Could not connect to MongoDB service at {self.client.host}:{self.client.port}")
            else:
                logger.error(f"Could not connect to MongoDB service at {self.client.host}")
            return False

    def on_mount(self) -> None:
        """Connect to the MongoDB service when the app starts."""
        logger.info("TextualizeClient mounting - initializing MongoDB connection")

        # Check if MongoDB service is running
        logger.debug("Checking if MongoDB service is running")
        if not self._ensure_mongo_service_running():
            if hasattr(self.client, 'port') and self.client.port is not None:
                logger.warning(f"No MangaDB service found at {self.client.host}:{self.client.port}")
                self.notify(f"No MangaDB service found at {self.client.host}:{self.client.port}. UI will load with limited functionality.", severity="warning")
            else:
                logger.warning(f"No MangaDB service found at {self.client.host}")
                self.notify(f"No MangaDB service found at {self.client.host}. UI will load with limited functionality.", severity="warning")
            # Continue loading the UI even if MongoDB service is not available
            return

        # Try to connect with retries
        max_retries = 3
        retry_delay = 1  # seconds
        logger.info(f"Attempting to connect to MangaDB service with {max_retries} retries")

        for attempt in range(max_retries):
            logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
            if self.client.connect():
                logger.info("Successfully connected to MongoDB service")
                break

            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds")
                self.notify(f"Connection attempt {attempt + 1} failed, retrying...", severity="warning")
                time.sleep(retry_delay)
                # Increase delay for next attempt
                retry_delay *= 1.5
        else:
            # All connection attempts failed
            logger.error(f"Failed to connect to MongoDB service after {max_retries} attempts")
            self.notify(f"Failed to connect to MongoDB service after {max_retries} attempts. UI will load with limited functionality.", severity="error")

    def on_unmount(self) -> None:
        """Disconnect from the MongoDB service when the app exits."""
        self.client.disconnect()

    def on_load(self) -> None:
        """Load the initial screen."""
        self.push_screen(CollectionSelect(self.client))


    def action_quit(self) -> None:
        """Quit the application."""
        # Disconnect from the MongoDB service
        self.client.disconnect()

        self.exit()

    def action_pop_screen(self) -> None:
        """Go back to the previous screen."""
        try:
            if len(self.screen_stack) > 1:
                self.pop_screen()
        except IndexError:
            # Handle the case when trying to pop from an empty list
            logger.warning("Attempted to pop screen from empty stack")
            # No need to do anything else, just prevent the error


def main():
    """Run the Textualize client."""
    try:
        # Parse command line arguments
        import argparse
        parser = argparse.ArgumentParser(description="MangaDB Textualize Client")
        parser.add_argument("--host", type=str, default="localhost", help="Host for MongoDB service (default: localhost)")
        parser.add_argument("--port", type=int, help="Port for MongoDB service (default: 27020, omitted for domain names)")
        args = parser.parse_args()

        # Create data directory if it doesn't exist
        import os
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"Creating data directory: {data_dir}")
            os.makedirs(data_dir)

        # Start the app with command line arguments
        if args.port is not None:
            app = TextualizeClient(args.host, args.port)
        else:
            app = TextualizeClient(args.host)
        app.run()
    except Exception as e:
        print(f"Error running Textualize client: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True


if __name__ == "__main__":
    main()
