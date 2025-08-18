class ChatbotUI {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.processingIndicator = document.getElementById('processingIndicator');
        
        this.userEmail = null;
        this.isEmailPhase = true;
        this.screenshotData = null;
        this.eventSource = null;
        
        this.initializeEventListeners();
        this.connectToPrintStream();
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

    connectToPrintStream() {
        // Close existing connection if any
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        // Connect to SSE stream for live print outputs
        this.eventSource = new EventSource('/stream-prints');
        
        this.eventSource.onopen = () => {
            console.log('SSE connection established');
            this.updateConnectionStatus(true);
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'print') {
                    this.addSystemMessage(data.message);
                }
            } catch (error) {
                console.error('Error parsing SSE message:', error);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            this.updateConnectionStatus(false);
            // Attempt to reconnect after a delay
            setTimeout(() => this.connectToPrintStream(), 5000);
        };
    }

    updateConnectionStatus(isConnected) {
        const statusText = document.querySelector('.status-text');
        const statusDot = document.querySelector('.status-dot');
        
        if (statusText && statusDot) {
            if (isConnected) {
                statusText.textContent = 'Live Updates Active';
                statusDot.style.background = '#10b981'; // Green
            } else {
                statusText.textContent = 'Reconnecting...';
                statusDot.style.background = '#f59e0b'; // Yellow
            }
        }
    }

    disconnectFromPrintStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    // Cleanup method for when the page is unloaded
    cleanup() {
        this.disconnectFromPrintStream();
    }


    async captureScreenshot() {
        try {
            // Check if html2canvas is available
            if (typeof html2canvas === 'undefined') {
                console.warn('html2canvas not available, skipping screenshot');
                return null;
            }
            
            const chatContainer = document.querySelector('.chat-container');
            const canvas = await html2canvas(chatContainer, {
                backgroundColor: '#ffffff',
                scale: 2,
                useCORS: true,
                allowTaint: true
            });
            return canvas.toDataURL('image/png');
        } catch (error) {
            console.error('Error capturing screenshot:', error);
            return null;
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
            
            // Capture screenshot if not in email phase
            let screenshotData = null;
            if (!this.isEmailPhase) {
                screenshotData = await this.captureScreenshot();
            }
            
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    email: this.userEmail,
                    screenshot: screenshotData
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

            // If backend signals end of session, lock the UI
            if (data.end) {
                this.disableInput();
                return; // Do not re-enable in finally
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addBotMessage("Sorry, I'm having trouble processing your request. Please try again.");
        } finally {
            this.hideLoading();
            // Only re-enable if not ended
            if (!(typeof data !== 'undefined' && data.end)) {
                this.enableInput();
                this.messageInput.focus();
            }
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
        
        // Add a brief highlight effect to show new system message
        messageElement.style.animation = 'highlightNew 0.5s ease-out';
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
        // Show the subtle processing indicator instead of full overlay
        if (this.processingIndicator) {
            this.processingIndicator.classList.add('show');
        }
        
        // Also show processing indicator in header
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.classList.add('processing');
            const statusText = statusIndicator.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = 'Processing...';
            }
        }
    }

    hideLoading() {
        // Hide the subtle processing indicator
        if (this.processingIndicator) {
            this.processingIndicator.classList.remove('show');
        }
        
        // Remove processing indicator from header
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusIndicator) {
            statusIndicator.classList.remove('processing');
            const statusText = statusIndicator.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = 'Live Updates Active';
            }
        }
    }

    showFullLoading() {
        // Show the full loading overlay for longer operations
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('show');
        }
    }

    hideFullLoading() {
        // Hide the full loading overlay
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('show');
        }
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
    const chatbot = new ChatbotUI();
    
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

    // Cleanup when page is unloaded
    window.addEventListener('beforeunload', () => {
        chatbot.cleanup();
    });
});
