# MangaDB Certified Developer Examination Workflow

This document describes the MangaDB Certified Developer Examination workflow, including the PayPal payment integration.

## Overview

The MangaDB Certified Developer Examination allows users to demonstrate their proficiency in MangaDB development. The workflow includes:

1. Registration for the examination
2. Taking the examination
3. Payment processing through PayPal
4. Certificate generation

## Workflow Steps

### 1. Registration and Examination

Users start by visiting the `/exam` endpoint, where they:

- Enter their full name and email
- Take a timed examination (30 minutes)
- Answer multiple-choice and short-answer questions about MangaDB
- Submit their answers for automatic grading

The examination tests knowledge of:
- NoSQL database concepts
- MangaDB document storage
- Custom wire protocol implementation
- Collection management
- Query operations

### 2. Examination Results

After submission:

- The system automatically grades the examination
- A passing score is 70% or higher
- Results are stored in the `exam_attempts` collection
- If passed, the user is presented with a payment option through PayPal

### 3. Payment Processing

For users who pass the examination:

- The PayPal payment button is displayed
- The certification fee is $25.00 USD
- PayPal handles the payment processing securely
- After successful payment, the payment status is updated in the database

### 4. Certificate Generation

Upon successful payment:

- The user is redirected to the certificate page
- A personalized certificate is generated with the user's name
- The certificate includes the current date and signatory information
- The certificate status is marked as issued in the database

## Technical Implementation

### Data Model

The `exam_attempts` collection stores:

```json
{
  "full_name": "User's full name",
  "email": "user@example.com",
  "score": 85,
  "passed": true,
  "payment_status": "completed",
  "payment_id": "PAYPAL-123456789",
  "certificate_issued": true,
  "timestamp": "2025-08-07T10:38:00"
}
```

### API Endpoints

- `GET /exam` - Serves the examination page
- `POST /api/exam-results` - Saves examination results
- `POST /api/update-payment` - Updates payment status
- `GET /certificate` - Generates the certificate

## PayPal Integration Setup

To set up PayPal integration:

1. Create a PayPal Developer account at [developer.paypal.com](https://developer.paypal.com)
2. Create a new application to get your client ID and secret
3. Replace the test client ID in the exam.html template:

```html
<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&currency=USD"></script>
```

4. For production, update the PayPal SDK script to use your live client ID

### Testing the Integration

For testing purposes:

- Use the PayPal Sandbox environment
- Create sandbox buyer and seller accounts
- Use the test script `test_certification_workflow.py` to verify the workflow

## Security Considerations

- Payment verification is performed before certificate issuance
- User data is stored securely in the MongoDB database
- PayPal handles sensitive payment information

## Customization

The certification workflow can be customized by:

- Modifying the examination questions in `exam.html`
- Adjusting the passing score threshold
- Changing the certification fee
- Updating the certificate template in `certificate.html`