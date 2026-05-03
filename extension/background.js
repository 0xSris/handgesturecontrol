chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    gestureControl: {
      cursor_speed: 1.35,
      alpha: 0.3,
      dead_zone_radius: 0.04,
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
