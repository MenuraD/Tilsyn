chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.type === 'form_submission') {
        console.log("Email: " + message.email + " was registered at " + message.url);
        
        // You can store this data locally or send it to a server
        chrome.storage.local.get({ registrations: [] }, function (data) {
            let registrations = data.registrations;
            registrations.push({
                email: message.email,
                url: message.url,
                timestamp: new Date().toISOString()
            });
            chrome.storage.local.set({ registrations: registrations });
        });
    }
});