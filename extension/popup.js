const MODES = ["cursor", "volume", "shortcuts", "media", "browser", "presentation", "share"];
const DEFAULT_SETTINGS = { cursor_speed: 1.35, alpha: 0.3, dead_zone_radius: 0.04, enabled: false };

const els = {
  dot: document.querySelector("#dot"),
  connection: document.querySelector("#connection"),
  toggle: document.querySelector("#toggle"),
  startApp: document.querySelector("#startApp"),
  state: document.querySelector("#state"),
  mode: document.querySelector("#mode"),
  fps: document.querySelector("#fps"),
  gesture: document.querySelector("#gesture"),
  modes: document.querySelector("#modes"),
  lock: document.querySelector("#lock"),
  cursor_speed: document.querySelector("#cursor_speed"),
  alpha: document.querySelector("#alpha"),
  dead_zone_radius: document.querySelector("#dead_zone_radius")
};

let socket;
let reconnectTimer;
let sliderTimer;
let settings = { ...DEFAULT_SETTINGS };

function send(command) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(command));
  }
}

function persist() {
  chrome.storage.sync.set({ gestureControl: settings });
}

function setConnected(connected) {
  els.dot.classList.toggle("connected", connected);
  els.connection.textContent = connected ? "Connected" : "Disconnected";
  els.startApp.classList.toggle("hidden", connected);
}

function connect() {
  clearTimeout(reconnectTimer);
  socket = new WebSocket("ws://localhost:7433");
  socket.addEventListener("open", () => setConnected(true));
  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    els.state.textContent = data.state ?? "LOCKED";
    els.mode.textContent = data.mode ?? "cursor";
    els.fps.textContent = data.fps ?? "0";
    els.gesture.textContent = data.gesture ?? "none";
    updateModeButtons(data.mode);
  });
  socket.addEventListener("close", () => {
    setConnected(false);
    reconnectTimer = setTimeout(connect, 2000);
  });
  socket.addEventListener("error", () => {
    setConnected(false);
    try {
      socket.close();
    } catch {
      reconnectTimer = setTimeout(connect, 2000);
    }
  });
}

function updateToggle() {
  els.toggle.textContent = settings.enabled ? "ON" : "OFF";
  els.toggle.classList.toggle("on", settings.enabled);
}

function updateModeButtons(activeMode) {
  document.querySelectorAll(".mode").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === activeMode);
  });
}

function debounceParam(key, value) {
  clearTimeout(sliderTimer);
  sliderTimer = setTimeout(() => send({ cmd: "set_param", key, value: Number(value) }), 300);
}

async function init() {
  const stored = await chrome.storage.sync.get("gestureControl");
  const local = await chrome.storage.local.get("pendingCommand");
  settings = { ...DEFAULT_SETTINGS, ...(stored.gestureControl ?? {}) };
  els.cursor_speed.value = settings.cursor_speed;
  els.alpha.value = settings.alpha;
  els.dead_zone_radius.value = settings.dead_zone_radius;
  updateToggle();

  MODES.forEach((mode) => {
    const button = document.createElement("button");
    button.className = "mode";
    button.dataset.mode = mode;
    button.textContent = mode;
    button.addEventListener("click", () => send({ cmd: "set_mode", mode }));
    els.modes.append(button);
  });

  els.toggle.addEventListener("click", () => {
    settings.enabled = !settings.enabled;
    updateToggle();
    persist();
    send({ cmd: "toggle" });
  });
  els.lock.addEventListener("click", () => send({ cmd: "lock" }));
  els.startApp.addEventListener("click", () => {
    window.location.href = "hgc://start";
  });

  ["cursor_speed", "alpha", "dead_zone_radius"].forEach((key) => {
    els[key].addEventListener("input", () => {
      settings[key] = Number(els[key].value);
      persist();
      debounceParam(key, els[key].value);
    });
  });

  connect();

  if (local.pendingCommand && Date.now() - local.pendingCommand.createdAt < 10000) {
    setTimeout(() => send(local.pendingCommand), 500);
    chrome.storage.local.remove("pendingCommand");
  }
}

init();
