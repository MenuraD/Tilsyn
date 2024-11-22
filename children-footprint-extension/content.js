// Function to detect form submissions
document.addEventListener('submit', function(event) {
    let form = event.target;
    let emailField = form.querySelector('input[type="email"]');  // Detects email input field

    if (emailField) {
        let email = emailField.value;
        let currentUrl = window.location.href;

        // Send email and URL data to the background script
        chrome.runtime.sendMessage({
            type: 'form_submission',
            email: email,
            url: currentUrl
        });
    }
});