chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    gestureControl: {
      cursor_speed: 2.4,
      alpha: 0.55,
      dead_zone_radius: 0.018,
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
