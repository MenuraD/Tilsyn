chrome.alarms.create("keep-alive", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener(() => {}); 
let lifeline;
keepAlive();

function keepAlive() {
  lifeline = setInterval(chrome.runtime.getPlatformInfo, 25e3);
  chrome.runtime.onStartup.addListener(keepAlive);
}

chrome.runtime.onSuspend.addListener(() => {
  clearInterval(lifeline);
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "check_incognito") {
    console.log("Checking window ID:", sender.tab?.windowId);
    chrome.windows.get(sender.tab.windowId, (window) => {
      console.log("Window incognito status:", window.incognito);
      sendResponse({ isIncognito: window.incognito });
    });
    return true; 
  }
});

chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
  console.log("Received message:", message); 

  if (message.type === "form_submission" || message.type === "login_attempt") {
    console.log(
      "Captured:",
      message.email,
      "at",
      message.url,
      "Type:",
      message.type
    );

    chrome.storage.local.get(
      { registrations: [], logins: [] },
      function (data) {
        if (message.type === "form_submission") {
          data.registrations.push({
            email: message.email,
            url: message.url,
            timestamp: new Date().toISOString(),
          });
          chrome.storage.local.set({ registrations: data.registrations });
        } else if (message.type === "login_attempt") {
          data.logins.push({
            email: message.email,
            url: message.url,
            timestamp: new Date().toISOString(),
          });
          chrome.storage.local.set({ logins: data.logins });
        }
      }
    );

    let endpoint =
      message.type === "form_submission" ? "track-email" : "track-login";
    console.log("Sending to endpoint:", endpoint); 

    fetch(`http://127.0.0.1:5000/api/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: message.email,
        url: message.url,
        timestamp: new Date().toISOString(),
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Server Response:", data);
      })
      .catch((err) => console.error("Error sending data to server:", err));
  }
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete") {
    chrome.runtime.sendMessage({ type: "check_ip_now" });
  }
});

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "page_visit") {

    if (!message.url || !message.timestamp) {
      console.error("Missing URL/timestamp in message:", message);
      return;
    }

    if (message.isIncognito) {
      try {
        const urlHost = new URL(message.url).hostname; 
        chrome.notifications.create({
          type: "basic",
          iconUrl: chrome.runtime.getURL("icon.png"),
          title: "🚨 Incognito Alert!",
          message: `Child visited ${new URL(message.url).hostname} privately`,
          priority: 2,
        });
      } catch (err) {
        console.error("Notification failed:", err);
      }
    }

    const payload = {
      url: message.url,
      timestamp: message.timestamp,
      is_incognito: message.isIncognito || false, 
    };
    console.log("Sending visit data:", payload);

    fetch(`http://127.0.0.1:5000/api/track-visit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        return response.json();
      })
      .then((data) => console.log("Server response:", data))
      .catch((err) => console.error("Failed to send visit data:", err));
  }
});
