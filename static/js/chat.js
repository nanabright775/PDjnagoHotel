    // Function to copy text to clipboard
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text);
    }

    // Function to clear clipboard content
    function clearClipboard() {
        navigator.clipboard.writeText('');
    }

    // Function to strip HTML tags from a string
    function stripHTMLTags(text) {
        let doc = new DOMParser().parseFromString(text, 'text/html');
        return doc.body.textContent || "";
    }

    // Add event listeners to copy buttons
    document.querySelectorAll('.copy-button').forEach(button => {
        let isCopied = false;  // Flag to keep track of copy state

        button.addEventListener('click', () => {
            const content = button.getAttribute('data-content');
            const strippedContent = stripHTMLTags(content);  // Strip HTML tags
            
            if (isCopied) {
                // If already copied, clear clipboard and revert button
                clearClipboard();
                button.innerHTML = '<i class="bi bi-clipboard"></i>';
            } else {
                // If not copied, copy stripped content and change button to tick
                copyToClipboard(strippedContent);
                button.innerHTML = '<i class="bi bi-check-circle-fill"></i>';
            }

            // Toggle the copy state
            isCopied = !isCopied;
        });
    });

    // Scroll chat box to the last response
    function scrollToLastResponse() {
        const chatBox = document.getElementById('chat-box');
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Call the scrollToLastResponse function to scroll to the last response
    scrollToLastResponse();

    // Optionally, you can also observe the chat box for new messages
    const observer = new MutationObserver(() => {
        scrollToLastResponse();
    });
    observer.observe(document.getElementById('chat-box'), { childList: true });

    // Add event listeners to command boxes
    document.querySelectorAll('.command-box').forEach(box => {
        box.addEventListener('click', () => {
            const command = box.getAttribute('data-command');
            document.querySelector('textarea[name="message"]').value = command;
            sendMessage(command);
        });
    });

    // Chat button functionality
    document.getElementById('chat-button').addEventListener('click', () => {
    document.getElementById('chat-window').classList.toggle('open');
});
    

    document.getElementById('close-chat').addEventListener('click', () => {
        document.getElementById('chat-window').classList.remove('open');
    });

    // AJAX form submission for chat
    document.getElementById('chat-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch("{% url 'chat' %}", {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.data.text) {
                const chatBox = document.getElementById('chat-box');
                const userMessage = document.querySelector('textarea[name="message"]').value;
                chatBox.innerHTML += `
                    <div class="user-message m-3">
                        <strong>{{ request.user.username }}</strong> <br> ${userMessage}
                        <button id="copy_button" class="btn btn-sm copy-button text-light" data-content="${userMessage}"><i class="bi bi-clipboard"></i></button>
                    </div>
                    <div class="bot-response">
                        <strong><i class="bi bi-robot"></i></strong><br>
                        ${data.data.text}
                        <button id="copy_button" class="btn btn-sm copy-button" data-content="${data.data.text}"><i class="bi bi-clipboard"></i></button>
                    </div>
                `;
                document.querySelector('textarea[name="message"]').value = '';
                scrollToLastResponse();
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Function to send command as a message via AJAX
    function sendMessage(command) {
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('message', command);

        fetch("{% url 'chat' %}", {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            },
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.data.text) {
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML += `
                    <div class="user-message m-3">
                        <strong>{{ request.user.username }}</strong> <br> ${command}
                        <button id="copy_button" class="btn btn-sm copy-button text-light" data-content="${command}"><i class="bi bi-clipboard"></i></button>
                    </div>
                    <div class="bot-response">
                        <strong><i class="bi bi-robot"></i></strong><br>
                        ${data.data.text}
                        <button id="copy_button" class="btn btn-sm copy-button" data-content="${data.data.text}"><i class="bi bi-clipboard"></i></button>
                    </div>
                `;
                scrollToLastResponse();
            }
        })
        .catch(error => console.error('Error:', error));
    }