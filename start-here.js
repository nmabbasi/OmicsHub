/* Progressive enhancement only: all core guidance and disclosures work without JS. */
(() => {
  'use strict';
  function revealHashTarget() {
    if (!location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    if (id === 'sh-hpc') target.querySelector('details')?.setAttribute('open', '');
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'instant' }));
  }
  document.addEventListener('DOMContentLoaded', revealHashTarget);
  window.addEventListener('hashchange', revealHashTarget);
  const printState = new Map();
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('main details').forEach(detail => {
      if (!printState.has(detail)) printState.set(detail, detail.open);
      detail.open = true;
    });
  });
  window.addEventListener('afterprint', () => {
    printState.forEach((open, detail) => { detail.open = open; });
    printState.clear();
  });
})();
