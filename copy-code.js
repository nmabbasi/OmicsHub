/* Copy controls stay outside code, so copied examples never include UI text. */
(() => {
  'use strict';
  const languageNames = { r: 'R', python: 'Python', bash: 'Bash', powershell: 'PowerShell', yaml: 'YAML', json: 'JSON', csv: 'CSV', text: 'Plain text', diff: 'Diff', lua: 'Lua', groovy: 'Groovy', javascript: 'JavaScript', markdown: 'Markdown', sql: 'SQL' };
  const copyIcon = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"></path></svg>';
  function initialise() {
    document.querySelectorAll('pre').forEach((pre, index) => {
      if (pre.closest('.tutorial-code-frame')) return;
      const code = pre.querySelector('code');
      const languageClass = Array.from(code?.classList || []).find(name => name.startsWith('language-'));
      const language = pre.dataset.codeLanguage || languageClass?.slice(9) || 'text';
      const languageName = languageNames[language] || language;
      const isText = ['text', 'csv', 'none'].includes(language);
      const action = isText ? 'Copy text' : 'Copy code';
      const frame = document.createElement('div');
      frame.className = 'tutorial-code-frame';
      const toolbar = document.createElement('div');
      toolbar.className = 'code-block-toolbar';
      const label = document.createElement('span');
      label.className = 'code-block-language';
      label.textContent = languageName;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'code-copy-button';
      button.innerHTML = copyIcon;
      const buttonText = document.createElement('span');
      buttonText.textContent = action;
      button.append(buttonText);
      button.setAttribute('aria-label', `${action}: ${languageName} example ${index + 1}`);
      button.title = `${action} to clipboard`;
      const status = document.createElement('span');
      status.id = `code-copy-status-${index + 1}`;
      status.className = 'code-copy-status code-feedback-visually-hidden';
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'true');
      button.setAttribute('aria-describedby', status.id);
      pre.before(frame);
      toolbar.append(label, button);
      frame.append(toolbar, pre, status);
      pre.tabIndex = 0;
      pre.setAttribute('role', 'region');
      pre.setAttribute('aria-label', `${languageName} example ${index + 1}, horizontally scrollable`);
      let resetTimer;
      button.addEventListener('click', async () => {
        clearTimeout(resetTimer);
        const text = code ? code.textContent : pre.textContent;
        status.textContent = '';
        status.classList.add('code-feedback-visually-hidden');
        button.classList.remove('is-copied');
        button.disabled = true;
        try {
          if (typeof navigator.clipboard?.writeText !== 'function') throw new Error('Clipboard unavailable');
          await navigator.clipboard.writeText(text);
          buttonText.textContent = 'Copied';
          button.classList.add('is-copied');
          status.textContent = `${languageName} example copied to clipboard.`;
          resetTimer = window.setTimeout(() => {
            buttonText.textContent = action;
            button.classList.remove('is-copied');
          }, 2200);
        } catch (_) {
          buttonText.textContent = action;
          const selection = window.getSelection();
          if (selection) {
            const range = document.createRange();
            range.selectNodeContents(code || pre);
            selection.removeAllRanges(); selection.addRange(range);
            status.textContent = 'Clipboard access failed. The example is selected; copy it manually.';
          } else status.textContent = 'Clipboard access failed. Select the example and copy it manually.';
          status.classList.remove('code-feedback-visually-hidden');
        } finally { button.disabled = false; }
      });
    });
  }
  document.addEventListener('tutorial-code-ready', initialise, { once: true });
  function onReady() {
    if (!document.querySelector('#tutorial-content > article') || document.documentElement.dataset.tutorialCodeReady === 'true') initialise();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', onReady, { once: true });
  else onReady();
})();
