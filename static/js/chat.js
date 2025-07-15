

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
    const upperNote = document.getElementById('upper-note');
    const lowerNote = document.getElementById('lower-note');
    // Fetch and display previous chat history
    let chatEndpoint = "/accounts/chat/";

    if (typeof window.collectionId !== 'undefined') {
        chatEndpoint = `/collections/${window.collectionId}/chat/`;
    }

    fetch(chatEndpoint, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
    })
    .then((response) => response.json())
    .then((data) => {
        if (Array.isArray(data.history)) {
            data.history.forEach((entry) => {
                const sender = entry.role === "user" ? "user" : "ai";
                const label = sender === "user" ? "You" : "AI";
                chatMessages.innerHTML += `<div class="chat-bubble ${sender}"><strong>${label}:</strong><br>${escapeHtml(entry.content).replace(/\n/g, "<br/>")}</div>`;

            });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });


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

        chatMessages.className = "p-2";
        chatMessages.innerHTML += `<div class="chat-bubble user"><strong>You:</strong><br>${escapeHtml(message).replace(/\n/g, "<br/>")}</div>`;

    
        chatInput.value = "";
        aiLoading.style.display = 'block';  // Show "AI is thinking..."
        upperNote.style.display = 'none';
        try {
            const response = await fetch(chatEndpoint, {
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

    clearButton.addEventListener('click', () => {
        
        chatMessages.innerHTML = '';
        chatMessages.className = "p-0";
        
        fetch('/accounts/clear_chat/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
        });
    });

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
});
