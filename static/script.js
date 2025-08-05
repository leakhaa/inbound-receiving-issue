class ChatbotUI {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        
        this.userEmail = null;
        this.isEmailPhase = true;
        
        this.initializeEventListeners();
        this.initializeChat();
    }

    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input focus for better UX
        this.messageInput.addEventListener('focus', () => {
            this.messageInput.parentElement.style.boxShadow = '0 4px 20px rgba(102, 126, 234, 0.3)';
        });

        this.messageInput.addEventListener('blur', () => {
            this.messageInput.parentElement.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        });
    }

    async initializeChat() {
        try {
            this.showLoading();
            const response = await fetch('/', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.text();
                // Extract initial message from the response
                const parser = new DOMParser();
                const doc = parser.parseFromString(data, 'text/html');
                const initialMessage = doc.querySelector('.initial-message')?.textContent || 
                                     "Hello! I'm your warehouse assistant. Please provide your email address to get started.";
                
                this.addBotMessage(initialMessage);
            }
        } catch (error) {
            console.error('Error initializing chat:', error);
            this.addBotMessage("Hello! I'm your warehouse assistant. Please provide your email address to get started.");
        } finally {
            this.hideLoading();
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addUserMessage(message);
        this.messageInput.value = '';
        this.disableInput();

        try {
            this.showLoading();
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    email: this.userEmail
                })
            });

            const data = await response.json();
            
            if (data.email_valid !== undefined) {
                // Email validation phase
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

            // Add bot response
            this.addBotMessage(data.response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addBotMessage("Sorry, I'm having trouble processing your request. Please try again.");
        } finally {
            this.hideLoading();
            this.enableInput();
            this.messageInput.focus();
        }
    }

    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">${this.formatMessage(message)}</div>
        `;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message system';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-cog"></i>
            </div>
            <div class="message-content system-content">${this.formatMessage(message)}</div>
        `;
        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    formatMessage(message) {
        // Convert line breaks to <br> tags
        return this.escapeHtml(message).replace(/\n/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showLoading() {
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    disableInput() {
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
    }

    enableInput() {
        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
    }

    // Utility method to show typing indicator
    showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot typing-indicator';
        typingElement.id = 'typing-indicator';
        typingElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.chatMessages.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
}

// Initialize the chatbot when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatbotUI();
    
    // Add smooth entrance animation
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.style.opacity = '0';
        chatContainer.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            chatContainer.style.transition = 'all 0.5s ease-out';
            chatContainer.style.opacity = '1';
            chatContainer.style.transform = 'translateY(0)';
        }, 100);
    }

    // Add hover effects for send button
    const sendButton = document.getElementById('sendButton');
    if (sendButton) {
        sendButton.addEventListener('mouseenter', () => {
            sendButton.style.transform = 'scale(1.05)';
        });
        
        sendButton.addEventListener('mouseleave', () => {
            sendButton.style.transform = 'scale(1)';
        });
    }
});
