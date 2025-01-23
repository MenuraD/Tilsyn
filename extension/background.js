// Listener for messages from content.js
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'form_submission' || message.type === 'login_attempt') {
        const logType = message.type === 'form_submission' ? "Registration" : "Login";
        console.log(`${logType} detected - Email: ${message.email}, URL: ${message.url}`);

        const storageKey = message.type === 'form_submission' ? "registrations" : "logins";

        // Store the data locally
        chrome.storage.local.get({ [storageKey]: [] }, function (data) {
            let logData = data[storageKey];
            logData.push({
                email: message.email,
                url: message.url,
                timestamp: new Date().toISOString()
            });
            chrome.storage.local.set({ [storageKey]: logData });
        });

        // Send the data to the backend server
        const apiEndpoint = message.type === 'form_submission' ? "/api/track-email" : "/api/track-login";

        fetch(`http://127.0.0.1:5000${apiEndpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email: message.email,
                url: message.url,
                timestamp: new Date().toISOString(),
            }),
        })
        .then((response) => {
            if (response.ok) {
                console.log(`${logType} data sent to server successfully.`);
            } else {
                console.error(`Failed to send ${logType} data to server. Status:`, response.status);
            }
        })
        .catch((err) => console.error(`Error sending ${logType} data to server:`, err));
    }
});