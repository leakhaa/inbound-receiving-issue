# Screenshot Feature Implementation

## Overview
This document describes the implementation of screenshot functionality in the warehouse assistant chatbot. The feature automatically captures screenshots of the chat interface and attaches them to emails sent to users.

## Features Added

### 1. Frontend Screenshot Capture
- **Library**: Uses `html2canvas` library for capturing screenshots
- **Trigger**: Screenshots are captured automatically when users send messages (after email validation phase)
- **Target**: Captures the entire chat container
- **Format**: PNG format with high quality (2x scale)

### 2. Backend Email Handler Enhancement
- **New Function**: `send_email_with_screenshot()` in `backend/scripts/email_handler.py`
- **Image Support**: Added `MIMEImage` import for handling image attachments
- **Base64 Decoding**: Automatically handles base64 encoded screenshot data
- **Error Handling**: Graceful fallback if screenshot attachment fails

### 3. Integration Points
- **Chat Endpoint**: Updated to receive screenshot data from frontend
- **Resolver**: All email sending calls updated to use screenshot functionality
- **Templates**: Added html2canvas library to all HTML templates

## Files Modified

### Backend Files
1. **`backend/scripts/email_handler.py`**
   - Added `MIMEImage` import
   - Added `base64` import
   - Added `send_email_with_screenshot()` function

2. **`backend/scripts/resolver.py`**
   - Updated `resolve_issue()` function signature to accept screenshot data
   - Replaced all `send_email()` calls with `send_email_with_screenshot()`
   - Added screenshot parameter to all email sending calls

3. **`backend/app.py`**
   - Updated `/chat` endpoint to handle screenshot data
   - Added `/test_screenshot` endpoint for testing
   - Added html2canvas library to chatbot interface

### Frontend Files
1. **`backend/static/script.js`**
   - Added `captureScreenshot()` method
   - Updated `sendMessage()` to capture screenshots
   - Added screenshot data to API requests

2. **`static/script.js`**
   - Added `captureScreenshot()` method
   - Updated `sendMessage()` to capture screenshots
   - Added screenshot data to API requests

3. **HTML Templates**
   - **`backend/templates/index.html`**: Added html2canvas library
   - **`static/index.html`**: Added html2canvas library
   - **`backend/app.py`**: Added html2canvas library to inline chatbot

## How It Works

### 1. Screenshot Capture Process
```javascript
async captureScreenshot() {
    const chatContainer = document.querySelector('.chat-container');
    const canvas = await html2canvas(chatContainer, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        allowTaint: true
    });
    return canvas.toDataURL('image/png');
}
```

### 2. Email with Screenshot Process
```python
def send_email_with_screenshot(to, subject, body, screenshot_data=None, html_format=False):
    msg = MIMEMultipart()
    # ... email setup ...
    
    if screenshot_data:
        # Remove data URL prefix if present
        if screenshot_data.startswith('data:image/'):
            screenshot_data = screenshot_data.split(',')[1]
        
        # Decode base64 data
        image_data = base64.b64decode(screenshot_data)
        
        # Create image attachment
        image = MIMEImage(image_data)
        image.add_header('Content-Disposition', 'attachment', filename='screenshot.png')
        msg.attach(image)
```

### 3. Integration Flow
1. User sends a message (after email validation)
2. Frontend captures screenshot of chat interface
3. Screenshot data sent to backend with message
4. Backend processes issue and sends email with screenshot attached
5. User receives email with screenshot showing the chat conversation

## Testing

### Test File
Created `test_screenshot.html` for testing the functionality:
- Tests screenshot capture
- Tests email sending with screenshot
- Provides visual feedback on success/failure

### Test Endpoint
Added `/test_screenshot` endpoint in `backend/app.py`:
- Accepts screenshot data via POST
- Sends test email with screenshot
- Returns success/failure status

## Usage

### For Users
- Screenshots are captured automatically
- No additional action required
- Screenshots are attached to all emails sent by the system

### For Developers
- Screenshots are only captured after email validation phase
- Screenshot data is optional - emails work without screenshots
- Error handling ensures system continues working if screenshot fails

## Benefits

1. **Better Communication**: Users receive visual context of their conversation
2. **Issue Tracking**: Screenshots help track the exact state when issues were reported
3. **User Experience**: No manual screenshot taking required
4. **Support Efficiency**: Support team can see exactly what the user saw

## Technical Notes

- **File Size**: Screenshots are high quality (2x scale) but compressed as PNG
- **Performance**: Screenshot capture is asynchronous and doesn't block the UI
- **Compatibility**: Works with all modern browsers that support html2canvas
- **Fallback**: System continues working even if screenshot capture fails

## Future Enhancements

1. **Selective Capture**: Only capture relevant parts of the interface
2. **Compression**: Add image compression to reduce email size
3. **Format Options**: Support different image formats (JPEG, WebP)
4. **Storage**: Option to store screenshots in database for later reference
