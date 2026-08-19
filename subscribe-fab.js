/* Floating Subscribe + Back-to-Top Buttons (Universal) */
document.addEventListener("DOMContentLoaded", () => {

  /* ── 1. Back-to-Top Button (universal, for pages that don't have script.js) ── */
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

  /* ── 2. Subscribe Button ── */
  const sub = document.createElement("a");
  sub.id = "subscribe-fab";
  sub.setAttribute("aria-label", "Subscribe to newsletter");
  sub.setAttribute("title", "Get free tutorials & cheat sheets");

  const isInSubdir = window.location.pathname.includes("/pages/");
  const prefix = isInSubdir ? "../" : "";
  sub.href = prefix + "services.html#newsletter-title";

  sub.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg><span>Subscribe</span>';

  Object.assign(sub.style, {
    position: "fixed",
    bottom: "5rem",
    right: "2rem",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "9px 16px",
    borderRadius: "50px",
    background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
    color: "#ffffff",
    fontSize: "0.78rem",
    fontWeight: "700",
    fontFamily: "'Inter', system-ui, sans-serif",
    textDecoration: "none",
    boxShadow: "0 4px 14px rgba(37,99,235,0.4)",
    zIndex: "9998",
    opacity: "0",
    visibility: "hidden",
    transform: "translateY(8px)",
    transition: "opacity 0.3s, visibility 0.3s, transform 0.3s, background 0.2s, box-shadow 0.2s",
    cursor: "pointer",
    letterSpacing: "0.01em",
    lineHeight: "1"
  });

  sub.addEventListener("mouseenter", () => {
    sub.style.background = "linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%)";
    sub.style.boxShadow = "0 6px 20px rgba(37,99,235,0.55)";
    sub.style.transform = "translateY(-2px)";
  });
  sub.addEventListener("mouseleave", () => {
    sub.style.background = "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)";
    sub.style.boxShadow = "0 4px 14px rgba(37,99,235,0.4)";
    sub.style.transform = "translateY(0)";
  });

  document.body.appendChild(sub);

  /* ── 3. Scroll handler: show/hide both buttons ── */
  const onScroll = () => {
    const y = window.scrollY || window.pageYOffset;
    const show = y > 300;

    // Back-to-top
    const topBtn = document.getElementById("back-to-top");
    if (topBtn) {
      topBtn.style.opacity = show ? "1" : "0";
      topBtn.style.visibility = show ? "visible" : "hidden";
    }

    // Subscribe
    sub.style.opacity = show ? "1" : "0";
    sub.style.visibility = show ? "visible" : "hidden";
    if (show) sub.style.transform = "translateY(0)";
    else sub.style.transform = "translateY(8px)";
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
});
