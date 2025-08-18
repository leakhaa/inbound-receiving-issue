from flask import Flask, request, render_template, jsonify, Response
from scripts.classifier import classify_with_retry, classify
from scripts.resolver import resolve_issue, get_print_outputs, add_print_output
from scripts.extractor import extract_ids, validate_ids
import requests
import re
import json
import os # <-- Import os to get API key from environment variable
import queue
import threading
import time

app = Flask(__name__, static_folder='../static', template_folder='../templates')

# Global queue for print outputs
print_queue = queue.Queue()
print_clients = set()

# AI assistant using LLaMA model
API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Secure your API key by using an environment variable
API_KEY = "sk-xxxxxx"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}
MODEL = "llama3-8b-8192"

conversation = []
chat_log = []

def chat_with_ai(user_message: str) -> str:
    conversation.append({"role": "user", "content": user_message})
    payload = {"model": MODEL, "messages": conversation, "temperature": 0.2}
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    ai_message = response.json()["choices"][0]["message"]["content"]
    conversation.append({"role": "assistant", "content": ai_message})
    chat_log.append({"user": user_message, "bot": ai_message})
    return ai_message

def is_valid_email(email):
    return re.fullmatch(r"[\w\.-]+@[\w\.-]+\.\w{2,}", email) is not None

def broadcast_print_output(message):
    """Broadcast print output to all connected clients"""
    if print_clients:
        # Remove disconnected clients
        disconnected_clients = set()
        for client in print_clients:
            try:
                client.put(f"data: {json.dumps({'type': 'print', 'message': message})}\n\n")
            except:
                disconnected_clients.add(client)
        
        # Clean up disconnected clients
        print_clients.difference_update(disconnected_clients)

def capture_print_output():
    """Capture print statements and broadcast them live"""
    import builtins
    original_print = builtins.print
    
    def live_print(*args, **kwargs):
        # Call original print
        original_print(*args, **kwargs)
        # Broadcast to frontend
        output = ' '.join(str(arg) for arg in args)
        broadcast_print_output(output)
    
    return live_print

# SSE endpoint for live print outputs
@app.route('/stream-prints')
def stream_prints():
    def generate():
        # Create a queue for this client
        client_queue = queue.Queue()
        print_clients.add(client_queue)
        
        try:
            while True:
                try:
                    # Wait for messages with timeout
                    message = client_queue.get(timeout=30)
                    yield message
                except queue.Empty:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': time.time()})}\n\n"
        except GeneratorExit:
            # Client disconnected
            print_clients.discard(client_queue)
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Cache-Control'
    })

# The home page route
@app.route('/')
def home():
    # Initialize the conversation with the greeting
    global conversation
    conversation = []
    try:
        initial_message = chat_with_ai("You are a warehouse assistant. Start the chat with casual greeting and ask for email.no lengthly message just sharp and crisp nut be casual")
    except Exception as e:
        print(f"Error calling AI: {e}")
        initial_message = "Hello! I'm your warehouse assistant. Please provide your email address to get started."
    
    # Debug: Print the template being rendered
   # print(f"Rendering template with initial_message: {initial_message}")
    return render_template('index.html', initial_message=initial_message)

# Debug route to test static files
@app.route('/test')
def test():
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Page</h1>
        <p>If you can see this, Flask is working!</p>
        <a href="/">Go to Chatbot</a>
    </body>
    </html>
    """

# Static HTML route for testing
@app.route('/templates-html')
def static_html():
    return app.send_static_file('index.html')

# Simple test route with inline HTML
@app.route('/simple')
def simple():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Simple Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .container { max-width: 400px; margin: 50px auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; }
            button { background: white; color: #667eea; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Flask is Working!</h1>
            <p>If you can see this styled page, Flask is serving HTML correctly.</p>
            <button onclick="alert('JavaScript works too!')">Test JavaScript</button>
            <br><br>
            <a href="/" style="color: white;">← Go to Chatbot</a>
        </div>
    </body>
    </html>
    """

