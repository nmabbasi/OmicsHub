/* Shared reader enhancements. Native links/history remain in charge of navigation. */
(() => {
  'use strict';
  const STORAGE_KEY = 'omicsHubCatalogueReturn';
  const sharedScriptURL = document.currentScript?.src || new URL('subscribe-fab.js', location.href).href;
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
    if (!strip || document.getElementById('catalogue-category') || typeof window.filterTutorialsOnly !== 'function') return;
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
    const cssPath = '/back-to-top.css';
    let stylesheet = [...document.querySelectorAll('link[rel="stylesheet"][href]')]
      .find(link => new URL(link.href, location.href).pathname.endsWith(cssPath));
    let stylesheetReady;
    if (stylesheet?.sheet) {
      stylesheetReady = Promise.resolve();
    } else if (stylesheet) {
      stylesheetReady = new Promise(resolve => {
        stylesheet.addEventListener('load', resolve, { once: true });
        stylesheet.addEventListener('error', resolve, { once: true });
      });
    } else {
      stylesheet = document.createElement('link');
      stylesheet.rel = 'stylesheet';
      stylesheet.href = new URL('back-to-top.css?v=20261024-sitewide-circle', sharedScriptURL).href;
      stylesheetReady = new Promise(resolve => {
        stylesheet.addEventListener('load', resolve, { once: true });
        stylesheet.addEventListener('error', resolve, { once: true });
      });
      document.head.appendChild(stylesheet);
    }

    let existing = document.getElementById('back-to-top');
    let tools = existing?.closest('.reader-tools.tutorial-top-tools');
    if (existing) {
      tools ||= existing.parentElement;
      tools.classList.add('reader-tools', 'tutorial-top-tools');
    } else {
      const heading = document.querySelector('main h1') || document.querySelector('h1');
      if (!heading) return;
      if (!heading.id) {
        const baseId = 'site-page-title';
        let id = baseId;
        let suffix = 2;
        while (document.getElementById(id)) id = `${baseId}-${suffix++}`;
        heading.id = id;
      }
      tools = document.createElement('div');
      tools.className = 'reader-tools tutorial-top-tools';
      existing = document.createElement('a');
      existing.id = 'back-to-top';
      existing.href = `#${heading.id}`;
      existing.setAttribute('aria-label', 'Back to top');
      const icon = document.createElement('span');
      icon.className = 'tutorial-top-icon';
      icon.setAttribute('aria-hidden', 'true');
      icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5m-6 6 6-6 6 6"/></svg>';
      const label = document.createElement('span');
      label.textContent = 'Back to top';
      existing.append(icon, label);
      tools.appendChild(existing);
      const footer = document.querySelector('footer');
      if (footer) footer.before(tools);
      else document.body.appendChild(tools);
    }

    // The native hidden attribute prevents an unstyled link flash while a newly
    // referenced shared stylesheet loads, and keeps it absent before scrolling.
    tools.hidden = true;
    tools.classList.add('is-floating');
    const navigationFooter = document.querySelector('#reader-course-navigation .reader-sequence-footer');
    if (existing.matches('a[href="#tutorial-title"]') && navigationFooter) navigationFooter.appendChild(tools);

    existing.addEventListener('click', event => {
      const target = existing.hash ? document.getElementById(existing.hash.slice(1)) : null;
      if (!target || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

      event.preventDefault();
      if (location.hash) {
        const cleanUrl = `${location.pathname}${location.search}`;
        try {
          if (typeof window.history.replaceState === 'function') {
            window.history.replaceState(window.history.state, '', cleanUrl);
          } else {
            window.location.replace(cleanUrl);
          }
        } catch (error) {
          window.location.replace(cleanUrl);
        }
      }
      target.tabIndex = -1;
      try {
        target.focus({ preventScroll: true });
      } catch (error) {
        target.focus();
      }
      const scrollTarget = () => {
        const currentY = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || 0;
        const targetY = target.getBoundingClientRect().top + currentY;
        window.scrollTo(0, targetY);
      };
      try {
        if (typeof target.scrollIntoView === 'function') {
          try {
            target.scrollIntoView({ block: 'start' });
          } catch (error) {
            target.scrollIntoView(true);
          }
        } else {
          scrollTarget();
        }
      } catch (error) {
        scrollTarget();
      }
    });

    stylesheetReady.then(() => {
      let scheduled = false;
      const update = () => {
        const focused = document.activeElement === existing;
        tools.hidden = window.scrollY < 240 && !focused;
        if (!tools.hidden && !focused) {
          const rect = existing.getBoundingClientRect();
          const headerBottom = document.querySelector('body > header')?.getBoundingClientRect().bottom || 0;
          const intersects = box => box.width > 0 && box.height > 0 &&
            box.left < rect.right + 7 && box.right > rect.left - 7 &&
            box.top < rect.bottom + 7 && box.bottom > rect.top - 7;
          const controls = document.querySelectorAll('body a[href], body button, body summary, body input, body select, body textarea, body [tabindex]');
          const controlOverlap = [...controls].some(control => control !== existing && [...control.getClientRects()].some(intersects));
          // Measure text fragments, not full-width paragraph boxes: the circle
          // uses whitespace only and yields to content, forms, navigation, and footer text.
          const reading = document.querySelectorAll('body h1, body h2, body h3, body h4, body h5, body h6, body p, body li, body pre, body figcaption, body td, body th, body blockquote, body label, body dt, body dd, body address');
          const textOverlap = !controlOverlap && [...reading].some(block => {
            if (block.contains(existing) || !block.getClientRects().length) return false;
            const bounds = block.getBoundingClientRect();
            if (!intersects(bounds)) return false;
            const range = document.createRange();
            range.selectNodeContents(block);
            return [...range.getClientRects()].some(intersects);
          });
          tools.hidden = controlOverlap || textOverlap || rect.top < headerBottom + 8;
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
    });
  }
  function initLayoutMetrics() {
    const banner = document.getElementById('cookie-consent-banner');
    const header = document.querySelector('header');
    const row = header?.querySelector('nav > div:first-child');
    const update = () => {
      const h = banner && getComputedStyle(banner).display !== 'none' ? Math.ceil(banner.getBoundingClientRect().height) : 0;
      let headerHeight;
      if (row && header) {
        const height = row.getBoundingClientRect().bottom - header.getBoundingClientRect().top + parseFloat(getComputedStyle(header.querySelector('nav')).paddingBottom) + 1;
        headerHeight = `${Math.ceil(height)}px`;
      }
      const rootStyle = document.documentElement.style;
      const bannerSpace = `${h}px`;
      const currentBannerSpace = rootStyle.getPropertyValue('--reader-banner-space');
      const currentHeaderHeight = headerHeight === undefined ? null : rootStyle.getPropertyValue('--reader-header-height');
      if (currentBannerSpace !== bannerSpace) rootStyle.setProperty('--reader-banner-space', bannerSpace);
      if (headerHeight !== undefined && currentHeaderHeight !== headerHeight) rootStyle.setProperty('--reader-header-height', headerHeight);
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
      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.target || anchor.hasAttribute('download')) return;
      const url = new URL(anchor.href, location.href);
      if (url.origin !== location.origin || !url.pathname.endsWith('.html') || url.pathname === location.pathname || prefetched.has(url.href) || prefetched.size >= 8) return;
      prefetched.add(url.href);
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url.href;
      document.head.appendChild(link);
    };
    document.addEventListener('pointerover', prefetch, { passive: true });
    document.addEventListener('touchstart', prefetch, { passive: true });
    document.addEventListener('focusin', prefetch);
  }
  function initNavigationGuard() {
    const getPageName = url => {
      try {
        const path = new URL(url, location.href).pathname.replace(/\/+$/, '');
        const file = path.split('/').pop() || 'index';
        return file.replace(/\.html$/, '') || 'index';
      } catch (_) { return ''; }
    };
    const currentPage = getPageName(location.href);

    const closeMobileMenu = () => {
      const menu = document.getElementById('mobile-menu');
      const trigger = document.querySelector('button[aria-controls="mobile-menu"]');
      if (menu && !menu.classList.contains('hidden')) {
        menu.classList.add('hidden');
        if (trigger) {
          trigger.setAttribute('aria-expanded', 'false');
          trigger.setAttribute('aria-label', 'Open navigation menu');
        }
      }
    };

    let inFlightTarget = '';
    let lastNavTime = 0;

    document.addEventListener('click', event => {
      const anchor = event.target.closest('header nav a[href], a[id^="nav-desktop-"], a[id^="nav-mobile-"], a[title="The Omics Hub home"], a[aria-label="Go to The Omics Hub home"], footer a[href]');
      if (!anchor || anchor.target || anchor.hasAttribute('download')) return;

      const href = anchor.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;

      const url = new URL(anchor.href, location.href);
      if (url.origin !== location.origin) return;

      const targetPage = getPageName(url.href);

      // Active tab zero-reload guard: if clicking current page tab, smoothly scroll to top and close menu
      if (targetPage === currentPage && !url.hash) {
        event.preventDefault();
        closeMobileMenu();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        return;
      }

      // Rapid-click debounce: ignore duplicate navigation requests to the same target within 800ms, or any rapid click within 350ms
      const now = Date.now();
      if ((inFlightTarget === targetPage && now - lastNavTime < 800) || (now - lastNavTime < 350)) {
        event.preventDefault();
        return;
      }

      lastNavTime = now;
      inFlightTarget = targetPage;
      closeMobileMenu();
      setTimeout(() => { inFlightTarget = ''; }, 1000);
    }, { capture: true });

    window.addEventListener('pageshow', () => { inFlightTarget = ''; });
    window.addEventListener('pagehide', () => { inFlightTarget = ''; });
  }
  const initAll = () => {
    initCompactCategories();
    initResultReturnLinks();
    initInFlowTopControl();
    initLayoutMetrics();
    initIntentPrefetch();
    initNavigationGuard();
    const input = document.querySelector('#home-page #search-input');
    if (input) {
      const original = input.placeholder;
      const narrow = matchMedia('(max-width: 639px)');
      const update = () => { input.placeholder = narrow.matches ? 'Search tutorials…' : original; };
      narrow.addEventListener('change', update);
      update();
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
