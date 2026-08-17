(() => {
  let tabSetCounter = 0;

  function initialiseCodeTabs(container) {
    const tabs = Array.from(container.querySelectorAll('[role="tab"]'));
    const panels = Array.from(container.querySelectorAll('[role="tabpanel"]'));
    if (!tabs.length || !panels.length) return;

    const activate = (tab, focus = false) => {
      const panelId = tab.getAttribute('aria-controls');
      tabs.forEach((item) => {
        const active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
        item.classList.toggle('is-active', active);
      });
      panels.forEach((panel) => {
        panel.hidden = panel.id !== panelId;
      });
      if (focus) tab.focus();
    };

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => activate(tab));
      tab.addEventListener('keydown', (event) => {
        let nextIndex = null;
        if (event.key === 'ArrowRight' || event.key === 'ArrowDown') nextIndex = (index + 1) % tabs.length;
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') nextIndex = (index - 1 + tabs.length) % tabs.length;
        if (event.key === 'Home') nextIndex = 0;
        if (event.key === 'End') nextIndex = tabs.length - 1;
        if (nextIndex !== null) {
          event.preventDefault();
          activate(tabs[nextIndex], true);
        }
      });
    });

    const selected = tabs.find((tab) => tab.getAttribute('aria-selected') === 'true') || tabs[0];
    activate(selected);
  }

  function makeTabButton(id, label, panelId, selected) {
    const button = document.createElement('button');
    button.id = id;
    button.className = `code-tab-button${selected ? ' is-active' : ''}`;
    button.type = 'button';
    button.setAttribute('role', 'tab');
    button.setAttribute('aria-selected', String(selected));
    button.setAttribute('aria-controls', panelId);
    if (!selected) button.tabIndex = -1;
    button.textContent = label;
    return button;
  }

  function getLanguage(code) {
    if (code.classList.contains('language-python')) return 'python';
    if (code.classList.contains('language-r')) return 'r';
    return null;
  }

  function upgradeAdjacentLanguagePairs() {
    const codeBlocks = Array.from(document.querySelectorAll('pre > code.language-python, pre > code.language-r'));

    codeBlocks.forEach((firstCode) => {
      const firstPre = firstCode.parentElement;
      if (!firstPre || firstPre.closest('[data-code-tabs]')) return;

      const firstLanguage = getLanguage(firstCode);
      const secondPre = firstPre.nextElementSibling;
      const secondCode = secondPre && secondPre.matches('pre')
        ? secondPre.querySelector(':scope > code.language-python, :scope > code.language-r')
        : null;
      const secondLanguage = secondCode ? getLanguage(secondCode) : null;

      if (!secondCode || !firstLanguage || !secondLanguage || firstLanguage === secondLanguage || secondPre.closest('[data-code-tabs]')) {
        return;
      }

      tabSetCounter += 1;
      const prefix = `paired-code-${tabSetCounter}`;
      const firstPanelId = `${prefix}-${firstLanguage}-panel`;
      const secondPanelId = `${prefix}-${secondLanguage}-panel`;

      const container = document.createElement('div');
      container.className = 'code-tabs';
      container.dataset.codeTabs = '';

      const tabList = document.createElement('div');
      tabList.className = 'code-tab-list';
      tabList.setAttribute('role', 'tablist');
      tabList.setAttribute('aria-label', 'Equivalent Python and R code examples');
      tabList.append(
        makeTabButton(`${prefix}-${firstLanguage}-tab`, firstLanguage === 'python' ? 'Python' : 'R', firstPanelId, true),
        makeTabButton(`${prefix}-${secondLanguage}-tab`, secondLanguage === 'python' ? 'Python' : 'R', secondPanelId, false)
      );

      const firstPanel = document.createElement('div');
      firstPanel.id = firstPanelId;
      firstPanel.className = 'code-tab-panel';
      firstPanel.setAttribute('role', 'tabpanel');
      firstPanel.setAttribute('aria-labelledby', `${prefix}-${firstLanguage}-tab`);

      const secondPanel = document.createElement('div');
      secondPanel.id = secondPanelId;
      secondPanel.className = 'code-tab-panel';
      secondPanel.setAttribute('role', 'tabpanel');
      secondPanel.setAttribute('aria-labelledby', `${prefix}-${secondLanguage}-tab`);
      secondPanel.hidden = true;

      // Insert the container before moving either original block into its panel.
      firstPre.replaceWith(container);
      container.append(tabList, firstPanel, secondPanel);
      firstPanel.append(firstPre);
      secondPanel.append(secondPre);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    upgradeAdjacentLanguagePairs();
    document.querySelectorAll('[data-code-tabs]').forEach(initialiseCodeTabs);
  });
})();
