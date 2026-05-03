chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    gestureControl: {
      cursor_speed: 2.1,
      alpha: 0.72,
      dead_zone_radius: 0.004,
      enabled: false
    }
  });
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "toggle-gesture-control") {
    chrome.storage.local.set({
      pendingCommand: { cmd: "toggle", createdAt: Date.now() }
    });
  }
});
