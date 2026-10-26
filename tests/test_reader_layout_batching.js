'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'subscribe-fab.js'), 'utf8');
const start = source.indexOf('  function initLayoutMetrics() {');
const end = source.indexOf('  function initIntentPrefetch() {', start);
assert.notEqual(start, -1, 'initLayoutMetrics() exists');
assert.notEqual(end, -1, 'initLayoutMetrics() has a following function boundary');
const initializer = source.slice(start, end).trim();

const log = [];
const listeners = new Map();
const resizeObservers = [];
const mutationObservers = [];
const values = new Map([
  ['--reader-banner-space', ''],
  ['--reader-header-height', ''],
]);
const banner = {
  height: 20.2,
  display: 'block',
  getBoundingClientRect() {
    log.push('read:banner-geometry');
    return { height: this.height };
  },
};
const nav = { paddingBottom: '8.2px' };
const header = {
  top: 10,
  querySelector(selector) {
    if (selector === 'nav > div:first-child') return row;
    assert.equal(selector, 'nav');
    return nav;
  },
  getBoundingClientRect() {
    log.push('read:header-geometry');
    return { top: this.top };
  },
};
const row = {
  bottom: 50,
  getBoundingClientRect() {
    log.push('read:row-geometry');
    return { bottom: this.bottom };
  },
};
const rootStyle = {
  getPropertyValue(name) {
    log.push(`read:style:${name}`);
    return values.get(name) || '';
  },
  setProperty(name, value) {
    log.push(`write:${name}:${value}`);
    values.set(name, value);
  },
};
const document = {
  documentElement: { style: rootStyle },
  getElementById(id) {
    assert.equal(id, 'cookie-consent-banner');
    return banner;
  },
  querySelector(selector) {
    assert.equal(selector, 'header');
    return header;
  },
};
const window = {
  ResizeObserver: function ResizeObserver(callback) {
    this.callback = callback;
    this.observe = target => { this.target = target; };
    resizeObservers.push(this);
  },
  addEventListener(name, callback, options) {
    listeners.set(name, { callback, options });
  },
  dispatchEvent(event) {
    log.push(`dispatch:${event.type}`);
    return true;
  },
};
class MutationObserverDouble {
  constructor(callback) { this.callback = callback; mutationObservers.push(this); }
  observe(target, options) { this.target = target; this.options = options; }
}
const context = {
  document,
  window,
  ResizeObserver: window.ResizeObserver,
  MutationObserver: MutationObserverDouble,
  Event: class Event { constructor(type) { this.type = type; } },
  getComputedStyle(element) {
    log.push(`read:computed-style:${element === banner ? 'banner' : 'header-nav'}`);
    return element === banner ? { display: banner.display } : { paddingBottom: nav.paddingBottom };
  },
};
vm.runInNewContext(`(${initializer})()`, context, { filename: 'subscribe-fab.js:initLayoutMetrics' });

function updateLog() {
  const entries = log.splice(0);
  const firstWrite = entries.findIndex(entry => entry.startsWith('write:'));
  const readsAfterWrite = firstWrite < 0 ? [] : entries.slice(firstWrite + 1).filter(entry => entry.startsWith('read:'));
  assert.deepEqual(readsAfterWrite, [], 'all geometry, computed-style, and existing-value reads precede writes');
  assert.equal(entries.filter(entry => entry === 'dispatch:readerlayoutchange').length, 1,
    'each update dispatches readerlayoutchange once');
  return entries;
}

// The initial call remains synchronous and preserves the original calculations.
assert.equal(values.get('--reader-banner-space'), '21px');
assert.equal(values.get('--reader-header-height'), '50px');
const initial = updateLog();
assert.deepEqual(initial.filter(entry => entry.startsWith('write:')),
  ['write:--reader-banner-space:21px', 'write:--reader-header-height:50px']);
assert.equal(resizeObservers.length, 1);
assert.equal(resizeObservers[0].target, row, 'ResizeObserver still observes the layout row');
assert.equal(mutationObservers.length, 1);
assert.equal(mutationObservers[0].target, banner, 'MutationObserver still observes the banner');
assert.equal(JSON.stringify(mutationObservers[0].options),
  JSON.stringify({ attributes: true, attributeFilter: ['class', 'style'] }));

// A no-change rerun still dispatches but does not write either custom property.
resizeObservers[0].callback();
const unchanged = updateLog();
assert.deepEqual(unchanged.filter(entry => entry.startsWith('write:')), []);

// Mutation and resize callbacks both rerun the measurement and update changed values.
banner.height = 31.1;
row.bottom = 62;
header.top = 12;
nav.paddingBottom = '5px';
mutationObservers[0].callback();
assert.equal(values.get('--reader-banner-space'), '32px');
assert.equal(values.get('--reader-header-height'), '56px');
const mutationUpdate = updateLog();
assert.deepEqual(mutationUpdate.filter(entry => entry.startsWith('write:')),
  ['write:--reader-banner-space:32px', 'write:--reader-header-height:56px']);

banner.display = 'none';
listeners.get('resize').callback();
assert.equal(values.get('--reader-banner-space'), '0px');
assert.equal(values.get('--reader-header-height'), '56px');
const resizeUpdate = updateLog();
assert.deepEqual(resizeUpdate.filter(entry => entry.startsWith('write:')),
  ['write:--reader-banner-space:0px']);

console.log('reader layout batching regression tests passed');
