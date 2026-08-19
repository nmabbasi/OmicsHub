document.addEventListener("DOMContentLoaded", () => {
  const preElements = document.querySelectorAll("pre");

  preElements.forEach((pre) => {
    // Ensure proper positioning context
    pre.style.position = "relative";

    // Create the copy button
    const copyButton = document.createElement("button");
    copyButton.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>';
    copyButton.setAttribute("aria-label", "Copy code");
    copyButton.setAttribute("title", "Copy to clipboard");

    // Style the button directly for maximum reliability
    Object.assign(copyButton.style, {
      position: "absolute",
      top: "8px",
      right: "8px",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      width: "32px",
      height: "32px",
      padding: "0",
      border: "none",
      borderRadius: "6px",
      background: "rgba(255,255,255,0.1)",
      color: "rgba(255,255,255,0.5)",
      cursor: "pointer",
      opacity: "0",
      transition: "opacity 0.2s, background 0.2s, color 0.2s",
      zIndex: "10"
    });

    // Show on hover
    pre.addEventListener("mouseenter", () => { copyButton.style.opacity = "1"; });
    pre.addEventListener("mouseleave", () => { copyButton.style.opacity = "0"; });
    copyButton.addEventListener("mouseenter", () => {
      copyButton.style.background = "rgba(255,255,255,0.2)";
      copyButton.style.color = "#ffffff";
    });
    copyButton.addEventListener("mouseleave", () => {
      copyButton.style.background = "rgba(255,255,255,0.1)";
      copyButton.style.color = "rgba(255,255,255,0.5)";
    });

    // Copy on click
    copyButton.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      const code = pre.querySelector("code");
      const textToCopy = code ? code.innerText : pre.innerText;

      navigator.clipboard.writeText(textToCopy).then(() => {
        copyButton.innerHTML = '<svg width="16" height="16" fill="none" stroke="#4ade80" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path></svg>';
        setTimeout(() => {
          copyButton.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>';
        }, 2000);
      }).catch(() => {});
    });

    pre.appendChild(copyButton);
  });
});
