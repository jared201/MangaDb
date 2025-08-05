from textualize_client import HTTPClient

# Create an HTTP client instance
client = HTTPClient("example.com")

# Test that accessing the socket attribute doesn't raise an AttributeError
if hasattr(client, 'socket'):
    print("SUCCESS: Socket attribute exists")
    print(f"Socket value: {client.socket}")
else:
    print("ERROR: Socket attribute does not exist")

print("Test completed successfully!")