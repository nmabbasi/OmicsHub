/* Review-only catalogue controls. Shared homepage search helpers remain the source of query normalization and aliases. */
(() => {
  'use strict';

  const VALID_LEVELS = new Set(['all', 'beginner', 'intermediate', 'advanced']);
  const VALID_FORMATS = new Set(['all', 'hands-on-lab', 'conceptual-guide', 'advanced-template', 'reference']);
  const FILTER_KEYS = ['category', 'q', 'level', 'format'];

  function getControls() {
    return {
      category: document.getElementById('catalogue-category'),
      level: document.getElementById('catalogue-level'),
      format: document.getElementById('catalogue-format'),
      query: document.getElementById('search-input')
    };
  }

  function validCategory(value) {
    const values = [...document.querySelectorAll('#category-filter .category-btn')].map(button => button.dataset.category);
    return values.includes(value) ? value : 'all';
  }

  function readStateFromControls() {
    const controls = getControls();
    return {
      category: validCategory(controls.category?.value || 'all'),
      q: (controls.query?.value || '').trim(),
      level: VALID_LEVELS.has(controls.level?.value) ? controls.level.value : 'all',
      format: VALID_FORMATS.has(controls.format?.value) ? controls.format.value : 'all'
    };
  }

  function urlForState(state) {
    const params = new URLSearchParams(window.location.search);
    FILTER_KEYS.forEach(key => params.delete(key));
    if (state.category !== 'all') params.set('category', state.category);
    if (state.q) params.set('q', state.q);
    if (state.level !== 'all') params.set('level', state.level);
    if (state.format !== 'all') params.set('format', state.format);
    return `${window.location.pathname}${params.size ? `?${params.toString()}` : ''}${window.location.hash}`;
  }

  function writeURL(mode) {
    const url = urlForState(readStateFromControls());
    const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    if (url === current) return;
    if (mode === 'push') window.history.pushState({}, '', url);
    else window.history.replaceState({}, '', url);
  }

  function updateCategoryButtons(category) {
    document.querySelectorAll('#category-filter .category-btn').forEach(button => {
      const selected = button.dataset.category === category;
      button.setAttribute('aria-pressed', selected ? 'true' : 'false');
      button.classList.toggle('is-selected', selected);
      button.classList.toggle('bg-blue-600', selected && category === 'all');
      button.classList.toggle('text-white', selected);
      button.classList.toggle('bg-gray-200', !selected);
      button.classList.toggle('text-gray-700', !selected);
    });
  }

  function applyCatalogueFilters(category, query) {
    const list = document.getElementById('all-tutorials-list');
    if (!list) return;
    const controls = getControls();
    const chosenCategory = validCategory(category ?? controls.category?.value ?? 'all');
    const chosenLevel = VALID_LEVELS.has(controls.level?.value) ? controls.level.value : 'all';
    const chosenFormat = VALID_FORMATS.has(controls.format?.value) ? controls.format.value : 'all';
    const rawQuery = String(query ?? controls.query?.value ?? '').trim();
    const terms = window.normalizeSearchText(rawQuery).split(' ').filter(Boolean);
    const cards = [...list.querySelectorAll('.tutorial-grid-card')];
    let count = 0;

    cards.forEach(card => {
      const categoryMatch = chosenCategory === 'all' || card.dataset.category === chosenCategory;
      const levelMatch = chosenLevel === 'all' || card.dataset.level === chosenLevel;
      const formatMatch = chosenFormat === 'all' || card.dataset.format === chosenFormat;
      const queryMatch = window.searchTextMatches(
        window.normalizeSearchText(card.dataset.search || card.textContent), terms
      );
      const matches = categoryMatch && levelMatch && formatMatch && queryMatch;
      card.classList.toggle('hidden', !matches);
      card.style.display = matches ? 'flex' : 'none';
      if (matches) count += 1;
    });

    const status = document.getElementById('search-results-status');
    if (status) {
      status.textContent = `${count} ${rawQuery || chosenCategory !== 'all' || chosenLevel !== 'all' || chosenFormat !== 'all' ? 'matching ' : ''}${count === 1 ? 'tutorial' : 'tutorials'}.`;
      status.classList.remove('hidden');
    }
    const countLabel = document.getElementById('catalogue-results-count');
    if (countLabel) countLabel.textContent = `${count} ${count === 1 ? 'lesson' : 'lessons'}`;
    const empty = document.getElementById('catalogue-empty-state');
    if (empty) empty.hidden = count !== 0;
    updateCategoryButtons(chosenCategory);
  }

  function filterTutorialsOnly(category) {
    const controls = getControls();
    const chosen = validCategory(category);
    if (controls.category) controls.category.value = chosen;
    applyCatalogueFilters(chosen, controls.query?.value || '');
    writeURL('push');
  }

  function restoreCatalogueState() {
    if (!document.getElementById('all-tutorials-list')) return;
    const params = new URLSearchParams(window.location.search);
    const controls = getControls();
    const category = validCategory(params.get('category') || 'all');
    const level = VALID_LEVELS.has(params.get('level')) ? params.get('level') : 'all';
    const format = VALID_FORMATS.has(params.get('format')) ? params.get('format') : 'all';
    const query = params.get('q') || '';
    if (controls.category) controls.category.value = category;
    if (controls.level) controls.level.value = level;
    if (controls.format) controls.format.value = format;
    if (controls.query) controls.query.value = query;
    applyCatalogueFilters(category, query);
    // Invalid filter values are safely normalized in the visible controls and URL.
    writeURL('replace');
  }

  function resetFilters() {
    const controls = getControls();
    if (controls.category) controls.category.value = 'all';
    if (controls.level) controls.level.value = 'all';
    if (controls.format) controls.format.value = 'all';
    if (controls.query) controls.query.value = '';
    applyCatalogueFilters('all', '');
    writeURL('push');
  }

  function initCatalogueSearchState() {
    const list = document.getElementById('all-tutorials-list');
    if (!list) return;
    restoreCatalogueState();

    const controls = getControls();
    if (controls.query) {
      controls.query.addEventListener('input', () => {
        applyCatalogueFilters(controls.category?.value || 'all', controls.query.value);
        writeURL('replace');
      });
    }
    [controls.category, controls.level, controls.format].forEach(select => {
      if (!select) return;
      select.addEventListener('change', () => {
        if (select === controls.category) select.value = validCategory(select.value);
        if (select === controls.level && !VALID_LEVELS.has(select.value)) select.value = 'all';
        if (select === controls.format && !VALID_FORMATS.has(select.value)) select.value = 'all';
        applyCatalogueFilters(controls.category?.value || 'all', controls.query?.value || '');
        writeURL('push');
      });
    });
    document.getElementById('catalogue-reset')?.addEventListener('click', resetFilters);
    document.getElementById('catalogue-clear-empty')?.addEventListener('click', resetFilters);
    window.addEventListener('popstate', restoreCatalogueState);
    window.addEventListener('pageshow', restoreCatalogueState);
  }

  window.applyCatalogueFilters = applyCatalogueFilters;
  window.filterTutorialsOnly = filterTutorialsOnly;
  window.restoreCatalogueState = restoreCatalogueState;
  window.initCatalogueSearchState = initCatalogueSearchState;
})();
