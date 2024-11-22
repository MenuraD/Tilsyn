document.addEventListener('DOMContentLoaded', function() {
    let logContainer = document.getElementById('log');
    
    // Fetch stored registration data
    chrome.storage.local.get({ registrations: [] }, function(data) {
        let registrations = data.registrations;
        
        registrations.forEach(function(entry) {
            let div = document.createElement('div');
            div.classList.add('entry');
            div.textContent = `Email: ${entry.email} - URL: ${entry.url} (Time: ${entry.timestamp})`;
            logContainer.appendChild(div);
        });
    });
    
    // Clear log functionality
    document.getElementById('clear-log').addEventListener('click', function() {
        chrome.storage.local.set({ registrations: [] }, function() {
            logContainer.innerHTML = '';  // Clear the display
        });
    });
});