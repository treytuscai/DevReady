document.addEventListener("DOMContentLoaded", function () {
    const editor = ace.edit("editor");
    const hintBtn = document.getElementById("hint-btn");
    const chatBox = document.getElementById("chat-box");

    function getQuestionDescription() {
        const descriptionElement = document.getElementById("question-description");
        return descriptionElement ? descriptionElement.innerText.trim() : "Unknown Problem";
    }

    function addMessage(role, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("p-2", "rounded", "mb-1", "d-inline-block");

        if (role === "user") {
            messageDiv.classList.add("bg-black", "text-white", "align-self-end");
        } else {
            messageDiv.classList.add("bg-light", "border");
        }

        messageDiv.innerHTML = `<small>${role === "user" ? "You" : "AI Helper"} (${new Date().toLocaleTimeString()}):</small><br>${text}`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
    }

    function showLoadingIndicator() {
        const loadingDiv = document.createElement("div");
        loadingDiv.id = "loading-indicator";
        loadingDiv.classList.add("text-muted", "text-center", "mt-2");
        loadingDiv.innerHTML = "AI is thinking...";
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeLoadingIndicator() {
        const loadingDiv = document.getElementById("loading-indicator");
        if (loadingDiv) loadingDiv.remove();
    }

    async function fetchHint(description, code) {
        try {
            console.log(description)
            const response = await fetch("/hint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question_description: description, code: code })
            });

            const result = await response.json();
            return result.success ? result.hint : `Error: ${result.error}`;
        } catch (error) {
            return "Network error. Please try again.";
        }
    }

    hintBtn.addEventListener("click", async function () {
        const questionDescription = getQuestionDescription();
        const code = editor.getValue().trim();

        if (!code) {
            addMessage("AI Helper", "<span class='text-danger'>Please write some code first.</span>");
            return;
        }

        addMessage("user", "Get Hint!");
        showLoadingIndicator();

        const hint = await fetchHint(questionDescription, code);
        removeLoadingIndicator();
        addMessage("AI Helper", hint);
    });
});
