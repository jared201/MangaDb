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
from typing import Dict, List, Any, Optional
from mongo_db_client import MongoDBClient

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
                        # Try to ensure the service is running
                        logger.warning("Connection failed, checking if MongoDB service is running")
                        app = self.app
                        if hasattr(app, '_ensure_mongo_service_running'):
                            if not app._ensure_mongo_service_running():
                                logger.error("Failed to start MongoDB service")
                                self.notify("Failed to start MongoDB service. Check the logs for details.", severity="error")
                                self.collections = []
                                break

                            # Try connecting again after ensuring service is running
                            logger.info("Retrying connection after ensuring service is running")
                            if not self.client.connect():
                                logger.error("Failed to connect to MongoDB service even after restart")
                                self.notify("Failed to connect to MongoDB service. Check if the service is running.", severity="error")
                                self.collections = []
                                break
                        else:
                            logger.error("Failed to connect to MongoDB service")
                            self.notify("Failed to connect to MongoDB service. Check if the service is running.", severity="error")
                            self.collections = []
                            break

                # Get collections
                logger.debug("Calling list_collections()")
                self.collections = self.client.list_collections()
                logger.info(f"Successfully loaded {len(self.collections)} collections")
                break  # Success, exit the retry loop

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
                    self.notify(f"Error loading collections: {e}", severity="error")
                    self.collections = []
            except Exception as e:
                logger.error(f"Unexpected error loading collections: {e}", exc_info=True)
                self.notify(f"Error loading collections: {e}", severity="error")
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
            # Create an empty document to initialize the collection
            try:
                self.client.insert(collection_name, {})
                self.app.pop_screen()
                # Refresh the collection list
                collection_screen = self.app.query_one(CollectionSelect)
                collection_screen.load_collections()
            except Exception as e:
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
        try:
            self.documents = self.client.find(self.collection, {})

            table = self.query_one("#document-table", DataTable)
            table.clear(columns=True)

            # Disable view and delete buttons when loading documents
            view_btn = self.query_one("#view-btn", Button)
            delete_btn = self.query_one("#delete-btn", Button)
            view_btn.disabled = True
            delete_btn.disabled = True

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

        except Exception as e:
            self.notify(f"Error loading documents: {e}", severity="error")

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

                if self.is_new:
                    # Insert new document
                    doc_id = self.client.insert(self.collection, updated_doc)
                    self.notify(f"Document created with ID: {doc_id}")
                else:
                    # Update existing document
                    doc_id = self.document.get("_id")
                    count = self.client.update(self.collection, {"_id": doc_id}, updated_doc)
                    self.notify(f"Updated {count} document(s)")

                # Go back to document list and refresh
                self.app.pop_screen()
                document_list = self.app.query_one(DocumentListScreen)
                document_list.load_documents()

            except json.JSONDecodeError:
                self.notify("Invalid JSON format", severity="error")
            except Exception as e:
                self.notify(f"Error saving document: {e}", severity="error")

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
            try:
                query = json.loads(editor.text)
                results = self.client.find(self.collection, query)

                table = self.query_one("#results-table", DataTable)
                table.clear(columns=True)

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

            except json.JSONDecodeError:
                self.notify("Invalid JSON format", severity="error")
            except Exception as e:
                self.notify(f"Error executing query: {e}", severity="error")

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

    mongo_service_process = None

    def __init__(self):
        super().__init__()
        self.client = MongoDBClient()

    def _is_mongo_service_running(self):
        """Check if the MongoDB service process is running."""
        logger.debug("Checking if MongoDB service process is running")

        if TextualizeClient.mongo_service_process is None:
            logger.debug("MongoDB service process is None")
            return False

        # Check if the process is still running
        poll_result = TextualizeClient.mongo_service_process.poll()
        if poll_result is not None:
            # Process has terminated
            logger.warning(f"MongoDB service process has terminated with exit code: {poll_result}")
            TextualizeClient.mongo_service_process = None
            return False

        logger.debug("MongoDB service process is running")
        return True

    def _ensure_mongo_service_running(self):
        """Ensure the MongoDB service is running, start it if not."""
        logger.info("Ensuring MongoDB service is running")

        if not self._is_mongo_service_running():
            logger.info("MongoDB service is not running, attempting to start it")

            # Create data directory if it doesn't exist
            data_dir = "data"
            if not os.path.exists(data_dir):
                logger.info(f"Creating data directory: {data_dir}")
                os.makedirs(data_dir)

            # Get the full path to the service script
            service_script = "mongo_db_service.py"
            service_path = os.path.abspath(service_script)
            logger.info(f"Starting MongoDB service from: {service_path}")

            try:
                # Start the MongoDB service in a separate process
                logger.debug(f"Executing: {sys.executable} {service_script}")

                # Use shell=True on Windows to avoid console window
                if os.name == 'nt':
                    TextualizeClient.mongo_service_process = subprocess.Popen(
                        f'"{sys.executable}" "{service_path}"',
                        shell=True,
                        # Redirect output to avoid blocking
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        # Use CREATE_NEW_PROCESS_GROUP on Windows to ensure the process can be terminated properly
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    TextualizeClient.mongo_service_process = subprocess.Popen(
                        [sys.executable, service_script],
                        # Redirect output to avoid blocking
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )

                # Log process ID
                pid = TextualizeClient.mongo_service_process.pid
                logger.info(f"MongoDB service process started with PID: {pid}")

                # Wait for the service to start
                wait_time = 5  # Increased from 2 to 5 seconds to give more time for initialization
                logger.debug(f"Waiting {wait_time} seconds for service to initialize")
                time.sleep(wait_time)

                # Check if the process started successfully
                if not self._is_mongo_service_running():
                    logger.error("MongoDB service failed to start")

                    # Try to get error output from the process
                    if TextualizeClient.mongo_service_process:
                        stderr_output = TextualizeClient.mongo_service_process.stderr.read()
                        if stderr_output:
                            logger.error(f"MongoDB service error output: {stderr_output.decode('utf-8')}")

                    return False

                # Verify that the service is accepting connections
                logger.info("MongoDB service process is running, verifying connection...")
                test_client = MongoDBClient()
                connection_retries = 3

                for i in range(connection_retries):
                    logger.debug(f"Connection verification attempt {i+1}/{connection_retries}")
                    if test_client.connect():
                        logger.info("Successfully verified connection to MongoDB service")
                        test_client.disconnect()
                        logger.info("MongoDB service started successfully")
                        return True
                    else:
                        logger.warning(f"Connection verification attempt {i+1} failed")
                        time.sleep(1)  # Wait before retrying

                logger.error("MongoDB service process is running but not accepting connections")
                return False

            except Exception as e:
                logger.error(f"Error starting MongoDB service: {e}", exc_info=True)
                return False

        logger.debug("MongoDB service is already running")
        return True

    def on_mount(self) -> None:
        """Connect to the MongoDB service when the app starts."""
        logger.info("TextualizeClient mounting - initializing MongoDB connection")

        # Ensure MongoDB service is running
        logger.debug("Ensuring MongoDB service is running")
        if not self._ensure_mongo_service_running():
            logger.error("Failed to start MongoDB service")
            self.notify("Failed to start MongoDB service", severity="error")
            return

        # Try to connect with retries
        max_retries = 5
        retry_delay = 1  # seconds
        logger.info(f"Attempting to connect to MongoDB service with {max_retries} retries")

        for attempt in range(max_retries):
            logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
            if self.client.connect():
                logger.info("Successfully connected to MongoDB service")
                break

            # Check if MongoDB service is still running
            logger.debug("Checking if MongoDB service is still running")
            if not self._is_mongo_service_running():
                logger.warning("MongoDB service is not running, attempting to restart")
                # Try to restart the service
                if not self._ensure_mongo_service_running():
                    logger.error("MongoDB service stopped unexpectedly and could not be restarted")
                    self.notify("MongoDB service stopped unexpectedly and could not be restarted", severity="error")
                    return

            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds")
                self.notify(f"Connection attempt {attempt + 1} failed, retrying...", severity="warning")
                time.sleep(retry_delay)
                # Increase delay for next attempt
                retry_delay *= 1.5
        else:
            # All connection attempts failed
            logger.error(f"Failed to connect to MongoDB service after {max_retries} attempts")
            self.notify(f"Failed to connect to MongoDB service after {max_retries} attempts", severity="error")

    def on_unmount(self) -> None:
        """Disconnect from the MongoDB service when the app exits."""
        self.client.disconnect()

        # Terminate the MongoDB service process
        self._terminate_mongo_service()

    def on_load(self) -> None:
        """Load the initial screen."""
        self.push_screen(CollectionSelect(self.client))

    def _terminate_mongo_service(self):
        """Terminate the MongoDB service process safely."""
        if TextualizeClient.mongo_service_process:
            try:
                # Try to terminate gracefully first
                TextualizeClient.mongo_service_process.terminate()

                # Wait for up to 3 seconds for the process to terminate
                for _ in range(30):
                    if TextualizeClient.mongo_service_process.poll() is not None:
                        # Process has terminated
                        break
                    time.sleep(0.1)
                else:
                    # Process didn't terminate, force kill it
                    if os.name == 'nt':
                        # On Windows
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(TextualizeClient.mongo_service_process.pid)])
                    else:
                        # On Unix
                        TextualizeClient.mongo_service_process.kill()
            except Exception as e:
                print(f"Error terminating MangaDB service: {e}")
            finally:
                TextualizeClient.mongo_service_process = None

    def action_quit(self) -> None:
        """Quit the application."""
        # Disconnect from the MongoDB service
        self.client.disconnect()

        # Terminate the MongoDB service process
        self._terminate_mongo_service()

        self.exit()

    def action_pop_screen(self) -> None:
        """Go back to the previous screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()


def main():
    """Run the Textualize client."""
    mongo_process = None
    try:
        # Start MongoDB service manually before creating the app
        # This ensures the service is running before the app tries to connect
        import subprocess
        import os
        import sys
        import time
        import atexit

        # Create data directory if it doesn't exist
        data_dir = "data"
        if not os.path.exists(data_dir):
            print(f"Creating data directory: {data_dir}")
            os.makedirs(data_dir)

        # Start MongoDB service
        service_script = "mongo_db_service.py"
        service_path = os.path.abspath(service_script)
        print(f"Starting MongoDB service from: {service_path}")

        # Use shell=True on Windows to avoid console window
        if os.name == 'nt':
            mongo_process = subprocess.Popen(
                f'"{sys.executable}" "{service_path}"',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            mongo_process = subprocess.Popen(
                [sys.executable, service_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

        # Register function to terminate MongoDB service on exit
        def terminate_mongo_service():
            if mongo_process:
                print("Terminating MangaDB service...")
                try:
                    if os.name == 'nt':
                        # On Windows
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(mongo_process.pid)])
                    else:
                        # On Unix
                        mongo_process.terminate()
                        mongo_process.wait(timeout=5)
                except Exception as e:
                    print(f"Error terminating MangaDB service: {e}")

        # Register the termination function to be called on exit
        atexit.register(terminate_mongo_service)

        # Wait for service to start
        print("Waiting for MongoDB service to start...")
        time.sleep(5)

        # Now start the app
        app = TextualizeClient()
        # Store the mongo_process in the app for proper cleanup
        app.mongo_process = mongo_process
        app.run()
    except Exception as e:
        print(f"Error running Textualize client: {e}")
        import traceback
        traceback.print_exc()

        # Ensure MongoDB service is terminated on error
        if mongo_process:
            print("Terminating MangaDB service due to error...")
            try:
                if os.name == 'nt':
                    # On Windows
                    subprocess.call(['taskkill', '/F', '/T', '/PID', str(mongo_process.pid)])
                else:
                    # On Unix
                    mongo_process.terminate()
                    mongo_process.wait(timeout=5)
            except Exception as cleanup_error:
                print(f"Error terminating MangaDB service: {cleanup_error}")

        return False
    return True


if __name__ == "__main__":
    main()
