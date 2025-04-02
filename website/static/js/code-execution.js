// Execute code via API
async function executeCode(endpoint, isSubmission = false) {
    const questionElem = document.getElementById("question-title");
    const questionId = questionElem ? questionElem.dataset.questionId : null;
    if (!questionId) return alert("No question selected!");

    // Editor and code
    const editor = ace.edit("editor");
    const code = editor.getValue();
    const language = document.getElementById("language-select").value.toLowerCase();

    // Output block
    const outputContainer = document.getElementById('output-container');

    // Error block and text
    const errorContainer = document.getElementById('stderr-container');
    const errorText = document.getElementById('stderr-text');

    // Try running code
    try {
        const res = await fetch(`/${endpoint}/${questionId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ code, language }),
        });
        const result = await res.json();
        isSubmission ? displaySubmissionResults(result.results) : displayRunResults(result.results);
    } catch (error) {
        // Hide output and show fetch error
        outputContainer.style.display = "none";
        errorContainer.style.display = "block";
        errorText.innerHTML = `<pre class="text-danger">Error: ${error.message}</pre>`;
    }
}

// Update sample test case buttons based on run results
function displayRunResults(results) {
    // Test case buttons
    const buttons = document.querySelectorAll("#test-case-buttons button");

    // Add results to buttons
    results.forEach((test, i) => {
        if (i < buttons.length) {
            const btn = buttons[i];
            btn.className = test.passed ? "btn btn-success" : "btn btn-danger";
            btn.onclick = () => showTestCase(test.stderr, test.input, test.stdout, test.output, test.expected, btn);
        }
    });

    // Automatically show the first test case result
    showTestCase(results[0].stderr, results[0].input, results[0].stdout, results[0].output, results[0].expected, buttons[0]);
}

// Needs logic to show unpassed cases beyond sample !!!!!
// Update test case buttons based on submission results
function displaySubmissionResults(results) {
    // Test case buttons
    const buttons = document.querySelectorAll("#test-case-buttons button");

    // Add results to buttons
    results.forEach((test, i) => {
        if (i < buttons.length) {
            const btn = buttons[i];
            btn.className = test.passed ? "btn btn-success" : "btn btn-danger";
            btn.onclick = () => showTestCase(test.stderr, test.input, test.stdout, test.output, test.expected, btn);
        }
    });

    // Automatically show the first test case result
    showTestCase(results[0].stderr, results[0].input, results[0].stdout, results[0].output, results[0].expected, buttons[0]);
}

// Display a single test case result
function showTestCase(stderr, input, stdout, output, expected, activeButton, initial=false) {
    // Error container and text
    let stderrContainer = document.getElementById("stderr-container");
    let stderrText = document.getElementById("stderr-text");

    // Expected output and input test cases
    document.getElementById("expected-text").innerHTML = `${expected}`;
    document.getElementById("input-text").innerHTML = `${input}`;

    // Stdout container and text
    let stdoutContainer = document.getElementById("stdout-container");
    let stdoutText = document.getElementById("stdout-text");

    // Output block and text
    const outputContainer = document.getElementById('output-container');
    outputContainer.style.display = "block";
    const outputText = document.getElementById('output-text');

    // Update button styles
    document.querySelectorAll("#test-case-buttons button").forEach(btn => {
        btn.classList.remove("btn-primary", "active");
    });
    activeButton.classList.add("btn-primary", "active");

    // Handle errors
    if (stderr) {
        outputContainer.style.display = "none";
        stdoutContainer.style.display = "none";
        stderrText.innerHTML = `<pre style="color: red">${stderr}</pre>`;
        stderrContainer.style.display = "block"; // Show stderr box
        return;
    } else {
        stderrContainer.style.display = "none"; // Hide if empty
    }

    // Handle print statements
    if (stdout) {
        stdoutContainer.style.display = "block"; // Show stdout box
        stdoutText.innerHTML = `<pre>${stdout.join("\n")}</pre>`;
    } else {
        stdoutContainer.style.display = "none"; // Hide if empty
    }

    // Check type of output (show output if we have run code at least once)
    if (!initial) {
        outputContainer.style.display = "block"; // Show stdout box
        outputText.innerHTML = formatOutput(output);
    } else {
        outputContainer.style.display = "none"; // Hide output box if null or undefined
    }
}

// Utility function to format output based on type
function formatOutput(value) {
    // Handle complex numbers (convert to string)
    if (typeof value === 'string' && value.includes('j')) {
        return `"${value}"`; // Handle complex numbers as string (e.g., "3+4j")
    }

    // Handle string values
    if (typeof value === 'string') {
        return `"${value}"`; // Wrap string in quotes
    }

    // Handle arrays
    else if (Array.isArray(value)) {
        return `[${value.map(formatOutput).join(', ')}]`; // Wrap array in brackets
    }

    // Handle null values
    else if (value === null) {
        return 'null'; // Display null as is
    }

    // Handle other types (numbers, booleans, etc.)
    else {
        return String(value);
    }
}