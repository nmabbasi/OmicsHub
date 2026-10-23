'use strict';

// Run with: node --test tests/test_advertising_consent.js
// A deliberately small DOM fixture keeps these offline tests dependency-free.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');

const source = fs.readFileSync(path.join(__dirname, '..', 'cookie-consent.js'), 'utf8');

class Element {
  constructor(tagName, ownerDocument) {
    this.tagName = tagName.toUpperCase();
    this.ownerDocument = ownerDocument;
    this.attributes = Object.create(null);
    this.children = [];
    this.parentElement = null;
    this.dataset = Object.create(null);
    this.classList = { add() {} };
    this.listeners = Object.create(null);
    this.open = false;
    this._text = '';
    this._id = '';
  }

  set id(value) { this._id = value; this.setAttribute('id', value); }
  get id() { return this._id; }
  set type(value) { this.setAttribute('type', value); }
  set className(value) { this.setAttribute('class', value); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }

  set innerHTML(markup) {
    this.children = [];
    const idTags = /<([a-z][\w-]*)\b[^>]*\bid="([^"]+)"[^>]*>/gi;
    let match;
    while ((match = idTags.exec(markup))) this.appendChild(new Element(match[1], this.ownerDocument).withId(match[2]));
  }

  withId(value) { this.id = value; return this; }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === 'id') this._id = String(value);
  }
  getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null; }
  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
  showModal() { this.open = true; }
  close() { this.open = false; }
  focus() {}

  matches(selector) {
    if (selector === 'button[data-cookie-choice]') return this.tagName === 'BUTTON' && this.getAttribute('data-cookie-choice') !== null;
    const attr = selector.match(/^\[([^\]]+)\]$/);
    return Boolean(attr && this.getAttribute(attr[1]) !== null);
  }
  closest(selector) {
    for (let node = this; node; node = node.parentElement) if (node.matches(selector)) return node;
    return null;
  }
  querySelector(selector) {
    if (selector[0] === '#' && this.innerHTML && this.innerHTML.includes(`id="${selector.slice(1)}"`)) {
      const id = selector.slice(1);
      const existing = this.children.find(child => child.id === id);
      if (existing) return existing;
      const match = this.innerHTML.match(new RegExp(`<([a-z][\\w-]*)\\b[^>]*id="${id}"`, 'i'));
      if (match) return this.appendChild(new Element(match[1], this.ownerDocument).withId(id));
    }
    return this.ownerDocument.find(this, selector);
  }
  querySelectorAll(selector) {
    const result = [];
    const visit = node => node.children.forEach(child => {
      if (child.matches(selector)) result.push(child);
      visit(child);
    });
    visit(this);
    return result;
  }
}

class DocumentFixture {
  constructor() {
    this.listeners = Object.create(null);
    this.documentElement = new Element('html', this);
    this.documentElement.dataset = Object.create(null);
    this.body = new Element('body', this);
    this.footer = this.body.appendChild(new Element('footer', this));
    this.cookie = '';
    this.activeElement = this.body;
  }
  createElement(tagName) { return new Element(tagName, this); }
  createTextNode(text) { const node = new Element('#text', this); node.textContent = text; return node; }
  getElementById(id) {
    if (id === 'cookie-consent-banner') return null;
    return this.find(this.body, `#${id}`);
  }
  find(root, selector) {
    const visit = node => {
      for (const child of node.children) {
        if (selector === 'footer' && child.tagName === 'FOOTER') return child;
        if (selector === 'a[href*="cookie.html"]' && child.tagName === 'A' && (child.getAttribute('href') || '').includes('cookie.html')) return child;
        if (selector[0] === '#' && child.id === selector.slice(1)) return child;
        if (child.matches(selector)) return child;
        const found = visit(child);
        if (found) return found;
      }
      return null;
    };
    return visit(root);
  }
  querySelector(selector) { return this.find(this.body, selector); }
  querySelectorAll(selector) {
    const result = [];
    const visit = node => node.children.forEach(child => {
      if (child.matches(selector)) result.push(child);
      visit(child);
    });
    visit(this.body);
    return result;
  }
  addEventListener(type, handler) { (this.listeners[type] ||= []).push(handler); }
  click(target) { for (const handler of this.listeners.click || []) handler({ target }); }
}

function setup(options = {}) {
  const document = new DocumentFixture();
  const storage = new Map();
  const analyticsCalls = [];
  const window = {
    document,
    location: { hostname: 'example.test', reload() {} },
    localStorage: {
      getItem: key => storage.has(key) ? storage.get(key) : null,
      setItem: (key, value) => storage.set(key, value)
    },
    gtag: (...args) => analyticsCalls.push(args),
    omicsHubLoadAnalytics: () => analyticsCalls.push(['load-analytics'])
  };
  if (Object.prototype.hasOwnProperty.call(options, 'googlefc')) window.googlefc = options.googlefc;
  const context = vm.createContext({ window, document, console });
  const run = () => vm.runInContext(source, context, { filename: 'cookie-consent.js' });
  const control = () => document.querySelector('[data-advertising-preferences]');
  const status = () => document.querySelector('[data-advertising-consent-status]');
  run();
  return { window, document, storage, analyticsCalls, run, control, status };
}

