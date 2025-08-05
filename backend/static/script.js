class Chatbot {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.loading = document.getElementById('loading');
        
        this.userEmail = null;
        this.isEmailPhase = true;
        
        this.init();
    }

    init() {
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
                if (data.email_valid) {
                    this.userEmail = data.email;
                    this.isEmailPhase = false;
                    this.messageInput.placeholder = "Describe your issue...";
                }
            }

            this.addBotMessage(data.response);
            
        } catch (error) {
            console.error('Error:', error);
            this.addBotMessage("Sorry, I'm having trouble. Please try again.");
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

    formatMessage(message) {
        // Handle processing details with special formatting
        if (message.includes('**Processing Details:**')) {
            const parts = message.split('**Processing Details:**');
            const beforeProcessing = parts[0];
            const processingDetails = parts[1];
            
            let formattedMessage = this.escapeHtml(beforeProcessing);
            
            if (processingDetails) {
                formattedMessage += '<div class="processing-details">';
                formattedMessage += '<strong>Processing Details:</strong>';
                formattedMessage += '<div class="processing-list">';
                const details = processingDetails.split('\n').filter(line => line.trim());
                details.forEach(detail => {
                    if (detail.trim()) {
                        formattedMessage += `<div class="processing-item">${this.escapeHtml(detail.trim())}</div>`;
                    }
                });
                formattedMessage += '</div></div>';
            }
            
            return formattedMessage;
        }
        
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
        this.loading.classList.add('show');
    }

    hideLoading() {
        this.loading.classList.remove('show');
    }

    disableInput() {
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
    }

    enableInput() {
        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
    }
}

// Initialize chatbot when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Chatbot();
}); 