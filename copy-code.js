/* Copy controls, line numbers, wrap/expand toggles, TOC, progress bar, and figure lightbox stay outside code text. */
(() => {
  'use strict';
  const languageNames = {
    r: 'R',
    python: 'Python',
    bash: 'Bash',
    powershell: 'PowerShell',
    yaml: 'YAML',
    json: 'JSON',
    csv: 'CSV',
    text: 'Plain text',
    diff: 'Diff',
    lua: 'Lua',
    groovy: 'Groovy',
    javascript: 'JavaScript',
    markdown: 'Markdown',
    sql: 'SQL',
    ini: 'INI',
    docker: 'Docker'
  };
  const formatLabels = {
    'hands-on-lab': 'Hands-on lab',
    'conceptual-guide': 'Conceptual guide',
    'advanced-template': 'Advanced template',
    'reference': 'Reference'
  };
  const copyIcon = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"></path></svg>';
  const wrapIcon = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M3 12h15a3 3 0 1 1 0 6h-4"/><path d="m16 16-2 2 2 2"/><path d="M3 18h7"/></svg>';

  function detectOutputOrTemplate(pre, language, rawText) {
    if (!['text', 'csv', 'none'].includes(language)) return null;
    if (language === 'csv') return 'CSV';
    const prev = pre.previousElementSibling;
    const prevText = (prev?.textContent || '').trim().toLowerCase();
    if (/\b(observed output|expected output|sample output|terminal output|console output|output)\b/.test(prevText) || /^STATUS\b/m.test(rawText)) {
      return 'Output';
    }
    if (/\b(template|legend|placeholder|checklist|prompt)\b/.test(prevText) || /\[[^\]]{3,}\]/.test(rawText)) {
      return 'Template';
    }
    return null;
  }

  function enhanceCodeBlocks() {
    document.querySelectorAll('pre').forEach((pre, index) => {
      if (pre.closest('.tutorial-code-frame')) return;
      const code = pre.querySelector('code');
      const languageClass = Array.from(code?.classList || []).find(name => name.startsWith('language-'));
      const language = pre.dataset.codeLanguage || languageClass?.slice(9) || 'text';
      const rawText = code ? code.textContent : pre.textContent;
      const normalizedLines = rawText.replace(/\r?\n$/, '').split(/\r?\n/);
      const lineCount = normalizedLines.length;
      const maxLineLength = normalizedLines.reduce((max, line) => Math.max(max, line.length), 0);

      const isText = ['text', 'csv', 'none'].includes(language);
      const outputKind = detectOutputOrTemplate(pre, language, rawText);
      const languageName = pre.dataset.codeLabel || outputKind || languageNames[language] || language;
      const action = isText ? 'Copy text' : 'Copy code';
      const ariaLanguageName = pre.dataset.codeLabel || languageNames[language] || language;

      const frame = document.createElement('div');
      frame.className = 'tutorial-code-frame';
      frame.dataset.language = language;
      if (outputKind || isText) frame.classList.add('is-output-frame');

      const toolbar = document.createElement('div');
      toolbar.className = 'code-block-toolbar';

      const label = document.createElement('span');
      label.className = 'code-block-language';
      label.textContent = languageName;

      const actions = document.createElement('div');
      actions.className = 'code-toolbar-actions';

      const autoWrap = (isText || language === 'markdown') && maxLineLength > 95;
      const wrapButton = document.createElement('button');
      wrapButton.type = 'button';
      wrapButton.className = 'code-wrap-button';
      wrapButton.innerHTML = wrapIcon;
      const wrapText = document.createElement('span');
      wrapText.textContent = 'Wrap';
      wrapButton.append(wrapText);
      wrapButton.setAttribute('aria-pressed', String(autoWrap));
      wrapButton.setAttribute('aria-label', `Toggle line wrapping for ${ariaLanguageName} example ${index + 1}`);
      wrapButton.title = 'Toggle line wrapping';
      if (autoWrap) frame.classList.add('is-wrapped');

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'code-copy-button';
      button.innerHTML = copyIcon;
      const buttonText = document.createElement('span');
      buttonText.textContent = action;
      button.append(buttonText);
      button.setAttribute('aria-label', `${action}: ${ariaLanguageName} example ${index + 1}`);
      button.title = `${action} to clipboard`;

      const status = document.createElement('span');
      status.id = `code-copy-status-${index + 1}`;
      status.className = 'code-copy-status code-feedback-visually-hidden';
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'true');
      button.setAttribute('aria-describedby', status.id);

      const body = document.createElement('div');
      body.className = 'code-block-body';

      let gutter = null;
      if (!isText && language !== 'markdown' && lineCount >= 5) {
        gutter = document.createElement('div');
        gutter.className = 'code-line-gutter';
        gutter.setAttribute('aria-hidden', 'true');
        const nums = [];
        for (let n = 1; n <= lineCount; n += 1) nums.push(String(n));
        gutter.textContent = nums.join('\n');
      }

      pre.before(frame);
      actions.append(wrapButton, button);
      toolbar.append(label, actions);
      if (gutter) body.append(gutter, pre);
      else body.append(pre);
      frame.append(toolbar, body);

      let expandButton = null;
      if (lineCount >= 38) {
        frame.classList.add('is-collapsible', 'is-collapsed');
        expandButton = document.createElement('button');
        expandButton.type = 'button';
        expandButton.className = 'code-expand-button';
        expandButton.setAttribute('aria-expanded', 'false');
        expandButton.textContent = `Show all ${lineCount} lines`;
        expandButton.addEventListener('click', () => {
          const collapsed = frame.classList.toggle('is-collapsed');
          expandButton.setAttribute('aria-expanded', String(!collapsed));
          expandButton.textContent = collapsed ? `Show all ${lineCount} lines` : `Collapse script (${lineCount} lines)`;
          updateOverflow();
        });
        frame.append(expandButton);
      }
      frame.append(status);

      pre.tabIndex = 0;
      pre.setAttribute('role', 'region');
      pre.setAttribute('aria-label', `${ariaLanguageName} example ${index + 1}, horizontally scrollable`);

      function updateOverflow() {
        const wrapped = frame.classList.contains('is-wrapped');
        const hasRight = !wrapped && pre.clientWidth > 0 && (pre.scrollWidth - pre.clientWidth - pre.scrollLeft) > 4;
        body.classList.toggle('has-overflow-right', hasRight);
      }

      wrapButton.addEventListener('click', () => {
        const wrapped = frame.classList.toggle('is-wrapped');
        wrapButton.setAttribute('aria-pressed', String(wrapped));
        updateOverflow();
      });
      pre.addEventListener('scroll', updateOverflow, { passive: true });
      if (typeof ResizeObserver === 'function') {
        const ro = new ResizeObserver(updateOverflow);
        ro.observe(pre);
      }
      requestAnimationFrame(updateOverflow);

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
          status.textContent = `${ariaLanguageName} example copied to clipboard.`;
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
            selection.removeAllRanges();
            selection.addRange(range);
            status.textContent = 'Clipboard access failed. The example is selected; copy it manually.';
          } else {
            status.textContent = 'Clipboard access failed. Select the example and copy it manually.';
          }
          status.classList.remove('code-feedback-visually-hidden');
        } finally {
          button.disabled = false;
        }
      });
    });
  }

  function slugifyHeading(text, usedIds) {
    const base = (text || 'section')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'section';
    let candidate = base;
    let suffix = 2;
    while (usedIds.has(candidate)) {
      candidate = `${base}-${suffix}`;
      suffix += 1;
    }
    usedIds.add(candidate);
    return candidate;
  }

  function enhanceReaderUx() {
    if (document.documentElement.dataset.readerUxReady === 'true') return;
    const article = document.querySelector('#tutorial-content > article');
    if (!article) return;
    document.documentElement.dataset.readerUxReady = 'true';

    // 1. Sticky reading progress bar inside <main> (no position: fixed)
    const main = document.querySelector('main');
    if (main && !main.querySelector('.tutorial-reading-progress')) {
      const progress = document.createElement('div');
      progress.className = 'tutorial-reading-progress';
      progress.setAttribute('aria-hidden', 'true');
      const bar = document.createElement('div');
      bar.className = 'tutorial-reading-progress__bar';
      progress.append(bar);
      main.prepend(progress);

      let rafPending = false;
      const syncProgress = () => {
        rafPending = false;
        const rect = article.getBoundingClientRect();
        const articleTop = rect.top + window.scrollY - 96;
        const scrollable = Math.max(1, article.offsetHeight - window.innerHeight * 0.55);
        const ratio = Math.min(1, Math.max(0, (window.scrollY - articleTop) / scrollable));
        bar.style.transform = `scaleX(${ratio.toFixed(4)})`;
      };
      const onScroll = () => {
        if (!rafPending) {
          rafPending = true;
          requestAnimationFrame(syncProgress);
        }
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      window.addEventListener('resize', onScroll, { passive: true });
      syncProgress();
    }

    // 2. Reading-time and lesson-scope metadata strip under the author row
    const headerSection = document.querySelector('#tutorial-content > section');
    if (headerSection && !headerSection.querySelector('.tutorial-meta-strip')) {
      const words = (article.textContent || '').trim().split(/\s+/).filter(Boolean).length;
      const minutes = Math.max(3, Math.round(words / 220));
      const codeCount = article.querySelectorAll('pre').length;
      const figureCount = article.querySelectorAll('figure').length;
      const formatKey = article.querySelector('.tutorial-learning-contract[data-tutorial-format]')?.dataset.tutorialFormat || '';

      const strip = document.createElement('div');
      strip.className = 'tutorial-meta-strip';
      strip.setAttribute('aria-label', 'Lesson overview');

      if (formatLabels[formatKey]) {
        const formatPill = document.createElement('span');
        formatPill.className = 'tutorial-meta-pill tutorial-meta-pill--format';
        formatPill.dataset.format = formatKey;
        formatPill.textContent = formatLabels[formatKey];
        strip.append(formatPill);
      }

      const timePill = document.createElement('span');
      timePill.className = 'tutorial-meta-pill';
      timePill.textContent = `~${minutes} min read`;
      strip.append(timePill);

      if (codeCount > 0) {
        const codePill = document.createElement('span');
        codePill.className = 'tutorial-meta-pill';
        codePill.textContent = `${codeCount} ${codeCount === 1 ? 'code block' : 'code blocks'}`;
        strip.append(codePill);
      }
      if (figureCount > 0) {
        const figPill = document.createElement('span');
        figPill.className = 'tutorial-meta-pill';
        figPill.textContent = `${figureCount} ${figureCount === 1 ? 'figure' : 'figures'}`;
        strip.append(figPill);
      }
      headerSection.append(strip);
    }

    // 3. Auto "On this page" TOC before <article> (never alters <article> child indices)
    const headings = Array.from(article.querySelectorAll(':scope > h2'));
    const tutorialPage = document.getElementById('tutorial-page');
    if (headings.length >= 3 && !document.querySelector('.tutorial-toc')) {
      const usedIds = new Set(Array.from(document.querySelectorAll('[id]'), el => el.id));
      const desktopQuery = window.matchMedia('(min-width: 1280px)');
      const toc = document.createElement('details');
      toc.className = 'tutorial-toc';
      toc.setAttribute('aria-label', 'On this page');
      if (desktopQuery.matches) toc.open = true;

      const summary = document.createElement('summary');
      summary.className = 'tutorial-toc__summary';
      summary.textContent = `On this page (${headings.length} sections)`;

      const nav = document.createElement('nav');
      nav.className = 'tutorial-toc__nav';
      nav.setAttribute('aria-label', 'Table of contents');

      const list = document.createElement('ol');
      list.className = 'tutorial-toc__list';

      const linkMap = new Map();
      headings.forEach(heading => {
        if (!heading.id) {
          heading.id = slugifyHeading(heading.textContent.trim(), usedIds);
        }
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `#${heading.id}`;
        a.className = 'tutorial-toc__link';
        a.textContent = heading.textContent.trim();
        li.append(a);
        list.append(li);
        linkMap.set(heading.id, a);
      });

      nav.append(list);
      toc.append(summary, nav);
      article.before(toc);
      if (tutorialPage) tutorialPage.classList.add('has-desktop-toc');

      const syncOpenForViewport = event => {
        if (event.matches) toc.open = true;
      };
      if (typeof desktopQuery.addEventListener === 'function') {
        desktopQuery.addEventListener('change', syncOpenForViewport);
      }

      let activeId = headings[0].id;
      const setActive = id => {
        if (!id || !linkMap.has(id)) return;
        activeId = id;
        linkMap.forEach((link, key) => {
          const current = key === id;
          link.classList.toggle('is-active', current);
          if (current) link.setAttribute('aria-current', 'location');
          else link.removeAttribute('aria-current');
        });
      };
      const updateActiveHeading = () => {
        const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 24;
        let currentId = headings[0].id;
        if (atBottom) {
          currentId = headings[headings.length - 1].id;
        } else {
          headings.forEach(heading => {
            if (heading.getBoundingClientRect().top <= 125) currentId = heading.id;
          });
        }
        setActive(currentId);
      };
      let tocRaf = 0;
      const scheduleTocUpdate = () => {
        if (tocRaf) return;
        tocRaf = window.requestAnimationFrame(() => {
          tocRaf = 0;
          updateActiveHeading();
        });
      };
      updateActiveHeading();
      window.addEventListener('scroll', scheduleTocUpdate, { passive: true });
      window.addEventListener('resize', scheduleTocUpdate, { passive: true });
      window.addEventListener('hashchange', scheduleTocUpdate);
    }

    // 4. Native <dialog> click-to-zoom lightbox for all tutorial figures
    const figureImages = Array.from(article.querySelectorAll('figure img'));
    if (figureImages.length > 0 && typeof HTMLDialogElement === 'function') {
      let dialog = document.querySelector('dialog.tutorial-lightbox');
      if (!dialog) {
        dialog = document.createElement('dialog');
        dialog.className = 'tutorial-lightbox';
        dialog.setAttribute('aria-label', 'Enlarged figure preview');

        const header = document.createElement('div');
        header.className = 'tutorial-lightbox__header';
        const title = document.createElement('span');
        title.className = 'tutorial-lightbox__title';
        title.textContent = 'Figure preview';
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'tutorial-lightbox__close';
        closeBtn.setAttribute('aria-label', 'Close enlarged figure');
        closeBtn.textContent = 'Close';
        header.append(title, closeBtn);

        const body = document.createElement('div');
        body.className = 'tutorial-lightbox__body';
        const previewImg = document.createElement('img');
        previewImg.className = 'tutorial-lightbox__img';
        previewImg.alt = '';
        previewImg.hidden = true;
        const caption = document.createElement('p');
        caption.className = 'tutorial-lightbox__caption';
        body.append(previewImg, caption);
        dialog.append(header, body);
        document.body.append(dialog);

        let lastTrigger = null;
        const resetDialogMedia = () => {
          previewImg.removeAttribute('src');
          previewImg.alt = '';
          previewImg.hidden = true;
          caption.textContent = '';
          caption.hidden = true;
        };
        const closeDialog = () => {
          if (dialog.open) dialog.close();
          resetDialogMedia();
          if (lastTrigger && typeof lastTrigger.focus === 'function') {
            lastTrigger.focus({ preventScroll: true });
          }
          lastTrigger = null;
        };
        closeBtn.addEventListener('click', closeDialog);
        dialog.addEventListener('click', event => {
          if (event.target === dialog) closeDialog();
        });
        dialog.addEventListener('close', () => {
          resetDialogMedia();
          if (lastTrigger && typeof lastTrigger.focus === 'function') {
            lastTrigger.focus({ preventScroll: true });
          }
          lastTrigger = null;
        });

        figureImages.forEach(img => {
          const figure = img.closest('figure');
          if (!figure) return;
          figure.classList.add('has-figure-zoom');
          img.classList.add('tutorial-zoomable-img');
          img.tabIndex = 0;
          img.setAttribute('role', 'button');
          img.setAttribute('aria-label', `Enlarge figure: ${img.alt || 'tutorial diagram'}`);

          const hint = document.createElement('span');
          hint.className = 'figure-zoom-hint';
          hint.setAttribute('aria-hidden', 'true');
          hint.textContent = 'Click to enlarge';
          const figcaption = figure.querySelector('figcaption');
          if (figcaption) figcaption.before(hint);
          else figure.append(hint);

          const openDialog = event => {
            if (event) {
              event.preventDefault();
              event.stopPropagation();
            }
            lastTrigger = img;
            previewImg.hidden = false;
            previewImg.src = img.currentSrc || img.src;
            previewImg.alt = img.alt || '';
            caption.textContent = figcaption ? figcaption.textContent.trim() : (img.alt || '');
            caption.hidden = !caption.textContent;
            dialog.showModal();
            closeBtn.focus({ preventScroll: true });
          };
          const parentLink = img.closest('a');
          if (parentLink) {
            parentLink.addEventListener('click', event => event.preventDefault());
          }
          img.addEventListener('click', openDialog);
          img.addEventListener('keydown', event => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              openDialog(event);
            }
          });
        });
      }
    }
  }

  function initialise() {
    enhanceCodeBlocks();
    enhanceReaderUx();
  }

  document.addEventListener('tutorial-code-ready', initialise, { once: true });
  function onReady() {
    if (!document.querySelector('#tutorial-content > article') || document.documentElement.dataset.tutorialCodeReady === 'true') {
      initialise();
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', onReady, { once: true });
  else onReady();
})();
