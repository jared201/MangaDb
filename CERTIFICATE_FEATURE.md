# MangaDB Certificate Feature

This document describes the MangaDB Certified Developer certificate feature added to the MangaDB application.

## Overview

The certificate feature allows users to generate a professional-looking MangaDB Certified Developer certificate. The certificate is presented as an HTML page that can be printed or saved as a PDF using the browser's print functionality.

## Usage

### Web Interface

To generate a certificate through the web interface, navigate to:

```
https://mangadb-bwmu.onrender.com/certificate
```

By default, this will generate a certificate for "John Doe" with "Jared Odulio" as the signatory.

### Custom Certificate

You can customize the certificate by providing query parameters:

```
https://mangadb-bwmu.onrender.com/certificate?recipient_name=Jane%20Smith&signatory_name=Jared%20Odulio&signatory_title=MangaDB%20Lead%20Developer
```

Available parameters:
- `recipient_name`: The name of the person receiving the certificate (default: "John Doe")
- `signatory_name`: The name of the person signing the certificate (default: "Jared Odulio")
- `signatory_title`: The title of the signatory (default: "MangaDB Lead Developer")

## Saving as PDF or PNG

To save the certificate as a PDF:
1. Open the certificate URL in a web browser
2. Use the browser's print functionality (Ctrl+P or Cmd+P)
3. Select "Save as PDF" as the destination
4. Click "Save"

To save as PNG:
1. Open the certificate URL in a web browser
2. Take a screenshot of the certificate
   - On Windows: Use the Snipping Tool or press Windows+Shift+S
   - On Mac: Press Cmd+Shift+4
   - On Linux: Use a screenshot tool like GNOME Screenshot
3. Save the screenshot as a PNG file

## Testing

A test script is provided to verify the certificate functionality:

```bash
python test_certificate.py
```

This script will:
1. Make a request to the certificate endpoint
2. Save the response to a temporary HTML file
3. Open the file in your default web browser
4. Clean up the temporary file after 5 seconds

## Implementation Details

The certificate feature consists of:
1. An HTML template (`templates/certificate.html`) with CSS styling
2. A FastAPI endpoint in `main.py` that renders the template with the provided parameters
3. The current date is automatically added to the certificate

The certificate design includes:
- A professional border and layout
- The MangaDB logo and branding
- A signature area for the signatory
- A decorative seal

## Future Enhancements

Potential future enhancements for the certificate feature:
- Add a unique certificate ID or QR code for verification
- Implement direct PDF generation on the server
- Add more customization options (colors, layout, etc.)
- Create an admin interface for managing certificates