const copyButton = document.querySelector("#copy-command");
const command = document.querySelector("#run-command");

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
