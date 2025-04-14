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

    // Show loading message only for submissions
    const testCaseButtons = document.getElementById('test-case-buttons');
    const testCaseStatus = document.getElementById('test-case-status');

    testCaseStatus.innerHTML = "";

    // Display loading message if submission
    if (isSubmission) {
        testCaseStatus.innerHTML = `
          <div class="d-flex align-items-center gap-2">
            <span>Running test cases...</span>
            <div class="spinner-border text-primary" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
        `;
    }

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

//displays results of submission to user
//i.e. "19/20 test cases passed"
function displaySubmissionResults(results) {
    const testCaseButtons = document.getElementById('test-case-buttons');
    const testCaseStatus = document.getElementById('test-case-status');

    // Clear the right side first
    testCaseStatus.innerHTML = "";

    const passedCases = results.filter(test => test.passed).length;
    const totalCases = results.length;

    if (passedCases === totalCases) {
        //If all test cases passed, remove test case buttons
        testCaseButtons.innerHTML = "";

        //Display pass message
        const passMessage = document.createElement('span');
        passMessage.style.color = "green";
        passMessage.textContent = `Successful submission! ${passedCases}/${totalCases} test cases passed`;
        testCaseButtons.appendChild(passMessage);

        //Display analyze button
        const analyzeBtn = document.createElement('button');
        analyzeBtn.id = 'analyze-btn';
        analyzeBtn.className = 'btn btn-submit';
        analyzeBtn.style.marginLeft = "1rem";
        analyzeBtn.textContent = 'Analyze Time Complexity';
        analyzeBtn.onclick = analyzeTimeComplexity;
        analyzeBtn.setAttribute('data-bs-toggle', 'modal');
        analyzeBtn.setAttribute('data-bs-target', '#complexityModal');
        testCaseButtons.appendChild(analyzeBtn);

        if (!document.getElementById('complexityModal')) {
            createComplexityModal();
        }
    } else {
        //Keep test case buttons if failed submissions
        const failMessage = document.createElement('span');
        failMessage.style.color = "red";
        failMessage.textContent = `${passedCases}/${totalCases} test cases passed`;
        testCaseStatus.appendChild(failMessage);

        const buttons = testCaseButtons.querySelectorAll("button");
        results.slice(0, 3).forEach((test, i) => {
            if (i < buttons.length) {
                buttons[i].classList.remove("btn-testcase");
                buttons[i].classList.add(test.passed ? "btn-success" : "btn-danger");
            }
        });

        // Show the first test case details by default
        if (results.length > 0 && buttons.length > 0) {
            showTestCase(
                results[0].stderr,
                results[0].input,
                results[0].stdout,
                results[0].output,
                results[0].expected,
                buttons[0]
            );
        }
    }
}

//creates modal to display time complexity analysis results
function createComplexityModal() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'complexityModal';
    modal.tabIndex = '-1';
    modal.setAttribute('aria-labelledby', 'complexityModalLabel');
    modal.setAttribute('aria-hidden', 'true');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="complexityModalLabel">Time Complexity Analysis</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" id="complexity-modal-body">
                    <div class="d-flex justify-content-center">
                        <div class="simple-spinner"></div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}

//Pass code to analyze_complexity endpoint and await response
async function analyzeTimeComplexity() {
    //Get the question title element and content
    const questionTitleElement = document.getElementById("question-title");
    const questionTitle = questionTitleElement ? questionTitleElement.textContent.trim() : null;

    //Get editor and code
    const editor = ace.edit("editor");
    const code = editor.getValue();

    //Create payload
    const payload = {
        "code": code,
        "question": questionTitle
    };

    //Get modal body for results
    const modalBody = document.getElementById('complexity-modal-body');

    //Show loading spinner in modal
    modalBody.innerHTML = `
        <div class="d-flex justify-content-center">
            <div class="spinner-border text-orange" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;

    try {
        const res = await fetch(`/analyze_submission`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const result = await res.json();

        //Display the analysis result in modal
        modalBody.innerHTML = `
            <div class="mb-3">
                <span class="fw-bold">Time Complexity:</span> 
                <span>${result.analysis.timeComplexity || 'Not determined'}</span>
            </div>
            <div class="mb-3">
                <span class="fw-bold">Space Complexity:</span>
                <span>${result.analysis.spaceComplexity || 'Not determined'}</span>
            </div>
            ${result.analysis.explanation ? `
                <div class="mt-4">
                    <h6 class="fw-bold">Explanation:</h6>
                    <div class="p-3 bg-light border rounded">${result.analysis.explanation}</div>
                </div>` : ''}
        `;

    } catch (error) {
        modalBody.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Could not analyze time complexity.
                <div class="mt-2">${error.message}</div>
            </div>
        `;
    }
}

//Display a single test case result
function showTestCase(stderr, input, stdout, output, expected, activeButton, initial=false) {
    // Error container and text
    let stderrContainer = document.getElementById("stderr-container");
    let stderrText = document.getElementById("stderr-text");

    //Expected output and input test cases
    document.getElementById("expected-text").innerHTML = `${expected}`;
    document.getElementById("input-text").innerHTML = `${input}`;

    // Stdout container and text
    let stdoutContainer = document.getElementById("stdout-container");
    let stdoutText = document.getElementById("stdout-text");

    //Output block and text
    const outputContainer = document.getElementById('output-container');
    outputContainer.style.display = "block";
    const outputText = document.getElementById('output-text');

    //Update button styles
    document.querySelectorAll("#test-case-buttons button").forEach(btn => {
        btn.classList.remove("btn-primary", "active");
    });
    if (activeButton && activeButton.classList) {
        activeButton.classList.add("btn-primary", "active");
    }

    //Handle errors
    if (stderr) {
        outputContainer.style.display = "none";
        stdoutContainer.style.display = "none";
        stderrText.innerHTML = `<pre style="color: red">${stderr}</pre>`;
        stderrContainer.style.display = "block";
        return;
    } else {
        stderrContainer.style.display = "none";
    }

    // Handle print statements
    if (stdout) {
        stdoutContainer.style.display = "block";
        stdoutText.innerHTML = `<pre>${stdout.join("\n")}</pre>`;
    } else {
        stdoutContainer.style.display = "none";
    }

    if (!initial) {
        outputContainer.style.display = "block";
        outputText.innerHTML = output
    } else {
        outputContainer.style.display = "none";
    }
}
