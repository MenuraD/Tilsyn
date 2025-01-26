document.addEventListener('submit', function (event) {
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]');

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

// Track manual login events (clicking a login button)
document.addEventListener('click', function (event) {
    if (event.target.tagName === 'BUTTON' || event.target.type === 'submit') {
        const form = event.target.closest('form');
        if (form) {
            const emailInput = form.querySelector('input[type="email"]');
            if (emailInput) {
                const email = emailInput.value;
                const url = window.location.href;

                chrome.runtime.sendMessage({
                    type: 'form_submission',
                    email: email,
                    url: url
                });
            }
        }
    }
});