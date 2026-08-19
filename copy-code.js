document.addEventListener("DOMContentLoaded", () => {
  const preElements = document.querySelectorAll("pre");

  preElements.forEach((pre) => {
    // Ensure proper positioning context
    pre.style.position = "relative";

    // Create the copy button with text label
    const copyButton = document.createElement("button");
    copyButton.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg><span style="margin-left:4px">Copy</span>';
    copyButton.setAttribute("aria-label", "Copy code to clipboard");
    copyButton.setAttribute("title", "Copy to clipboard");

    Object.assign(copyButton.style, {
      position: "absolute",
      top: "10px",
      right: "10px",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "5px 12px",
      border: "1px solid rgba(255,255,255,0.15)",
      borderRadius: "6px",
      background: "rgba(255,255,255,0.08)",
      color: "rgba(255,255,255,0.55)",
      cursor: "pointer",
      fontSize: "0.72rem",
      fontWeight: "600",
      fontFamily: "'Inter', system-ui, sans-serif",
      letterSpacing: "0.02em",
      opacity: "0",
      transition: "opacity 0.2s ease, background 0.2s ease, color 0.2s ease, border-color 0.2s ease",
      zIndex: "10",
      lineHeight: "1"
    });

    // Show on hover of pre block
    pre.addEventListener("mouseenter", () => { copyButton.style.opacity = "1"; });
    pre.addEventListener("mouseleave", () => { copyButton.style.opacity = "0"; });

    // Button hover feedback
    copyButton.addEventListener("mouseenter", () => {
      copyButton.style.background = "rgba(255,255,255,0.16)";
      copyButton.style.color = "#ffffff";
      copyButton.style.borderColor = "rgba(255,255,255,0.3)";
    });
    copyButton.addEventListener("mouseleave", () => {
      copyButton.style.background = "rgba(255,255,255,0.08)";
      copyButton.style.color = "rgba(255,255,255,0.55)";
      copyButton.style.borderColor = "rgba(255,255,255,0.15)";
    });

    // Copy on click
    copyButton.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const code = pre.querySelector("code");
      const textToCopy = code ? code.innerText : pre.innerText;

      navigator.clipboard.writeText(textToCopy).then(() => {
        copyButton.innerHTML = '<svg width="14" height="14" fill="none" stroke="#4ade80" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg><span style="margin-left:4px;color:#4ade80">Copied!</span>';
        copyButton.style.borderColor = "rgba(74,222,128,0.3)";
        copyButton.style.background = "rgba(74,222,128,0.1)";
        setTimeout(() => {
          copyButton.innerHTML = '<svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg><span style="margin-left:4px">Copy</span>';
          copyButton.style.borderColor = "rgba(255,255,255,0.15)";
          copyButton.style.background = "rgba(255,255,255,0.08)";
        }, 2000);
      }).catch(() => {});
    });

    pre.appendChild(copyButton);
  });
});
