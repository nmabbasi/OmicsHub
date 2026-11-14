'use strict';

// Run with: node --test tests/test_visitor_counter.js
// The provider request is mocked so tests never alter production visitor data.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync(path.join(__dirname, '..', 'visitor-counter.js'), 'utf8');
const base = 'https://hitscounter.dev/api/hit?url=https%3A%2F%2Ftheomicshub.com%2F&label=Visits&color=%23374151&message=&style=flat-square&tz=Europe%2FParis';

function runCounter({ counter = { dataset: { counterBase: base }, textContent: 'Loading visitor count…' }, fetchImpl } = {}) {
  const requests = [];
  const fetch = fetchImpl || ((url, options) => {
    requests.push({ url, options });
    return Promise.resolve({ ok: true, json: () => Promise.resolve({ today_hits: 49, total_hits: 7868 }) });
  });
  const context = vm.createContext({
    Date,
    Intl,
    Number,
    URL,
    document: { querySelector: (selector) => selector === '[data-visitor-counter]' ? counter : null },
    fetch
  });
  vm.runInContext(source, context, { filename: 'visitor-counter.js' });
  return { counter, requests };
}

async function flushPromises() {
  await new Promise((resolve) => setImmediate(resolve));
}

test('renders real provider JSON as readable text with one private, uncached request', async () => {
  const app = runCounter();
  await flushPromises();

  assert.equal(app.requests.length, 1, 'one page view must make exactly one hit request');
  const endpoint = new URL(app.requests[0].url);
  assert.equal(endpoint.origin, 'https://hitscounter.dev');
  assert.equal(endpoint.pathname, '/api/hit');
  assert.equal(endpoint.searchParams.get('url'), 'https://theomicshub.com/');
  assert.equal(endpoint.searchParams.get('tz'), 'Europe/Paris');
  assert.equal(endpoint.searchParams.get('output'), 'json');
  assert.ok(endpoint.searchParams.get('cb'));
  assert.equal(app.requests[0].options.cache, 'no-store');
  assert.equal(app.requests[0].options.credentials, 'omit');
  assert.equal(app.requests[0].options.referrerPolicy, 'no-referrer');
  assert.equal(app.counter.textContent, 'Visits: 49 today · 7,868 total');
  assert.equal(app.counter.dataset.counterState, 'loaded');
});

test('shows an explicit unavailable message when the counter request fails', async () => {
  const app = runCounter({ fetchImpl: () => Promise.reject(new Error('network unavailable')) });
  await flushPromises();
  assert.equal(app.counter.textContent, 'Visitor count temporarily unavailable · View counter service');
  assert.equal(app.counter.dataset.counterState, 'unavailable');
});

test('rejects unsuccessful HTTP responses and malformed counts instead of showing false values', async () => {
  const failedHttp = runCounter({ fetchImpl: () => Promise.resolve({ ok: false }) });
  await flushPromises();
  assert.equal(failedHttp.counter.dataset.counterState, 'unavailable');

  const invalidCounts = runCounter({ fetchImpl: () => Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ today_hits: -1, total_hits: 0 })
  }) });
  await flushPromises();
  assert.equal(invalidCounts.counter.dataset.counterState, 'unavailable');
  assert.match(invalidCounts.counter.textContent, /temporarily unavailable/);
});

test('does nothing when the footer has no visitor-counter element', () => {
  let requested = false;
  const app = runCounter({ counter: null, fetchImpl: () => { requested = true; } });
  assert.equal(app.requests.length, 0);
  assert.equal(requested, false);
});
