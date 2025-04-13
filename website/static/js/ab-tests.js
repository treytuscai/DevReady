// Run A/B Test logic only on specific pages
(function () {
    // Abort if not on relevant page
    if (!document.getElementById('hint-btn') || !document.getElementById('submit-btn')) return;
  
    const pageLoadTime = new Date().getTime();
    const group = Math.random() < 0.5 ? 'A' : 'B';
    let hintClicked = false;
  
    document.addEventListener('DOMContentLoaded', () => {
      // Adjust UI for Group B
      if (group === 'B') {
        const hintButton = document.getElementById('hint-btn');
        hintButton.classList.remove(...hintButton.classList);
        hintButton.classList.add('btn', 'btn-run');
  
        const submitButton = document.getElementById('submit-btn');
        submitButton.parentNode.insertBefore(hintButton, submitButton.nextSibling);
      }
  
      // Track "Get Hint" click
      const hintButton = document.getElementById('hint-btn');
      hintButton.addEventListener('click', () => {
        hintClicked = true;
        gtag('event', 'click', {
          event_category: 'AI Helper',
          event_label: 'Get Hint Button',
          value: 1,
          event_category: 'Group ' + group
        });
      });
  
      // Track submission and time spent
      const submitButton = document.getElementById('submit-btn');
      submitButton.addEventListener('click', () => {
        const submitTime = new Date().getTime();
        const timeSpent = (submitTime - pageLoadTime) / 1000;
  
        gtag('event', 'submit', {
          event_category: 'Submission',
          event_label: hintClicked ? 'Hint Used' : 'No Hint Used',
          value: timeSpent,
          event_category: 'Group ' + group
        });
      });
    });
  })();
  