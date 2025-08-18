# 🤖 AI-Powered Email System

## Overview
The warehouse management system now features **AI-generated email content** instead of predefined messages. This provides dynamic, contextual, and professional email communications while maintaining all existing functionality including screenshot attachments.

## ✨ Key Features

### 🔄 **Dynamic Content Generation**
- **AI-powered messages** that adapt to specific contexts and details
- **Contextual responses** based on actual data and scenarios
- **Professional tone** that maintains business standards
- **Personalized content** using user email and specific identifiers

### 📧 **Smart Email Contexts**
- **ASN Operations**: Found, Triggered, Failed, Pending
- **PO Operations**: Found, Triggered, Error, Timeout
- **Pallet Operations**: Found, Resolved, Missing, Error
- **Quantity Mismatch**: Detection, Resolution, Investigation
- **Error Handling**: Specific error messages with helpful guidance

### 🖼️ **Screenshot Integration**
- **All emails include screenshots** as before
- **HTML formatting** preserved for data tables
- **Visual context** maintained for better understanding

## 🏗️ Architecture

### Core Functions

#### 1. `generate_ai_email_content(context, details, user_email)`
```python
def generate_ai_email_content(context: str, details: dict, user_email: str = None) -> str:
    """
    Generate AI-powered email content based on context and details
    
    Args:
        context: The email context (e.g., "ASN Found", "PO Triggered")
        details: Dictionary containing relevant details
        user_email: User's email address for personalization
    
    Returns:
        AI-generated email content
    """
```

#### 2. `send_ai_email_with_screenshot(user_email, subject, context, details, screenshot_data, html_format)`
```python
def send_ai_email_with_screenshot(user_email: str, subject: str, context: str, 
                                 details: dict, screenshot_data: str = None, 
                                 html_format: bool = False):
    """
    Send email with AI-generated content and screenshot
    
    Args:
        user_email: Recipient email address
        subject: Email subject line
        context: Context for AI content generation
        details: Details dictionary for AI content
        screenshot_data: Screenshot data (optional)
        html_format: Whether to format as HTML
    """
```

### AI Prompt Structure
The system uses carefully crafted prompts to ensure consistent, professional output:

```
You are a professional warehouse management system assistant. Generate a clear, professional email message for the following context:

Context: {context}
Details: {details}
User Email: {user_email}

Requirements:
1. Be professional but friendly
2. Include all relevant details from the context
3. Use clear, concise language
4. If it's an error, be helpful and suggest next steps
5. If it's a success, be encouraging
6. If it's a request to SAP, be specific about what's needed
7. Keep it under 3-4 sentences
8. Use proper business email format

Generate only the email body content (no subject line or greetings):
```

## 🔄 Migration from Predefined Messages

### Before (Predefined)
```python
# Old way - static messages
send_email_with_screenshot(user_email, "ASN Found", 
    f"ASN {asn} already interfaced into the wms system.<br><br>{html}", 
    screenshot_data, html_format=True)
```

### After (AI-Generated)
```python
# New way - AI-powered dynamic content
send_ai_email_with_screenshot(user_email, "ASN Found in the wms system", 
    "ASN Found", {"asn_id": asn, "html": html}, 
    screenshot_data, html_format=True)
```

## 📋 Usage Examples

### 1. ASN Found Scenario
```python
# Context and details
context = "ASN Found"
details = {
    "asn_id": "01234",
    "html": "<table>...</table>",
    "status": "active"
}

# Send AI-powered email
send_ai_email_with_screenshot(
    user_email="user@company.com",
    subject="ASN Found in WMS System",
    context=context,
    details=details,
    screenshot_data=screenshot_data,
    html_format=True
)
```

### 2. PO Triggered Scenario
```python
# Context and details
context = "PO Triggered"
details = {
    "po_id": "2123456789",
    "sap_status": "success",
    "timestamp": "2024-01-15 10:30:00"
}

# Send AI-powered email
send_ai_email_with_screenshot(
    user_email="user@company.com",
    subject="PO Successfully Triggered",
    context=context,
    details=details,
    screenshot_data=screenshot_data
)
```

### 3. Error Handling
```python
# Context and details
context = "Error"
details = {
    "message": "Database connection failed",
    "severity": "high",
    "component": "PO validation"
}

# Send AI-powered email
send_ai_email_with_screenshot(
    user_email="user@company.com",
    subject="System Error Alert",
    context=context,
    details=details,
    screenshot_data=screenshot_data
)
```

## 🛡️ Fallback System

### AI Unavailable
If the AI system is unavailable, the system automatically falls back to predefined messages:

