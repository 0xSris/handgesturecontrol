const root = document.documentElement;
const toggle = document.querySelector("#theme-toggle");
const toggleText = toggle?.querySelector(".toggle-text");
const toggleIcon = toggle?.querySelector(".toggle-icon");
const copyButton = document.querySelector("#copy-command");
const command = document.querySelector("#run-command");

const savedTheme = localStorage.getItem("theme");
if (savedTheme === "light" || savedTheme === "dark") {
  root.dataset.theme = savedTheme;
}

function syncThemeButton() {
  const isLight = root.dataset.theme === "light";
  if (toggleText) {
    toggleText.textContent = isLight ? "Day" : "Night";
  }
  if (toggleIcon) {
    toggleIcon.textContent = isLight ? "☀" : "☾";
  }
}

syncThemeButton();

toggle?.addEventListener("click", () => {
  root.dataset.theme = root.dataset.theme === "light" ? "dark" : "light";
  localStorage.setItem("theme", root.dataset.theme);
  syncThemeButton();
});

copyButton?.addEventListener("click", async () => {
  const text = command?.innerText ?? "";
  try {
    await navigator.clipboard.writeText(text);
    copyButton.textContent = "Copied";
    setTimeout(() => {
      copyButton.textContent = "Copy command";
    }, 1400);
  } catch {
    copyButton.textContent = "Select command";
  }
});
