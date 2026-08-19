/* Floating Back-to-Top Button (Universal) */
document.addEventListener("DOMContentLoaded", () => {
  if (!document.getElementById("back-to-top")) {
    const topBtn = document.createElement("button");
    topBtn.id = "back-to-top";
    topBtn.setAttribute("aria-label", "Back to top");
    topBtn.innerHTML = '<svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>';
    Object.assign(topBtn.style, {
      position: "fixed",
      bottom: "2rem",
      right: "2rem",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      width: "44px",
      height: "44px",
      padding: "0",
      border: "none",
      borderRadius: "50%",
      background: "#2563EB",
      color: "#ffffff",
      cursor: "pointer",
      boxShadow: "0 4px 14px rgba(37,99,235,0.35)",
      zIndex: "9998",
      opacity: "0",
      visibility: "hidden",
      transition: "opacity 0.25s, visibility 0.25s, transform 0.2s, background 0.2s"
    });
    topBtn.addEventListener("mouseenter", () => { topBtn.style.background = "#1D4ED8"; topBtn.style.transform = "translateY(-2px)"; });
    topBtn.addEventListener("mouseleave", () => { topBtn.style.background = "#2563EB"; topBtn.style.transform = "translateY(0)"; });
    topBtn.addEventListener("click", () => { window.scrollTo({ top: 0, behavior: "smooth" }); });
    document.body.appendChild(topBtn);
  }

  const onScroll = () => {
    const y = window.scrollY || window.pageYOffset;
    const show = y > 300;
    const topBtn = document.getElementById("back-to-top");
    if (topBtn) {
      topBtn.style.opacity = show ? "1" : "0";
      topBtn.style.visibility = show ? "visible" : "hidden";
    }
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});
