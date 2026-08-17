(() => {
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
        const active = panel.id === panelId;
        panel.hidden = !active;
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

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-code-tabs]').forEach(initialiseCodeTabs);
  });
})();
