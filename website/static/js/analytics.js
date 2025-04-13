document.addEventListener('DOMContentLoaded', () => {
    // 🧪 Sample Mock Data — Replace with real backend data
    const data = {
        aiUsage: { A: 45, B: 60 },
        assignments: { A: 100, B: 110 },
        hintImpact: {
            A: { hint: 32, noHint: 25 },
            B: { hint: 40, noHint: 30 }
        }
    };

    // 1️⃣ AI Usage Chart
    new Chart(document.getElementById('aiUsageChart'), {
        type: 'bar',
        data: {
            labels: ['Group A', 'Group B'],
            datasets: [{
                label: 'Hint Clicks',
                data: [data.aiUsage.A, data.aiUsage.B],
                backgroundColor: ['#007bff', '#fd7e14']
            }]
        },
        options: {
            plugins: {
                title: { display: true, text: 'Hint Button Clicks by Group' }
            },
            responsive: true
        }
    });

    // 2️⃣ Assignments Chart
    new Chart(document.getElementById('groupAssignmentChart'), {
        type: 'bar',
        data: {
            labels: ['Group A', 'Group B'],
            datasets: [{
                label: 'Assignments',
                data: [data.assignments.A, data.assignments.B],
                backgroundColor: ['#28a745', '#dc3545']
            }]
        },
        options: {
            plugins: {
                title: { display: true, text: 'A/B Group Distribution' }
            },
            responsive: true
        }
    });

    // 4️⃣ Hint Impact on Submission Time
    new Chart(document.getElementById('hintImpactChart'), {
        type: 'bar',
        data: {
            labels: ['Group A (Hint)', 'Group A (No Hint)', 'Group B (Hint)', 'Group B (No Hint)'],
            datasets: [{
                label: 'Avg Submit Time (sec)',
                data: [
                    data.hintImpact.A.hint,
                    data.hintImpact.A.noHint,
                    data.hintImpact.B.hint,
                    data.hintImpact.B.noHint
                ],
                backgroundColor: ['#0dcaf0', '#ffc107', '#0dcaf0', '#ffc107']
            }]
        },
        options: {
            plugins: {
                title: { display: true, text: 'Hint Impact on Submission Time' }
            },
            responsive: true
        }
    });
});
