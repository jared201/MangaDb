#!/usr/bin/env python3
"""
Test script to verify that the HTTPClient is properly initialized without using the port parameter for domain names.
"""

import sys
import logging
from textualize_client import HTTPClient, TextualizeClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_domain_client')

def test_http_client_initialization():
    """Test that HTTPClient ignores port parameter."""
    # Test direct initialization
    client1 = HTTPClient("example.com", 12345)
    print(f"HTTPClient initialized with host='example.com', port=12345")
    print(f"  client1.host = {client1.host}")
    print(f"  client1.port = {client1.port}")
    print(f"  client1.base_url = {client1.base_url}")
    
    # Test initialization without port
    client2 = HTTPClient("example.com")
    print(f"HTTPClient initialized with host='example.com', no port")
    print(f"  client2.host = {client2.host}")
    print(f"  client2.port = {client2.port}")
    print(f"  client2.base_url = {client2.base_url}")
    
    # Verify both clients have the same base_url
    assert client1.base_url == client2.base_url, "base_url should be the same regardless of port parameter"
    print("✓ Both clients have the same base_url")
    
    # Verify port is None for both clients
    assert client1.port is None, "port should be None for HTTPClient"
    assert client2.port is None, "port should be None for HTTPClient"
    print("✓ Both clients have port=None")

def test_textualize_client_initialization():
    """Test that TextualizeClient doesn't pass port to HTTPClient for domain names."""
    # Test with domain name
    client1 = TextualizeClient("example.com", 12345)
    print(f"TextualizeClient initialized with host='example.com', port=12345")
    print(f"  client1.client.host = {client1.client.host}")
    print(f"  client1.client.port = {client1.client.port}")
    
    # Verify port is None for domain client
    assert client1.client.port is None, "port should be None for domain client"
    print("✓ Domain client has port=None")
    
    # Test with localhost
    client2 = TextualizeClient("localhost", 12345)
    print(f"TextualizeClient initialized with host='localhost', port=12345")
    print(f"  client2.client.host = {client2.client.host}")
    print(f"  client2.client.port = {client2.client.port}")
    
    # Verify port is set for localhost client
    assert client2.client.port == 12345, "port should be set for localhost client"
    print("✓ Localhost client has port=12345")
    
    # Test with IP address
    client3 = TextualizeClient("127.0.0.1", 12345)
    print(f"TextualizeClient initialized with host='127.0.0.1', port=12345")
    print(f"  client3.client.host = {client3.client.host}")
    print(f"  client3.client.port = {client3.client.port}")
    
    # Verify port is set for IP client
    assert client3.client.port == 12345, "port should be set for IP client"
    print("✓ IP client has port=12345")

if __name__ == "__main__":
    print("Testing HTTPClient initialization...")
    test_http_client_initialization()
    print("\nTesting TextualizeClient initialization...")
    test_textualize_client_initialization()
    print("\nAll tests passed!")