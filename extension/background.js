chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'form_submission') {
        console.log("🚀 Email Captured:", message.email, "at", message.url);

        // Store the data locally
        chrome.storage.local.get({ registrations: [] }, function (data) {
            let registrations = data.registrations;
            registrations.push({
                email: message.email,
                url: message.url,
                timestamp: new Date().toISOString()
            });
            chrome.storage.local.set({ registrations: registrations });
        });

        // Send the data to the backend server
        fetch("http://127.0.0.1:5000/api/track-email", {
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
        .then((response) => response.json())
        .then((data) => {
            console.log("✅ Server Response:", data);
        })
        .catch((err) => console.error("❌ Error sending data to server:", err));
    }
});