'use strict';

// Run with: node --test tests/test_analytics_load_order.js
// A bounded DOM fixture exercises the loader without network access or a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync(path.join(__dirname, '..', 'analytics.js'), 'utf8');

function setup({ choice = null, readyState = 'loading', withQueue = true } = {}) {
  const storage = new Map();
  if (choice !== null) storage.set('omicsHubCookieChoice', choice);
  const listeners = Object.create(null);
  const appended = [];
  const document = {
    readyState,
    head: { appendChild(tag) { appended.push(tag); return tag; } },
    createElement(tagName) { return { tagName, async: false, src: '', onload: null, onerror: null }; },
    addEventListener(type, callback) { (listeners[type] ||= []).push(callback); }
  };
  const calls = [];
  const window = {
    localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { storage.set(key, value); }
    },
    dataLayer: [],
    document,
    location: { reload() {} }
  };
  if (withQueue) window.gtag = (...args) => { calls.push(args); window.dataLayer.push(args); };
  const context = vm.createContext({ window, document, Date, encodeURIComponent });
  vm.runInContext(source, context, { filename: 'analytics.js' });
  return {
    window, document, storage, appended, calls,
    signalReady() {
      document.readyState = 'interactive';
      const callbacks = listeners.DOMContentLoaded || [];
      listeners.DOMContentLoaded = [];
      callbacks.forEach(callback => callback());
    },
    addDeniedDefaults() {
      window.dataLayer = window.dataLayer || [];
      if (typeof window.gtag !== 'function') {
        window.gtag = (...args) => { calls.push(args); window.dataLayer.push(args); };
      }
      window.gtag('consent', 'default', {
        analytics_storage: 'denied',
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied'
      });
    }
  };
}

test('saved acceptance in the early head waits for inline defaults and a usable queue', () => {
  const app = setup({ choice: 'accepted' });
  assert.equal(app.appended.length, 0, 'must not append gtag during parsing');
  assert.equal(app.calls.length, 0, 'must not issue an update before the default command');

  app.addDeniedDefaults();
  app.signalReady();
  assert.equal(app.appended.length, 1);
  assert.equal(app.appended[0].src, 'https://www.googletagmanager.com/gtag/js?id=G-MTD30PYWWH');
  assert.deepEqual(app.calls.map(call => call.slice(0, 2)), [['consent', 'default'], ['consent', 'update']]);
  assert.deepEqual({ ...app.calls[1][2] }, { analytics_storage: 'granted' });
});

test('absent and declined preferences never load analytics', () => {
  for (const choice of [null, 'declined']) {
    const app = setup({ choice });
    app.addDeniedDefaults();
    app.signalReady();
    assert.equal(app.appended.length, 0, `choice ${choice} must not load analytics`);
  }
});

test('missing, malformed, or unusable defaults fail closed and can be retried after setup', () => {
  const app = setup({ choice: 'accepted' });
  app.signalReady();
  assert.equal(app.appended.length, 0, 'missing defaults must fail closed');

  app.window.dataLayer.push(['consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied' }]);
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 0, 'partial defaults must fail closed');

  const unusable = setup({ choice: 'accepted', readyState: 'interactive', withQueue: false });
  unusable.window.dataLayer.push(['consent', 'default', {
    analytics_storage: 'denied', ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied'
  }]);
  unusable.window.omicsHubLoadAnalytics();
  assert.equal(unusable.appended.length, 0, 'defaults without a gtag queue must fail closed');

  app.addDeniedDefaults();
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1, 'a later valid queue/default setup may be retried');
});

test('acceptance after document readiness starts loading only after defaults are queued', () => {
  const app = setup({ readyState: 'interactive' });
  app.addDeniedDefaults();
  assert.equal(app.appended.length, 0);
  app.storage.set('omicsHubCookieChoice', 'accepted');
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1);
});

test('repeated readiness callbacks and loader calls append only one script', () => {
  const app = setup({ choice: 'accepted' });
  app.addDeniedDefaults();
  app.signalReady();
  app.signalReady();
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1);

  app.appended[0].onload();
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1, 'successful load must remain deduplicated');
});

test('current permission is rechecked when readiness arrives and can be opted into later', () => {
  const app = setup({ choice: 'accepted' });
  app.addDeniedDefaults();
  app.storage.set('omicsHubCookieChoice', 'declined');
  app.signalReady();
  assert.equal(app.appended.length, 0, 'withdrawal while waiting must cancel the pending load');

  app.storage.set('omicsHubCookieChoice', 'accepted');
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1, 'a later explicit acceptance may start loading');
});

test('withdrawal during download blocks configuration and later opt-in reuses the loaded script', () => {
  const app = setup({ choice: 'accepted', readyState: 'interactive' });
  app.addDeniedDefaults();
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1);
  app.storage.set('omicsHubCookieChoice', 'declined');
  app.appended[0].onload();
  assert.equal(app.window.__omicsHubAnalyticsLoaded, undefined);
  assert.equal(app.calls.some(call => call[0] === 'config'), false);

  app.storage.set('omicsHubCookieChoice', 'accepted');
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 1, 'a downloaded script must not be appended a second time');
  assert.equal(app.calls.some(call => call[0] === 'config'), true);
  assert.equal(app.window.__omicsHubAnalyticsLoaded, true);
});

test('a network error releases the guard so a later explicit retry can append once', () => {
  const app = setup({ choice: 'accepted', readyState: 'interactive' });
  app.addDeniedDefaults();
  app.window.omicsHubLoadAnalytics();
  app.appended[0].onerror();
  app.window.omicsHubLoadAnalytics();
  assert.equal(app.appended.length, 2, 'one new retry follows the failed request');
  assert.equal(app.appended[1].src, app.appended[0].src);
});
