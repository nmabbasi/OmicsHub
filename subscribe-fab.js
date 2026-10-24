/* Shared reader enhancements. Native links/history remain in charge of navigation. */
(() => {
  'use strict';
  const STORAGE_KEY = 'omicsHubCatalogueReturn';
  function readSavedResults() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY));
      if (!saved || typeof saved.href !== 'string') return null;
      const url = new URL(saved.href, location.origin);
      if (url.origin !== location.origin || !url.pathname.endsWith('/tutorials.html')) return null;
      return { href: url.href, y: Math.max(0, Math.min(Number(saved.y) || 0, 1000000)), card: saved.card || '' };
    } catch (_) { return null; }
  }
  function saveResults(card) {
    if (!document.getElementById('all-tutorials-list')) return;
    try {
      const old = readSavedResults();
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ href: location.href, y: scrollY, card: card || old?.card || '' }));
    } catch (_) { /* Ordinary links still work without browser storage. */ }
  }
  function initCompactCategories() {
    const strip = document.getElementById('category-filter');
    if (!strip || typeof window.filterTutorialsOnly !== 'function') return;
    const group = document.createElement('div');
    group.className = 'catalogue-category-select';
    const label = document.createElement('label');
    label.htmlFor = 'catalogue-category';
    label.textContent = 'Browse by category';
    const select = document.createElement('select');
    select.id = 'catalogue-category';
    strip.querySelectorAll('.category-btn').forEach(button => {
      const option = document.createElement('option');
      option.value = button.dataset.category;
      const count = button.querySelector('.category-count')?.textContent.trim();
      option.textContent = `${option.value === 'all' ? 'All tutorials' : option.value}${count ? ` (${count})` : ''}`;
      select.appendChild(option);
    });
    select.value = strip.querySelector('[aria-pressed="true"]')?.dataset.category || 'all';
    select.addEventListener('change', () => window.filterTutorialsOnly(select.value));
    group.append(label, select);
    strip.before(group);
    strip.parentElement.setAttribute('data-compact-categories', '');
  }
  function initResultReturnLinks() {
    const saved = readSavedResults();
    if (saved) {
      const filtered = new URL(saved.href).searchParams.size > 0;
      document.querySelectorAll('[data-catalogue-return]').forEach(link => {
        link.href = saved.href;
        const title = link.querySelector('strong');
        if (title) title.textContent = filtered ? 'Back to your results' : 'All tutorials';
        else link.textContent = filtered ? 'Back to results' : 'All tutorials';
      });
    }
    if (!document.getElementById('all-tutorials-list')) return;
    document.addEventListener('click', event => {
      const link = event.target.closest('#all-tutorials-list a[href]');
      if (link) saveResults(link.href);
    });
    window.addEventListener('pagehide', () => saveResults());
    window.addEventListener('pageshow', event => {
      if (event.persisted) return; // BFCache already restores viewport/focus.
      const state = readSavedResults();
      const referrer = document.referrer ? new URL(document.referrer) : null;
      const isReturn = performance.getEntriesByType('navigation')[0]?.type === 'back_forward' || (referrer?.origin === location.origin && /\/tutorials\/[^/]+\.html$/.test(referrer.pathname));
      if (!state || state.href !== location.href || !isReturn) return;
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const link = [...document.querySelectorAll('#all-tutorials-list a[href]')].find(a => a.href === state.card);
        link?.focus({ preventScroll: true });
        window.scrollTo({ top: state.y, behavior: 'instant' });
      }));
    });
  }
  function initInFlowTopControl() {
    const existing = document.getElementById('back-to-top');
    if (existing) {
      if (existing.matches('a[href="#tutorial-title"], a[href="#sh-hero-title"]')) {
        const tools = existing.closest('.reader-tools.tutorial-top-tools');
        const navigationFooter = document.querySelector('#reader-course-navigation .reader-sequence-footer');
        if (tools && navigationFooter) navigationFooter.appendChild(tools);
        if (tools) {
          tools.classList.add('is-floating');
          let scheduled = false;
          const update = () => {
            const focused = document.activeElement === existing;
            tools.hidden = window.scrollY < 240 && !focused;
            if (!tools.hidden && !focused) {
              const rect = existing.getBoundingClientRect();
              const headerBottom = document.querySelector('body > header')?.getBoundingClientRect().bottom || 0;
              const overlaps = [...document.querySelectorAll('main a, main button, main summary, main input, main select, main textarea, article button, #reader-course-navigation a:not(#back-to-top)')]
                .some(control => control !== existing && [...control.getClientRects()].some(box =>
                  box.width > 0 && box.height > 0 && box.left < rect.right + 4 && box.right > rect.left - 4 && box.top < rect.bottom + 4 && box.bottom > rect.top - 4));
              tools.hidden = overlaps || rect.top < headerBottom + 8;
            }
            scheduled = false;
          };
          const schedule = () => {
            if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
          };
          window.addEventListener('scroll', schedule, { passive: true });
          window.addEventListener('pageshow', schedule);
          window.addEventListener('resize', schedule, { passive: true });
          window.addEventListener('readerlayoutchange', schedule);
          document.addEventListener('toggle', schedule, true);
          existing.addEventListener('blur', schedule);
          update();
        }
        existing.addEventListener('click', () => {
          const title = document.getElementById(existing.hash.slice(1));
          if (title) {
            title.tabIndex = -1;
            title.focus({ preventScroll: true });
          }
        });
      }
      return;
    }
    const footer = document.querySelector('footer');
    if (!footer) return;
    const tools = document.createElement('div');
    tools.className = 'reader-tools';
    const button = document.createElement('button');
    button.id = 'back-to-top';
    button.type = 'button';
    button.textContent = 'Back to top ↑';
    button.addEventListener('click', () => {
      document.querySelector('header a[href]')?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
    });
    tools.appendChild(button);
    footer.before(tools);
  }
  function initLayoutMetrics() {
    const banner = document.getElementById('cookie-consent-banner');
    const header = document.querySelector('header');
    const row = header?.querySelector('nav > div:first-child');
    const update = () => {
      const h = banner && getComputedStyle(banner).display !== 'none' ? Math.ceil(banner.getBoundingClientRect().height) : 0;
      document.documentElement.style.setProperty('--reader-banner-space', `${h}px`);
      if (row && header) {
        const height = row.getBoundingClientRect().bottom - header.getBoundingClientRect().top + parseFloat(getComputedStyle(header.querySelector('nav')).paddingBottom) + 1;
        document.documentElement.style.setProperty('--reader-header-height', `${Math.ceil(height)}px`);
      }
      window.dispatchEvent(new Event('readerlayoutchange'));
    };
    if ('ResizeObserver' in window) {
      const observer = new ResizeObserver(update);
      if (banner) observer.observe(banner);
      if (row) observer.observe(row);
    }
    if (banner) new MutationObserver(update).observe(banner, { attributes: true, attributeFilter: ['class', 'style'] });
    window.addEventListener('resize', update, { passive: true });
    update();
  }
  function initIntentPrefetch() {
    if (navigator.connection?.saveData || /(^|-)2g$/.test(navigator.connection?.effectiveType || '')) return;
    const prefetched = new Set();
    const prefetch = event => {
      if (event.pointerType === 'touch') return;
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.target || anchor.hasAttribute('download')) return;
      const url = new URL(anchor.href, location.href);
      if (url.origin !== location.origin || !url.pathname.endsWith('.html') || url.pathname === location.pathname || prefetched.has(url.href) || prefetched.size >= 3) return;
      prefetched.add(url.href);
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url.href;
      document.head.appendChild(link);
    };
    document.addEventListener('pointerover', prefetch, { passive: true });
    document.addEventListener('focusin', prefetch);
  }
  document.addEventListener('DOMContentLoaded', () => {
    initCompactCategories();
    initResultReturnLinks();
    initInFlowTopControl();
    initLayoutMetrics();
    initIntentPrefetch();
    const input = document.querySelector('#home-page #search-input');
    if (input) {
      const original = input.placeholder;
      const narrow = matchMedia('(max-width: 639px)');
      const update = () => { input.placeholder = narrow.matches ? 'Search tutorials…' : original; };
      narrow.addEventListener('change', update);
      update();
    }
  });
})();
