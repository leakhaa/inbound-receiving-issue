# Live Printing System for Warehouse Assistant

## Overview

This system implements real-time printing from the backend to the frontend using Server-Sent Events (SSE). Instead of waiting for the entire process to complete, print statements now appear live in the frontend as they are executed in the backend.

## How It Works

### 1. Backend Implementation (`backend/app.py`)

- **SSE Endpoint**: `/stream-prints` - Streams print outputs to connected clients
- **Global Queue System**: Manages multiple client connections
- **Live Print Capture**: Intercepts print statements and broadcasts them immediately
- **Client Management**: Automatically handles client connections/disconnections

### 2. Frontend Implementation (`static/script.js`)

- **EventSource Connection**: Establishes SSE connection to `/stream-prints`
- **Real-time Updates**: Displays print outputs as they arrive
- **Connection Status**: Shows connection status in the UI
- **Auto-reconnection**: Automatically reconnects if connection is lost

### 3. Print Statement Integration (`backend/scripts/resolver.py`)

- **Live Print Function**: Replaces regular print statements with live broadcasting
- **Fallback Support**: Falls back to regular print if live system unavailable
- **Immediate Feedback**: Users see progress in real-time

## Features

### ✅ Real-time Updates
- Print statements appear immediately in the frontend
- No waiting for entire process completion
- Live progress indication

### ✅ Connection Management
- Automatic client connection handling
- Connection status indicators
- Auto-reconnection on connection loss

### ✅ Visual Feedback
- System messages with distinct styling
- Highlight animation for new messages
- Connection status in header

### ✅ Error Handling
- Graceful fallback to regular print
- Connection error handling
- Automatic reconnection attempts

## Usage

### 1. Start the Backend
```bash
cd backend
python app.py
```

### 2. Open the Frontend
Navigate to `http://localhost:5000` in your browser

### 3. Live Updates
- Print statements from the backend will appear in real-time
- Look for system messages (orange cog icon)
- Connection status shows "Live Updates Active" when working

## Technical Details

### Server-Sent Events (SSE)
- **Protocol**: HTTP-based streaming
- **Reconnection**: Automatic with exponential backoff
- **Keepalive**: 30-second heartbeat messages
- **Headers**: Proper CORS and cache control

### Print Statement Interception
```python
# In resolver.py
try:
    from app import broadcast_print_output
    def live_print(*args, **kwargs):
        import builtins
        builtins.print(*args, **kwargs)  # Regular console output
        output = ' '.join(str(arg) for arg in args)
        broadcast_print_output(output)    # Live frontend output
except ImportError:
    live_print = print  # Fallback
```

### Frontend Connection
```javascript
// In script.js
this.eventSource = new EventSource('/stream-prints');
this.eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'print') {
        this.addSystemMessage(data.message);
    }
};
```

## Testing

### Test Live Printing
```bash
cd backend
python test_live_print.py
```

### Manual Testing
1. Start the Flask app
2. Open the frontend
3. Send a message that triggers backend processing
4. Watch print statements appear in real-time

## Troubleshooting

### Common Issues

1. **No Live Updates**
   - Check browser console for SSE connection errors
   - Verify backend is running
   - Check network connectivity

2. **Connection Drops**
   - System automatically reconnects
   - Check backend logs for errors
   - Verify firewall settings

3. **Print Statements Not Appearing**
   - Ensure `live_print` is used instead of `print`
   - Check import statements in resolver.py
   - Verify SSE endpoint is accessible

### Debug Mode
Enable Flask debug mode to see detailed logs:
```python
app.run(debug=True)
```

## Benefits

1. **Better User Experience**: Users see progress in real-time
2. **Debugging**: Easier to track backend processing
3. **Transparency**: Users know what's happening behind the scenes
4. **Professional Feel**: Modern real-time application behavior

## Future Enhancements

- **Message Filtering**: Filter specific types of print statements
- **Message History**: Store and display message history
- **User Preferences**: Allow users to customize update frequency
- **Rich Formatting**: Support for structured data and formatting

## Security Considerations

- **CORS Headers**: Properly configured for cross-origin requests
- **Input Validation**: All print outputs are sanitized
- **Connection Limits**: Automatic cleanup of disconnected clients
- **Rate Limiting**: Consider implementing if needed

## Performance Notes

- **Memory Usage**: Minimal overhead with queue-based system
- **Network**: Efficient SSE protocol with minimal bandwidth
- **Scalability**: Can handle multiple concurrent clients
- **Resource Cleanup**: Automatic cleanup of disconnected clients
