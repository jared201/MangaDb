import requests
import webbrowser
import os
import time
import json

def test_certification_workflow():
    """
    Test the complete MangaDB Certified Developer Examination workflow.
    This script simulates:
    1. Submitting exam results
    2. Processing a payment
    3. Generating a certificate
    """
    print("Testing MangaDB Certified Developer Examination workflow...")
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    # Step 1: Open the examination page in a browser
    print("Opening examination page in browser...")
    webbrowser.open(f"{base_url}/exam")
    
    # Wait for user to review the page
    input("Press Enter after reviewing the examination page...")
    
    # Step 2: Simulate submitting exam results
    print("\nSimulating exam submission...")
    
    exam_data = {
        "full_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "score": 85,
        "passed": True,
        "payment_status": "pending",
        "certificate_issued": False,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    try:
        # Submit exam results
        response = requests.post(f"{base_url}/api/exam-results", json=exam_data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Exam results submitted successfully!")
            result_id = response.json().get("id")
            print(f"Exam result ID: {result_id}")
        else:
            print(f"Error: Exam submission returned status code {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"Error submitting exam results: {str(e)}")
        return
    
    # Step 3: Simulate PayPal payment
    print("\nSimulating PayPal payment...")
    
    payment_data = {
        "email": "jane.smith@example.com",
        "payment_id": "PAYPAL-123456789",
        "payment_status": "completed"
    }
    
    try:
        # Update payment status
        response = requests.post(f"{base_url}/api/update-payment", json=payment_data)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Payment status updated successfully!")
        else:
            print(f"Error: Payment update returned status code {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"Error updating payment status: {str(e)}")
        return
    
    # Step 4: Generate and view certificate
    print("\nGenerating certificate...")
    
    certificate_params = {
        "recipient_name": "Jane Smith",
        "payment_id": "PAYPAL-123456789"
    }
    
    try:
        # Generate certificate
        response = requests.get(f"{base_url}/certificate", params=certificate_params)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Certificate generated successfully!")
            
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
        else:
            print(f"Error: Certificate generation returned status code {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"Error generating certificate: {str(e)}")
        return
    
    # Step 5: Verify exam_attempts collection
    print("\nVerifying exam_attempts collection...")
    
    try:
        # Get all documents in the exam_attempts collection
        response = requests.get(f"{base_url}/collections/exam_attempts")
        
        # Check if the request was successful
        if response.status_code == 200:
            documents = response.json().get("documents", [])
            print(f"Found {len(documents)} documents in exam_attempts collection")
            
            # Find our test document
            for doc in documents:
                if doc.get("email") == "jane.smith@example.com":
                    print("\nFound test document:")
                    print(json.dumps(doc, indent=2))
                    
                    # Verify payment status and certificate issuance
                    if doc.get("payment_status") == "completed" and doc.get("certificate_issued") == True:
                        print("\n✅ Test passed: Payment status and certificate issuance verified!")
                    else:
                        print("\n❌ Test failed: Payment status or certificate issuance not updated correctly")
                    break
            else:
                print("Test document not found in exam_attempts collection")
        else:
            print(f"Error: Collection query returned status code {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"Error querying exam_attempts collection: {str(e)}")
        return
    
    print("\nCertification workflow test completed!")

if __name__ == "__main__":
    test_certification_workflow()