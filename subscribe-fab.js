/* Floating Subscribe Button */
document.addEventListener("DOMContentLoaded", () => {
  // Create the floating subscribe button
  const btn = document.createElement("a");
  btn.id = "subscribe-fab";
  btn.setAttribute("aria-label", "Subscribe to newsletter");
  btn.setAttribute("title", "Subscribe for free tutorials & cheat sheets");

  // Determine the correct link based on current page
  const depth = (window.location.pathname.match(/\//g) || []).length;
  const isInSubdir = window.location.pathname.includes("/pages/");
  const prefix = isInSubdir ? "../" : "";
  btn.href = prefix + "services.html#newsletter-title";

  btn.innerHTML = `
    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
    </svg>
    <span>Subscribe</span>
  `;

  // Style using inline CSS for maximum reliability
  Object.assign(btn.style, {
    position: "fixed",
    bottom: "5.5rem",
    right: "2rem",
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    padding: "10px 18px",
    borderRadius: "50px",
    background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
    color: "#ffffff",
    fontSize: "0.82rem",
    fontWeight: "700",
    fontFamily: "'Inter', sans-serif",
    textDecoration: "none",
    boxShadow: "0 4px 14px rgba(37,99,235,0.4), 0 1px 3px rgba(0,0,0,0.1)",
    zIndex: "9998",
    opacity: "0",
    transform: "translateY(10px)",
    transition: "opacity 0.3s ease, transform 0.3s ease, background 0.2s ease, box-shadow 0.2s ease",
    cursor: "pointer",
    letterSpacing: "0.01em"
  });

  // Hover effect
  btn.addEventListener("mouseenter", () => {
    btn.style.background = "linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%)";
    btn.style.boxShadow = "0 6px 20px rgba(37,99,235,0.55), 0 2px 6px rgba(0,0,0,0.15)";
    btn.style.transform = "translateY(-2px)";
  });
  btn.addEventListener("mouseleave", () => {
    btn.style.background = "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)";
    btn.style.boxShadow = "0 4px 14px rgba(37,99,235,0.4), 0 1px 3px rgba(0,0,0,0.1)";
    btn.style.transform = "translateY(0)";
  });

  document.body.appendChild(btn);

  // Show after scrolling 300px (like back-to-top), or show immediately on shorter pages
  const showButton = () => {
    const scrollY = window.scrollY || window.pageYOffset;
    if (scrollY > 300) {
      btn.style.opacity = "1";
      btn.style.transform = "translateY(0)";
    } else {
      btn.style.opacity = "0";
      btn.style.transform = "translateY(10px)";
    }
  };

  window.addEventListener("scroll", showButton, { passive: true });

  // Show immediately if already scrolled
  showButton();
});
