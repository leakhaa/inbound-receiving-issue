# Warehouse Assistant Chatbot

A modern, AI-powered chatbot system for warehouse inbound receiving support with a beautiful, responsive frontend.

## Features

- 🤖 **AI-Powered Assistant**: Uses LLaMA model via Groq API for intelligent responses
- 🎨 **Modern UI**: Beautiful, responsive design with smooth animations
- 📱 **Mobile-Friendly**: Works perfectly on desktop and mobile devices
- 🔄 **Real-time Chat**: Instant message processing and responses
- 📧 **Email Validation**: Secure email collection and validation
- 🏭 **Warehouse Focused**: Specialized for inbound receiving issues (ASN, PO, Pallet, Quantity Mismatch)

## System Architecture

```
├── backend/
│   ├── app.py              # Flask backend with AI integration
│   ├── static/             # Frontend assets
│   │   ├── style.css       # Modern CSS styling
│   │   └── script.js       # Interactive JavaScript
│   ├── templates/          # Flask templates
│   │   └── index.html      # Main chat interface
│   └── scripts/            # AI processing modules
├── frontend/               # Legacy frontend files
└── database/               # Database files
```

## Quick Start

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Set Up API Key

The system uses Groq API for AI responses. You'll need to:

1. Get a Groq API key from [https://console.groq.com/](https://console.groq.com/)
2. Update the `GROQ_API_KEY` in `backend/app.py` with your key

### 3. Run the Application

```bash
# Navigate to backend directory
cd backend

# Run the Flask application
python app.py
```

### 4. Access the Chatbot

Open your browser and go to: `http://localhost:5000`

## How It Works

### 1. Initial Greeting
- The chatbot starts with a casual greeting and asks for the user's email
- Email validation ensures proper user identification

### 2. Issue Classification
Once email is provided, the system can handle various warehouse issues:
- **ASN (Advanced Shipping Notice)** issues
- **PO (Purchase Order)** problems
- **Pallet** related concerns
- **Quantity Mismatch** issues

### 3. AI Processing
- User messages are processed through the LLaMA model
- The system extracts relevant IDs and parameters
- Issues are classified and resolved automatically

### 4. Response Generation
- AI generates contextual, helpful responses
- System maintains conversation context
- Users can report multiple issues in one session

## Frontend Features

### Modern Design
- **Gradient Background**: Beautiful purple gradient theme
- **Glass Morphism**: Translucent chat container with blur effects
- **Smooth Animations**: Message slide-in animations and hover effects
- **Responsive Layout**: Works on all screen sizes

### User Experience
- **Real-time Typing**: Visual feedback during message processing
- **Loading States**: Elegant loading spinners and overlays
- **Message Bubbles**: Clear distinction between user and bot messages
- **Auto-scroll**: Automatically scrolls to latest messages
- **Keyboard Support**: Enter to send, Shift+Enter for new lines

### Interactive Elements
- **Send Button**: Animated button with hover effects
- **Input Field**: Smart focus states and validation
- **Status Indicator**: Shows bot online status with pulsing animation
- **Avatar System**: User and bot avatars for clear identification

## API Endpoints

### `GET /`
- Serves the main chat interface
- Initializes conversation with greeting message

### `POST /chat`
- Processes user messages
- Handles email validation
- Returns AI-generated responses

**Request Body:**
```json
{
  "message": "user message",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "response": "AI response",
  "email_valid": true/false,
  "email": "validated_email@example.com"
}
```

## Customization

### Styling
- Modify `backend/static/style.css` to change colors, fonts, and layout
- The design uses CSS custom properties for easy theming

### AI Behavior
- Edit `backend/app.py` to modify AI prompts and responses
- Adjust temperature and model parameters for different response styles

### Adding Features
- Extend the JavaScript in `backend/static/script.js` for new interactions
- Add new API endpoints in `backend/app.py` for additional functionality

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Groq API key is valid and has sufficient credits
2. **Port Already in Use**: Change the port in `app.py` or kill existing processes
3. **Static Files Not Loading**: Ensure the `static` folder is in the correct location

### Debug Mode
Run with debug enabled for detailed error messages:
```python
app.run(debug=True, port=5000)
```

## Security Considerations

- API keys should be stored in environment variables
- Input validation is implemented for email addresses
- XSS protection through proper HTML escaping
- CSRF protection can be added for production use

## Future Enhancements

- [ ] User authentication system
- [ ] Chat history persistence
- [ ] File upload support for documents
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with warehouse management systems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