function signalReady(queue) {
  const callback = queue.find(item => item && typeof item === 'object' && typeof item.CONSENT_API_READY === 'function');
  assert.ok(callback, 'a CONSENT_API_READY callback should be queued');
  callback.CONSENT_API_READY();
}

test('missing or not-yet-ready CMP gives an accessible truthful fallback and never queues a later revocation', () => {
  const app = setup();
  const queue = app.window.googlefc.callbackQueue;
  assert.equal(queue.length, 1);
  assert.equal(Object.keys(queue[0])[0], 'CONSENT_API_READY');
  assert.match(app.control().textContent, /Privacy and cookie settings \(advertising\)/);
  assert.equal(app.status().getAttribute('role'), 'status');
  assert.equal(app.status().getAttribute('aria-live'), 'polite');
  assert.match(app.status().getAttribute('style'), /display:\s*block/);

  const nested = app.document.createElement('span');
  app.control().appendChild(nested);
  app.document.click(nested);
  assert.match(app.status().textContent, /could not be opened/);
  assert.match(app.status().textContent, /No change to your advertising choice is confirmed/);
  assert.equal(queue.length, 1, 'click before ready must not enqueue a revocation action');

  app.window.googlefc.showRevocationMessage = () => assert.fail('readiness must not open the CMP');
  signalReady(queue);
  assert.match(app.status().textContent, /settings are available/);
  assert.equal(queue.length, 1, 'a delayed ready callback must only update status');
});

test('ready revocation uses callbackQueue, delegates nested clicks, and does not touch analytics or grant ads', () => {
  const app = setup();
  const queue = app.window.googlefc.callbackQueue;
  let directCalls = 0;
  app.window.googlefc.showRevocationMessage = () => { directCalls += 1; };
  signalReady(queue);
  const beforeAnalytics = JSON.stringify(app.analyticsCalls);
  const beforeChoice = app.storage.get('omicsHubCookieChoice');

  const nested = app.document.createElement('strong');
  app.control().appendChild(nested);
  app.document.click(nested);
  assert.equal(queue.length, 2);
  assert.equal(queue[1], app.window.googlefc.showRevocationMessage);
  assert.equal(directCalls, 0, 'API must be invoked through callbackQueue rather than directly');
  assert.equal(JSON.stringify(app.analyticsCalls), beforeAnalytics);
  assert.equal(app.storage.get('omicsHubCookieChoice'), beforeChoice);
  assert.equal(app.document.documentElement.dataset.cookieChoice, undefined);
  assert.equal(Object.keys(app.window.googlefc).some(key => /ad_storage|ad_user_data|ad_personalization/.test(key)), false);
});

test('existing Google namespace and non-array callback queue are preserved', () => {
  const existingNamespace = { retained: true };
  const entries = [];
  const existingQueue = { push(value) { entries.push(value); } };
  existingNamespace.callbackQueue = existingQueue;
  const app = setup({ googlefc: existingNamespace });
  assert.equal(app.window.googlefc, existingNamespace);
  assert.equal(app.window.googlefc.callbackQueue, existingQueue);
  assert.equal(existingNamespace.retained, true);
  assert.equal(entries.length, 1);
  existingNamespace.showRevocationMessage = () => {};
  entries[0].CONSENT_API_READY();
  app.document.click(app.control());
  assert.equal(entries.length, 2);
  assert.equal(entries[1], existingNamespace.showRevocationMessage);
});

test('blocked queue reports failure without claiming a change or granting consent', () => {
  const calls = [];
  const googlefc = { callbackQueue: { push(value) { calls.push(value); throw new Error('blocked'); } } };
  const app = setup({ googlefc });
  assert.equal(calls.length, 1, 'only readiness registration was attempted');
  googlefc.showRevocationMessage = () => assert.fail('blocked queue must not call CMP directly');
  app.document.click(app.control());
  assert.match(app.status().textContent, /could not be opened/);
  assert.match(app.status().textContent, /No change to your advertising choice is confirmed/);
  assert.equal(calls.length, 1);
});

test('script re-execution keeps one advertising control, one readiness callback and one revocation dispatch', () => {
  const app = setup();
  const queue = app.window.googlefc.callbackQueue;
  app.window.googlefc.showRevocationMessage = () => {};
  signalReady(queue);
  app.run();
  assert.equal(app.document.querySelectorAll('[data-advertising-preferences]').length, 1);
  assert.equal(queue.filter(item => item && item.CONSENT_API_READY).length, 1);
  app.document.click(app.control());
  assert.equal(queue.length, 2, 'one explicit click should dispatch one revocation function');
});
