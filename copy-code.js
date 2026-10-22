document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("pre").forEach((pre, index) => {
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "code-copy-button";
    copyButton.textContent = "Copy code";
    copyButton.setAttribute("aria-label", "Copy code to clipboard");
    copyButton.title = "Copy code to clipboard";

    Object.assign(copyButton.style, {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      minWidth: "44px",
      minHeight: "44px",
      margin: "6px 0 12px",
      padding: "8px 12px",
      border: "1px solid #bfdbfe",
      borderRadius: "6px",
      background: "#eff6ff",
      color: "#123b5d",
      cursor: "pointer",
      font: "600 0.8rem/1.2 'Inter', system-ui, sans-serif"
    });

    copyButton.addEventListener("focus", () => {
      copyButton.style.outline = "2px solid currentColor";
      copyButton.style.outlineOffset = "2px";
    });
    copyButton.addEventListener("blur", () => {
      copyButton.style.outline = "";
      copyButton.style.outlineOffset = "";
    });

    const status = document.createElement("span");
    status.id = `code-copy-status-${index + 1}`;
    status.className = "code-copy-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    status.setAttribute("aria-atomic", "true");
    Object.assign(status.style, {
      display: "inline-block",
      minHeight: "44px",
      padding: "12px 8px",
      font: "400 0.8rem/1.2 'Inter', system-ui, sans-serif"
    });
    copyButton.setAttribute("aria-describedby", status.id);

    // Keep controls adjacent to, rather than inside or over, the code so
    // neither button text nor status can enter the copied selection.
    pre.insertAdjacentElement("afterend", copyButton);
    copyButton.insertAdjacentElement("afterend", status);

    copyButton.addEventListener("click", async () => {
      const code = pre.querySelector("code");
      const textToCopy = code ? code.textContent : pre.textContent;
      status.textContent = "";

      try {
        if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
          throw new Error("Clipboard API unavailable");
        }
        await navigator.clipboard.writeText(textToCopy);
        status.textContent = "Code copied to clipboard.";
      } catch (_error) {
        const selection = window.getSelection();
        if (selection) {
          const range = document.createRange();
          range.selectNodeContents(code || pre);
          selection.removeAllRanges();
          selection.addRange(range);
          status.textContent = "Clipboard access failed. Code is selected; copy it manually.";
        } else {
          status.textContent = "Clipboard access failed. Select the code and copy it manually.";
        }
      }
    });
  });
});
