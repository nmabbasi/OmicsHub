// Standalone pages do not load the tutorial catalogue's script.js handlers.
(() => {
  const menu = document.getElementById('mobile-menu');
  const trigger = document.querySelector('button[aria-controls="mobile-menu"]');
  if (!menu || !trigger) return;

  const isOpen = () => !menu.classList.contains('hidden');
  const update = () => {
    const state = isOpen();
    menu.hidden = !state;
    menu.setAttribute('aria-hidden', String(!state));
  };
  if (typeof window.toggleMobileMenu === 'function') {
    const original = window.toggleMobileMenu;
    window.toggleMobileMenu = () => {
      original();
      update();
    };
  }
  update();

  const close = () => {
    menu.classList.add('hidden');
    update();
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-label', 'Open navigation menu');
  };

  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape' || event.defaultPrevented || !isOpen()) return;
    // Let modal dialogs and consent controls handle their own Escape key.
    if (document.querySelector('dialog[open]') ||
        document.getElementById('cookie-consent-banner')?.contains(document.activeElement)) return;
    close();
    trigger.focus();
  });

  document.addEventListener('click', (event) => {
    if (!isOpen()) return;
    const target = event.target instanceof Element ? event.target : event.target?.parentElement;
    if (!target) return;
    if (target.closest('#mobile-menu a') ||
        (!menu.contains(target) && !trigger.contains(target))) close();
  });

  // Move initial Cookie Preferences modal focus to its heading instead of the inline link.
  document.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : event.target?.parentElement;
    if (!target || !target.closest('[data-cookie-preferences]')) return;
    const focusHeading = () => {
      const panel = document.getElementById('cookie-preferences-panel');
      const heading = document.getElementById('cookie-preferences-heading');
      if (panel && panel.open && heading) {
        if (!heading.hasAttribute('tabindex')) heading.setAttribute('tabindex', '-1');
        heading.focus({ preventScroll: true });
      }
    };
    if (typeof window.requestAnimationFrame === 'function') window.requestAnimationFrame(focusHeading);
    else window.setTimeout(focusHeading, 0);
  });
})();
