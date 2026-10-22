// Standalone pages do not load the tutorial catalogue's script.js handlers.
(() => {
  const menu = document.getElementById('mobile-menu');
  const trigger = document.querySelector('button[aria-controls="mobile-menu"]');
  if (!menu || !trigger) return;

  const isOpen = () => !menu.classList.contains('hidden');
  const close = () => {
    menu.classList.add('hidden');
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
})();
