document.addEventListener("DOMContentLoaded", function () {
  let logContainer = document.getElementById("log");
  chrome.runtime.onInstalled.addListener(() => {
    chrome.notifications.getPermissionLevel((level) => {
      if (level !== "granted") {
        chrome.notifications.create({
          type: "basic",
          title: "Tilsyn Needs Permission",
          message: 'Click "Allow" to enable incognito alerts!',
          iconUrl: chrome.runtime.getURL("icon.png"),
          priority: 2,
        });
      }
    });
  });
  chrome.storage.local.get({ registrations: [] }, function (data) {
    let registrations = data.registrations;

    registrations.forEach(function (entry) {
      let div = document.createElement("div");
      div.classList.add("entry");
      div.textContent = `Email: ${entry.email} - URL: ${entry.url} (Time: ${entry.timestamp})`;
      logContainer.appendChild(div);
    });
  });
  document.getElementById("clear-log").addEventListener("click", function () {
    chrome.storage.local.set({ registrations: [] }, function () {
      logContainer.innerHTML = ""; 
    });
  });
});
