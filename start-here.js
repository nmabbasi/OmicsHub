/* Progressive enhancement: direct anchors, all lessons and native details work without JS. */
(() => {
  'use strict';
  const main = document.getElementById('main-content');
  const panels = [...document.querySelectorAll('.sh-lesson-panel')];
  const links = [...document.querySelectorAll('[data-sh-step]')];
  const previous = document.querySelector('[data-sh-previous]');
  const next = document.querySelector('[data-sh-next]');
  const status = document.querySelector('.sh-step-status');
  const names = ['The big picture', 'Terminal navigation', 'Files and data', 'Choose R or Python'];
  let current = 1;
  const enhanced = main && panels.length === 4 && links.length === 8 && previous && next && status;

  function selectStep(number, { navigate = false, scroll = false } = {}) {
    if (!enhanced || !Number.isInteger(number) || number < 1 || number > panels.length) return;
    current = number;
    panels.forEach((panel, index) => { panel.hidden = index !== number - 1; });
    links.forEach(link => {
      if (Number(link.dataset.shStep) === number) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    });
    previous.disabled = number === 1;
    next.disabled = number === panels.length;
    status.textContent = `Viewing step ${number} of ${panels.length}: ${names[number - 1]}`;
    if (navigate && location.hash !== `#sh-step-${number}`) history.pushState(null, '', `#sh-step-${number}`);
    if (scroll && matchMedia('(max-width: 760px)').matches) panels[number - 1].scrollIntoView({ block: 'start', behavior: 'instant' });
  }

  function revealHashTarget() {
    if (!location.hash) {
      if (enhanced) selectStep(1);
      return;
    }
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    const panel = target.closest('.sh-lesson-panel');
    if (panel) selectStep(panels.indexOf(panel) + 1);
    for (let node = target; node; node = node.parentElement) {
      if (node.tagName === 'DETAILS') node.open = true;
    }
    if (id === 'sh-hpc') target.querySelector('details')?.setAttribute('open', '');
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'instant' }));
  }

  if (enhanced) {
    selectStep(1);
    main.classList.add('sh-enhanced');
    document.querySelector('.sh-orbit').hidden = false;
    document.querySelector('.sh-orbit-caption').hidden = false;
    document.querySelector('.sh-step-controls').hidden = false;
    links.forEach(link => link.addEventListener('click', event => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
      event.preventDefault();
      selectStep(Number(link.dataset.shStep), { navigate: true, scroll: true });
    }));
    previous.addEventListener('click', () => selectStep(current - 1, { navigate: true, scroll: true }));
    next.addEventListener('click', () => selectStep(current + 1, { navigate: true, scroll: true }));
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', revealHashTarget);
  else revealHashTarget();
  window.addEventListener('hashchange', revealHashTarget);
  window.addEventListener('popstate', revealHashTarget);

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
