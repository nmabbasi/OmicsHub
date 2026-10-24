/* Progressive enhancement only: source lessons retain both complete language routes. */
(() => {
  'use strict';
  const preferenceKey = 'omicsHubCodeLanguage';
  const controllers = [];
  let preference = null;
  try { preference = sessionStorage.getItem(preferenceKey); } catch (_) { /* Storage is optional. */ }

  async function fingerprint(text) {
    if (!window.crypto?.subtle || !window.TextEncoder) return null;
    const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, '0')).join('');
  }

  function validGroupRanges(groups, nodes) {
    if (!Array.isArray(groups)) return false;
    const occupied = new Set();
    return groups.every(group => {
      if (!group || typeof group.title !== 'string' || !Array.isArray(group.panels) || group.panels.length !== 2 || !Array.isArray(group.members)) return false;
      const [first, second] = group.panels;
      if (new Set(group.panels.map(panel => panel?.language)).size !== 2) return false;
      for (const panel of group.panels) {
        if (!panel || !['r', 'python'].includes(panel.language) || typeof panel.label !== 'string' ||
            !Number.isInteger(panel.start) || !Number.isInteger(panel.end) ||
            panel.start < 0 || panel.start > panel.end || panel.end >= nodes.length) return false;
      }
      if (first.end + 1 !== second.start || group.members.length !== second.end - first.start + 1) return false;
      return group.members.every((member, offset) => {
        const index = first.start + offset;
        if (!member || member.index !== index || !nodes[index] || occupied.has(index)) return false;
        occupied.add(index);
        return typeof member.sha256 === 'string' && typeof member.tag === 'string';
      });
    });
  }

  function selectLanguage(language, origin, focus = false, remember = true) {
    const oldTop = origin?.container.getBoundingClientRect().top;
    controllers.forEach(controller => controller.activate(language, controller === origin && focus));
    if (remember) {
      preference = language;
      try { sessionStorage.setItem(preferenceKey, language); } catch (_) { /* Native reading still works. */ }
    }
    // Switching earlier stages must not pull the current stage out of view.
    if (origin && oldTop >= 0 && oldTop < innerHeight) {
      const delta = origin.container.getBoundingClientRect().top - oldTop;
      if (Math.abs(delta) > 1) window.scrollBy({ top: delta, behavior: 'instant' });
    }
  }

  function createGroup(article, nodes, group, index) {
    const container = document.createElement('section');
    container.className = 'code-tabs tutorial-language-group';
    container.dataset.codeTabs = '';
    const prefix = `tutorial-language-${index + 1}`;
    const heading = document.createElement('div');
    heading.className = 'code-tabs-heading';
    const title = document.createElement('p');
    title.id = `${prefix}-title`;
    title.className = 'code-tabs-title';
    title.textContent = group.title;
    const hint = document.createElement('p');
    hint.className = 'code-tabs-hint';
    hint.textContent = 'Choose R or Python. Follow the same language through this lesson.';
    heading.append(title, hint);
    const tabList = document.createElement('div');
    tabList.className = 'code-tab-list';
    tabList.setAttribute('role', 'tablist');
    tabList.setAttribute('aria-labelledby', title.id);
    tabList.setAttribute('aria-orientation', 'horizontal');
    container.append(heading, tabList);
    const tabs = [];
    const panels = [];
    const controller = {
      container,
      activate(language, focus) {
        const selected = tabs.find(tab => tab.dataset.language === language) || tabs[0];
        tabs.forEach(tab => {
          const active = tab === selected;
          tab.setAttribute('aria-selected', String(active));
          tab.tabIndex = active ? 0 : -1;
          tab.classList.toggle('is-active', active);
        });
        panels.forEach(panel => { panel.hidden = panel.id !== selected.getAttribute('aria-controls'); });
        if (focus) selected.focus({ preventScroll: true });
      }
    };
    // All ranges and fingerprints have already passed before any original nodes move.
    article.insertBefore(container, nodes[group.panels[0].start]);
    group.panels.forEach((branch, branchIndex) => {
      const tab = document.createElement('button');
      tab.type = 'button';
      tab.id = `${prefix}-${branch.language}-tab`;
      tab.className = 'code-tab-button';
      tab.dataset.language = branch.language;
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-controls', `${prefix}-${branch.language}-panel`);
      const badge = document.createElement('span');
      badge.className = 'code-tab-language-icon';
      badge.setAttribute('aria-hidden', 'true');
      badge.textContent = branch.language === 'r' ? 'R' : 'Py';
      const label = document.createElement('span');
      label.textContent = branch.label;
      tab.append(badge, label);
      const panel = document.createElement('div');
      panel.id = `${prefix}-${branch.language}-panel`;
      panel.className = 'code-tab-panel';
      panel.dataset.language = branch.language;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', tab.id);
      panel.tabIndex = 0;
      tabs.push(tab); panels.push(panel);
      tabList.append(tab); container.append(panel);
      for (let member = branch.start; member <= branch.end; member += 1) panel.append(nodes[member]);
      tab.addEventListener('click', () => selectLanguage(branch.language, controller));
      tab.addEventListener('keydown', event => {
        let next = null;
        if (event.key === 'ArrowRight') next = (branchIndex + 1) % tabs.length;
        if (event.key === 'ArrowLeft') next = (branchIndex - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = tabs.length - 1;
        if (next !== null) {
          event.preventDefault();
          selectLanguage(tabs[next].dataset.language, controller, true);
        }
      });
    });
    controllers.push(controller);
    controller.activate(preference);
  }

  function revealHashTarget(scroll = false) {
    if (!location.hash) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    const panel = target?.closest('.code-tab-panel');
    if (!panel) return;
    const controller = controllers.find(item => item.container.contains(panel));
    selectLanguage(panel.dataset.language, controller, false, false);
    if (scroll) requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'instant' }));
  }

  async function initialise() {
    const article = document.querySelector('#tutorial-content > article');
    const slug = location.pathname.split('/').pop().replace(/\.html$/, '');
    const spec = window.OMICS_TUTORIAL_CODE?.tutorials?.[slug];
    let enhancedGroups = 0;
    try {
      if (article && spec) {
        const blocks = Array.from(article.querySelectorAll('pre'));
        const nodes = Array.from(article.children);
        const hashes = await Promise.all(blocks.map(pre => fingerprint((pre.querySelector('code') || pre).textContent)));
        const validBlocks = blocks.length === spec.blocks.length && hashes.every((hash, index) => hash && hash === spec.blocks[index].sha256);
        if (validBlocks) {
          blocks.forEach((pre, index) => {
            const code = pre.querySelector('code');
            const language = spec.blocks[index].language;
            pre.dataset.codeLanguage = language;
            if (code) {
              Array.from(code.classList).filter(name => name.startsWith('language-')).forEach(name => code.classList.remove(name));
              code.classList.add(`language-${language}`);
            }
          });
          const groups = spec.groups || [];
          if (validGroupRanges(groups, nodes)) {
            const prepared = await Promise.all(groups.map(async group => {
              const checks = await Promise.all(group.members.map(async member => {
                const node = nodes[member.index];
                return node.tagName.toLowerCase() === member.tag && await fingerprint(node.textContent) === member.sha256;
              }));
              return checks.every(Boolean);
            }));
            // Complete all range/content checks before moving any source nodes.
            groups.forEach((group, index) => {
              if (prepared[index]) {
                createGroup(article, nodes, group, index);
                enhancedGroups += 1;
              } else console.warn('Tutorial language group left visible: its reviewed structure has changed.');
            });
          } else {
            console.warn('Tutorial language groups left visible: invalid reviewed panel ranges.');
          }
        } else console.warn('Tutorial code left unchanged: its reviewed fingerprints have changed or are unavailable.');
        // Locally bundled Prism never needs a CDN or an autoloader request.
        if (window.Prism) article.querySelectorAll('pre > code').forEach(code => Prism.highlightElement(code));
        revealHashTarget(true);
        window.addEventListener('hashchange', () => revealHashTarget(true));
      }
    } catch (error) {
      // Do not hide instructional content when an enhancement fails.
      document.querySelectorAll('.code-tab-panel').forEach(panel => { panel.hidden = false; });
      console.warn('Tutorial enhancements unavailable; all language routes remain readable.', error);
    } finally {
      document.documentElement.dataset.tutorialCodeReady = 'true';
      document.dispatchEvent(new CustomEvent('tutorial-code-ready', { detail: { groups: enhancedGroups } }));
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialise, { once: true });
  else initialise();
})();
