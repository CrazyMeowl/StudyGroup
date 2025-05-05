

document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatSubmit = document.getElementById('chat-submit');
    const chatMessages = document.getElementById('chat-messages');
    const chatBox = document.getElementById('chat-box');
    const clearButton = document.getElementById('clear-button');
    const hideChatButton = document.getElementById('hide-chat-btn');
    const showChatButton = document.getElementById('show-chat-btn');
    const aiLoading = document.getElementById('ai-loading');  // Spinner element

    function escapeHtml(text) {
        if (!text) return '';
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    chatInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            if (!e.shiftKey) {
                e.preventDefault(); // Prevent newline
                chatForm.requestSubmit(); // Submit the form
            }
        }
    });


    chatForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const message = chatInput.value.trim();
        if (!message) return;

        chatInput.disabled = true;
        chatSubmit.disabled = true;

        
        chatMessages.innerHTML += `<div class="chat-bubble user"><strong>You:</strong><br>${escapeHtml(message).replace(/\n/g, "<br/>")}</div>`;

    
        chatInput.value = "";
        aiLoading.style.display = 'block';  // Show "AI is thinking..."

        try {
            const response = await fetch("/accounts/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRFToken(),
                },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();

            chatMessages.innerHTML += `<div class="chat-bubble ai"><strong>AI:</strong><br>${escapeHtml(data.reply).replace(/\n/g, "<br/>")}</div>`;


            chatMessages.scrollTop = chatMessages.scrollHeight;

        } catch (error) {
            chatMessages.innerHTML += `
                <p class="text-danger"><strong>Error:</strong> Could not contact AI assistant.</p>`;
        } finally {
            aiLoading.style.display = 'none';  // Hide spinner
            chatInput.disabled = false;
            chatSubmit.disabled = false;
            chatInput.focus();
        }
    });

    hideChatButton.addEventListener('click', () => {
        chatBox.style.display = 'none';
        showChatButton.style.display = 'flex';
    });


    showChatButton.addEventListener('click', () => {
        chatBox.style.display = 'flex';
        showChatButton.style.display = 'none';
    });

    function clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = '';

        fetch('/accounts/clear_chat/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        });
    }

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
});
