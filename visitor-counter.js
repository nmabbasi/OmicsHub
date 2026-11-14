(() => {
  const counter = document.querySelector('[data-visitor-counter]');
  if (!counter) return;

  const showUnavailable = () => {
    counter.textContent = 'Visitor count temporarily unavailable · View counter service';
    counter.dataset.counterState = 'unavailable';
  };

  try {
    const endpoint = new URL(counter.dataset.counterBase);
    endpoint.searchParams.set('output', 'json');
    endpoint.searchParams.set('cb', Date.now().toString());

    fetch(endpoint.toString(), {
      cache: 'no-store',
      credentials: 'omit',
      referrerPolicy: 'no-referrer'
    })
      .then((response) => {
        if (!response.ok) throw new Error('Counter request failed');
        return response.json();
      })
      .then((counts) => {
        if (!Number.isSafeInteger(counts.today_hits) || counts.today_hits < 0 ||
            !Number.isSafeInteger(counts.total_hits) || counts.total_hits < 0) {
          throw new Error('Counter response was invalid');
        }

        const format = new Intl.NumberFormat('en');
        counter.textContent = `Visits: ${format.format(counts.today_hits)} today · ${format.format(counts.total_hits)} total`;
        counter.dataset.counterState = 'loaded';
      })
      .catch(showUnavailable);
  } catch (error) {
    showUnavailable();
  }
})();