# Complete chatbot with inline CSS and JS
@app.route('/chatbot')
def chatbot():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Warehouse Assistant Chatbot</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Inter', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                height: 100vh; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                overflow: hidden; 
            }
            .chat-container { 
                width: 100%; max-width: 400px; height: 90vh; 
                background: rgba(255, 255, 255, 0.95); 
                backdrop-filter: blur(20px); border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1); 
                display: flex; flex-direction: column; overflow: hidden; 
                border: 1px solid rgba(255, 255, 255, 0.2); 
            }
            .chat-header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 20px 20px 0 0; 
            }
            .header-content { display: flex; align-items: center; gap: 15px; }
            .bot-avatar { 
                width: 50px; height: 50px; background: rgba(255, 255, 255, 0.2); 
                border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                font-size: 24px; 
            }
            .header-info h1 { font-size: 18px; font-weight: 600; margin-bottom: 2px; }
            .header-info p { font-size: 12px; opacity: 0.8; font-weight: 300; }
            .status-indicator { margin-left: auto; display: flex; align-items: center; gap: 6px; font-size: 12px; }
            .status-dot { 
                width: 8px; height: 8px; background: #4ade80; border-radius: 50%; 
                animation: pulse 2s infinite; 
            }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .chat-messages { 
                flex: 1; padding: 20px; overflow-y: auto; 
                display: flex; flex-direction: column; gap: 15px; 
            }
            .message { display: flex; gap: 10px; animation: slideIn 0.3s ease-out; }
            @keyframes slideIn { 
                from { opacity: 0; transform: translateY(10px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .message.user { flex-direction: row-reverse; }
            .message-avatar { 
                width: 35px; height: 35px; border-radius: 50%; 
                display: flex; align-items: center; justify-content: center; 
                font-size: 14px; flex-shrink: 0; 
            }
            .message.user .message-avatar { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; 
            }
            .message.bot .message-avatar { background: #f3f4f6; color: #6b7280; }
            .message-content { 
                max-width: 70%; padding: 12px 16px; border-radius: 18px; 
                font-size: 14px; line-height: 1.4; word-wrap: break-word; 
            }
            .message.user .message-content { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; border-bottom-right-radius: 6px; 
            }
            .message.bot .message-content { 
                background: #f3f4f6; color: #374151; border-bottom-left-radius: 6px; 
            }
            .message.system .message-avatar { background: #fef3c7; color: #d97706; }
            .message.system .message-content { 
                background: #fef3c7; color: #92400e; border-bottom-left-radius: 6px; 
                font-family: 'Courier New', monospace; font-size: 12px; 
            }
            .chat-input-container { 
                padding: 20px; background: rgba(255, 255, 255, 0.8); 
                border-top: 1px solid rgba(0, 0, 0, 0.1); 
            }
            .input-wrapper { 
                display: flex; gap: 10px; align-items: center; background: white; 
                border-radius: 25px; padding: 5px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); 
                border: 1px solid rgba(0, 0, 0, 0.1); 
            }
            #messageInput { 
                flex: 1; border: none; outline: none; padding: 12px 16px; 
                font-size: 14px; background: transparent; font-family: inherit; 
            }
            #messageInput::placeholder { color: #9ca3af; }
            .send-button { 
                width: 40px; height: 40px; border: none; border-radius: 50%; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; cursor: pointer; display: flex; align-items: center; 
                justify-content: center; transition: all 0.2s ease; font-size: 14px; 
            }
            .send-button:hover { transform: scale(1.05); box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); }
            .send-button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
            .input-hint { 
                display: flex; align-items: center; gap: 6px; margin-top: 8px; 
                font-size: 11px; color: #6b7280; opacity: 0.7; 
            }
            .loading-overlay { 
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0, 0, 0, 0.5); display: none; align-items: center; 
                justify-content: center; z-index: 1000; backdrop-filter: blur(5px); 
            }
            .loading-overlay.show { display: flex; }
            .loading-spinner { 
                background: white; padding: 30px; border-radius: 15px; 
                text-align: center; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); 
            }
            .spinner { 
                width: 40px; height: 40px; border: 3px solid #f3f4f6; 
                border-top: 3px solid #667eea; border-radius: 50%; 
                animation: spin 1s linear infinite; margin: 0 auto 15px; 
            }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .loading-spinner p { color: #6b7280; font-size: 14px; }
            @media (max-width: 480px) { 
                .chat-container { height: 100vh; max-width: 100%; border-radius: 0; } 
                .chat-header { border-radius: 0; } 
                .header-info h1 { font-size: 16px; } 
                .message-content { max-width: 85%; } 
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <div class="header-content">
                    <div class="bot-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="header-info">
                        <h1>Warehouse Assistant</h1>
                        <p>AI-powered inbound receiving support</p>
                    </div>
                    <div class="status-indicator">
                        <span class="status-dot"></span>
                        <span class="status-text">Online</span>
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message bot">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">Hello! I'm your warehouse assistant. Please provide your email address to get started.</div>
                </div>
            </div>

            <div class="chat-input-container">
                <div class="input-wrapper">
                    <input type="text" id="messageInput" placeholder="Type your message..." autocomplete="off">
                    <button id="sendButton" class="send-button">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="input-hint">
                    <i class="fas fa-info-circle"></i>
                    <span>Press Enter to send, Shift+Enter for new line</span>
                </div>
            </div>
        </div>

        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p>Processing your request...</p>
            </div>
        </div>

        <script>
            class ChatbotUI {
                constructor() {
                    this.chatMessages = document.getElementById('chatMessages');
                    this.messageInput = document.getElementById('messageInput');
                    this.sendButton = document.getElementById('sendButton');
                    this.loadingOverlay = document.getElementById('loadingOverlay');
                    this.userEmail = null;
                    this.isEmailPhase = true;
                    this.initializeEventListeners();
                }

                initializeEventListeners() {
                    this.sendButton.addEventListener('click', () => this.sendMessage());
                    this.messageInput.addEventListener('keypress', (e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            this.sendMessage();
                        }
                    });
                }

                async sendMessage() {
                    const message = this.messageInput.value.trim();
                    if (!message) return;

                    this.addUserMessage(message);
                    this.messageInput.value = '';
                    this.disableInput();

                    try {
                        this.showLoading();
                        const response = await fetch('/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ message: message, email: this.userEmail })
                        });

                        const data = await response.json();
                        
                        if (data.email_valid !== undefined) {
                            if (data.email_valid) {
                                this.userEmail = data.email;
                                this.isEmailPhase = false;
                                this.messageInput.placeholder = "Describe your inbound receiving issue...";
                            }
                        }

                        // Display print outputs if available
                        if (data.print_outputs && data.print_outputs.length > 0) {
                            data.print_outputs.forEach(output => {
                                this.addSystemMessage(output);
                            });
                        }

                        this.addBotMessage(data.response);
                    } catch (error) {
                        console.error('Error:', error);
                        this.addBotMessage("Sorry, I'm having trouble processing your request. Please try again.");
                    } finally {
                        this.hideLoading();
                        this.enableInput();
                        this.messageInput.focus();
                    }
                }
                  startPrintStreaming() {
                    // Clear any existing print outputs
                    this.stopPrintStreaming();
                    
                    this.lastPrintCount = 0;
                    
                    // Start polling for new print outputs
                    this.printPollingInterval = setInterval(async () => {
                        try {
                            const response = await fetch('/get-latest-prints');
                            const data = await response.json();
                            if (data.prints && data.prints.length > this.lastPrintCount) {
                                // Only show new prints since last check
                                const newPrints = data.prints.slice(this.lastPrintCount);
                                newPrints.forEach(output => {
                                    this.addSystemMessage(output);
                                });
                                this.lastPrintCount = data.prints.length;
                            }
                        } catch (error) {
                            console.error('Error polling prints:', error);
                        }
                    }, 100); // Poll every 100ms for more responsive updates
                }

                stopPrintStreaming() {
                    if (this.printPollingInterval) {
                        clearInterval(this.printPollingInterval);
                        this.printPollingInterval = null;
                    }
                }


                addUserMessage(message) {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message user';
                    messageElement.innerHTML = `
                        <div class="message-avatar"><i class="fas fa-user"></i></div>
                        <div class="message-content">${this.escapeHtml(message)}</div>
                    `;
                    this.chatMessages.appendChild(messageElement);
                    this.scrollToBottom();
                }

                addBotMessage(message) {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message bot';
                    messageElement.innerHTML = `
                        <div class="message-avatar"><i class="fas fa-robot"></i></div>
                        <div class="message-content">${this.formatMessage(message)}</div>
                    `;
                    this.chatMessages.appendChild(messageElement);
                    this.scrollToBottom();
                }

                 addSystemMessage(message) {
                    const messageElement = document.createElement('div');
                    messageElement.className = 'message system';
                    messageElement.innerHTML = `
                        <div class="message-avatar"><i class="fas fa-cog"></i></div>
                        <div class="message-content system-content">${this.formatMessage(message)}</div>
                    `;
                    this.chatMessages.appendChild(messageElement);
                    this.scrollToBottom();
                }
                formatMessage(message) {
                    return this.escapeHtml(message).replace(/\\n/g, '<br>');
                }

                escapeHtml(text) {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }

                scrollToBottom() {
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }

                showLoading() { this.loadingOverlay.classList.add('show'); }
                hideLoading() { this.loadingOverlay.classList.remove('show'); }
                disableInput() { this.messageInput.disabled = true; this.sendButton.disabled = true; }
                enableInput() { this.messageInput.disabled = false; this.sendButton.disabled = false; }
            }

            document.addEventListener('DOMContentLoaded', () => {
                new ChatbotUI();
            });
        </script>
    </body>
    </html>
    """

# The chat API endpoint
@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.get_json()
    user_message = user_data.get('message')
    user_email = user_data.get('email')
    if user_message.strip().lower() == 'exit':
        ai_response = "Thank you for using the warehouse assistant. Have a great day!"
        return jsonify({'response': ai_response})
    
    if not user_email:
        # This is for the email validation phase
        if is_valid_email(user_message):
            ai_response = chat_with_ai(f"thanks for providing your email: {user_message}.ow ask what inbound receiving issue the user is facing (ASN, PO, Pallet, Quantity Mismatch)")
            return jsonify({'response': ai_response, 'email_valid': True, 'email': user_message})
        else:
            ai_response = chat_with_ai("Please provide a valid email address.")
            return jsonify({'response': ai_response, 'email_valid': False})

    # This is for the issue handling phase
    issue_type = classify(user_message)
    ids = extract_ids(user_message)
    
    ai_response = chat_with_ai(f" I'VE identified this as :{issue_type}.  working on it. Extracted details: {json.dumps(ids)} crisp and sharp straight to the point like these are the parameters do not ask for any other parameters or questions ok" )
    
    # Use live print capture for real-time updates
    live_print = capture_print_output()
    import builtins
    original_print = builtins.print
    builtins.print = live_print
    
    try:
        print(ai_response)
        confirmation = resolve_issue(issue_type, ids, user_email)
    finally:
        builtins.print = original_print
    
    final_response = chat_with_ai(confirmation)
    final_response += f"\nWould you like to report another issue? Type 'exit' to quit or describe your issue."
    
    return jsonify({'response': final_response})

if __name__ == '__main__':
    # Add your GROQ_API_KEY as an environment variable before running
    # e.g., export GROQ_API_KEY="your_key_here"
    app.run(debug=True)