```python
try:
    # Try to use AI
    from app import chat_with_ai
    ai_content = chat_with_ai(prompt)
except ImportError:
    # Fallback to predefined messages
    fallback_messages = {
        "ASN Found": f"ASN {details.get('asn_id', 'N/A')} has been successfully found in the WMS system...",
        "PO Triggered": f"PO {details.get('po_id', 'N/A')} has been successfully triggered by SAP...",
        # ... more fallback messages
    }
    return fallback_messages.get(context, f"Status update: {context}")
```

### Predefined Fallback Messages
- **ASN Found**: "ASN {asn_id} has been successfully found in the WMS system. You can now proceed with receiving operations."
- **PO Triggered**: "PO {po_id} has been successfully triggered by SAP and is now available in the system."
- **Error**: "An error occurred: {message}. Please contact support if this persists."

## 🧪 Testing

### Test Script
Run the test script to verify AI email functionality:

```bash
cd backend
python test_ai_emails.py
```

### Test Cases
The test script covers:
- ASN Found scenarios
- PO Triggered scenarios
- Quantity Mismatch scenarios
- Error handling scenarios

## 🔧 Configuration

### AI Integration
The system automatically detects and uses the AI system if available:

```python
# Automatic AI detection
try:
    from app import chat_with_ai
    # Use AI for content generation
except ImportError:
    # Fallback to predefined messages
```

### Customization
You can customize the AI prompts by modifying the `generate_ai_email_content` function:

```python
# Customize the AI prompt
prompt = f"""
Your custom prompt here...
Context: {context}
Details: {details}
...
"""
```

## 📊 Benefits

### 1. **Dynamic Content**
- Messages adapt to specific situations
- Context-aware responses
- Personalized communication

### 2. **Professional Quality**
- Consistent business tone
- Clear and concise language
- Helpful error guidance

### 3. **Maintainability**
- No need to update predefined messages
- Automatic context adaptation
- Centralized AI logic

### 4. **User Experience**
- More engaging and relevant content
- Better understanding of system status
- Professional communication standards

## 🚀 Future Enhancements

### Planned Features
- **Multi-language support** for international warehouses
- **Tone customization** (formal, casual, technical)
- **Template learning** from user feedback
- **Advanced context analysis** for better message relevance

### Integration Possibilities
- **Slack/Teams integration** with AI-generated notifications
- **SMS alerts** with AI-optimized content
- **Voice notifications** using text-to-speech
- **Chatbot responses** with consistent AI messaging

## 🔍 Troubleshooting

### Common Issues

#### 1. AI Not Available
**Problem**: AI system returns ImportError
**Solution**: System automatically falls back to predefined messages

#### 2. Content Too Long
**Problem**: AI generates overly verbose content
**Solution**: Adjust prompt requirements for conciseness

#### 3. Inconsistent Tone
**Problem**: AI tone varies between messages
**Solution**: Refine prompt requirements for consistency

### Debug Mode
Enable debug logging to see AI generation process:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### Function Signatures

```python
# Generate AI content
generate_ai_email_content(context: str, details: dict, user_email: str = None) -> str

# Send AI-powered email
send_ai_email_with_screenshot(user_email: str, subject: str, context: str, 
                             details: dict, screenshot_data: str = None, 
                             html_format: bool = False) -> None
```

### Return Values
- **AI Content**: Generated email body text
- **Fallback Content**: Predefined message if AI unavailable
- **Email Status**: Success/failure of email sending

## 🎯 Best Practices

### 1. **Context Naming**
- Use clear, descriptive context names
- Maintain consistency across similar scenarios
- Avoid ambiguous or overlapping contexts

### 2. **Details Structure**
- Include all relevant identifiers (PO, ASN, Pallet IDs)
- Provide meaningful status information
- Use consistent key naming conventions

### 3. **Error Handling**
- Always provide fallback mechanisms
- Log AI generation failures
- Monitor AI system availability

### 4. **Testing**
- Test with various context combinations
- Verify fallback system functionality
- Validate email content quality

## 🔗 Related Components

- **Email Handler**: `scripts/email_handler.py`
- **Chat Interface**: `scripts/chat_interface.py`
- **Main App**: `app.py`
- **Database**: `scripts/db.py`
- **Utilities**: `scripts/utils.py`

---

## 📞 Support

For questions or issues with the AI email system:
1. Check the troubleshooting section above
2. Review the test script output
3. Verify AI system availability
4. Check system logs for errors

---

**🎉 The AI-powered email system transforms static, predefined messages into dynamic, contextual, and professional communications while maintaining all existing functionality!**
