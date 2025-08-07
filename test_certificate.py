import requests
import webbrowser
import os
import time

def test_certificate_endpoint():
    """
    Test the certificate endpoint by making a request and opening the result in a browser.
    """
    print("Testing certificate endpoint...")
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Parameters for the certificate
    params = {
        "recipient_name": "John Doe",
        "signatory_name": "Jared Odulio",
        "signatory_title": "MangaDB Lead Developer and Creator"
    }
    
    try:
        # Make a request to the certificate endpoint
        response = requests.get(f"{base_url}/certificate", params=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Certificate endpoint returned successfully!")
            
            # Save the HTML response to a temporary file
            temp_file = "temp_certificate.html"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Open the file in the default web browser
            print(f"Opening certificate in browser...")
            webbrowser.open(f"file://{os.path.abspath(temp_file)}")
            
            # Wait a moment before cleaning up
            time.sleep(5)
            
            # Clean up the temporary file
            os.remove(temp_file)
            print("Test completed successfully!")
        else:
            print(f"Error: Certificate endpoint returned status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_certificate_endpoint()