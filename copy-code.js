document.addEventListener("DOMContentLoaded", () => {
  // Find all <pre> tags (which contain the code blocks)
  const preElements = document.querySelectorAll("pre");

  preElements.forEach((pre) => {
    // Make sure the <pre> block is relative so we can position the button inside it
    if (getComputedStyle(pre).position === "static") {
      pre.style.position = "relative";
    }

    // Create the copy button
    const copyButton = document.createElement("button");
    copyButton.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>`;
    copyButton.className = "absolute top-2 right-2 bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white p-2 rounded-md transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 z-10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity";
    copyButton.setAttribute("aria-label", "Copy code");
    copyButton.setAttribute("title", "Copy to clipboard");

    // We want the button to appear on hover of the pre block
    pre.classList.add("group");

    // Add click event to copy text
    copyButton.addEventListener("click", () => {
      const code = pre.querySelector("code");
      const textToCopy = code ? code.innerText : pre.innerText;

      navigator.clipboard.writeText(textToCopy).then(() => {
        // Change icon to a checkmark temporarily
        copyButton.innerHTML = `<svg class="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>`;
        setTimeout(() => {
          // Revert back to copy icon
          copyButton.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>`;
        }, 2000);
      }).catch(err => {
        console.error("Failed to copy code: ", err);
      });
    });

    pre.appendChild(copyButton);
  });
});
