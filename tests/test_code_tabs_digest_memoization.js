'use strict';

const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'code-tabs.js'), 'utf8');
const sha256 = text => createHash('sha256').update(text).digest('hex');

function makeArticle(texts) {
  const blocks = texts.map(text => {
    const classNames = new Set(['language-original']);
    const code = {
      textContent: text,
      classList: {
        [Symbol.iterator]: () => classNames[Symbol.iterator](),
        remove: name => classNames.delete(name),
        add: name => classNames.add(name)
      }
    };
    return {
      tagName: 'PRE',
      textContent: text,
      dataset: {},
      querySelector: selector => selector === 'code' ? code : null
    };
  });
  return {
    blocks,
    article: {
      children: blocks,
      querySelectorAll: selector => selector === 'pre' ? blocks : [],
      insertBefore() { throw new Error('Invalid group unexpectedly mutated source nodes'); }
    }
  };
}

function makeSpec(texts) {
  return {
    blocks: texts.map(text => ({ sha256: sha256(text), language: 'r' })),
    groups: [{
      title: 'Regression group',
      tabOrder: ['r', 'python'],
      panels: [
        { language: 'r', label: 'R', start: 0, end: texts.length - 2 },
        { language: 'python', label: 'Python', start: texts.length - 1, end: texts.length - 1 }
      ],
      // Deliberately wrong fingerprints: exercise every group digest comparison
      // without allowing the test DOM to move or wrap any source nodes.
      members: texts.map((_, index) => ({ index, tag: 'pre', sha256: 'not-the-reviewed-hash' }))
    }]
  };
}

function createHarness({ texts, cryptoMode = 'resolve', missingTextEncoder = false }) {
  const { article, blocks } = makeArticle(texts);
  const calls = [];
  const warnings = [];
  const events = [];
  const cacheReads = [];
  let readyListener;
  class TrackingMap extends Map {
    get(key) {
      const value = super.get(key);
      cacheReads.push({ key, value });
      return value;
    }
  }
  const deferredFor = text => {
    if (cryptoMode === 'reject') return Promise.reject(new Error('digest unavailable'));
    if (cryptoMode === 'resolve') {
      const bytes = Uint8Array.from(Buffer.from(sha256(text), 'hex'));
      return Promise.resolve(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
    }
    return Promise.resolve(new ArrayBuffer(0));
  };
  const subtle = {
    digest(algorithm, input) {
      const text = Buffer.from(input).toString('utf8');
      const promise = deferredFor(text);
      calls.push({ algorithm, text, promise });
      return promise;
    }
  };
  const window = {
    OMICS_TUTORIAL_CODE: { tutorials: { regression: makeSpec(texts) } },
    TextEncoder: missingTextEncoder ? undefined : TextEncoder,
    crypto: cryptoMode === 'missing' ? undefined : { subtle },
    addEventListener() {}
  };
  const document = {
    readyState: 'loading',
    documentElement: { dataset: {} },
    querySelector: selector => selector === '#tutorial-content > article' ? article : null,
    querySelectorAll: () => [],
    addEventListener(type, callback) { if (type === 'DOMContentLoaded') readyListener = callback; },
    dispatchEvent(event) { events.push(event); },
    getElementById() { return null; }
  };
  class CustomEvent {
    constructor(type, options) { this.type = type; this.detail = options?.detail; }
  }
  const context = {
    window,
    document,
    location: { pathname: '/tutorials/regression.html', hash: '' },
    sessionStorage: { getItem() { return null; }, setItem() {} },
    TextEncoder: missingTextEncoder ? undefined : TextEncoder,
    crypto: window.crypto,
    Map: TrackingMap,
    CustomEvent,
    console: { warn: (...args) => warnings.push(args) },
    requestAnimationFrame() {},
    innerHeight: 1000
  };
  vm.runInNewContext(source, context, { filename: 'code-tabs.js' });
  assert.equal(typeof readyListener, 'function', 'script should wait for DOMContentLoaded');
  return {
    blocks,
    calls,
    cacheReads,
    events,
    warnings,
    ready: () => readyListener()
  };
}

test('one invocation shares pending digest promises by exact text across block and group checks', async () => {
  const texts = ['same source', 'same source ', 'same source'];
  const harness = createHarness({ texts });

  await harness.ready();

  assert.deepEqual(harness.calls.map(call => call.algorithm), ['SHA-256', 'SHA-256']);
  assert.deepEqual(harness.calls.map(call => call.text), ['same source', 'same source ']);
  assert.equal(harness.calls.filter(call => call.text === 'same source').length, 1);
  assert.equal(harness.calls.filter(call => call.text === 'same source ').length, 1);
  assert.ok(harness.calls.every(call => call.promise instanceof Promise));
  const repeatedTextReads = harness.cacheReads.filter(read => read.key === 'same source');
  assert.equal(repeatedTextReads.length, 4, 'the exact input should be looked up for both block and group comparisons');
  assert.ok(repeatedTextReads.every(read => read.value === repeatedTextReads[0].value), 'all matching lookups should return the identical cached promise');
  const whitespaceReads = harness.cacheReads.filter(read => read.key === 'same source ');
  assert.equal(whitespaceReads.length, 2);
  assert.notStrictEqual(repeatedTextReads[0].value, whitespaceReads[0].value, 'whitespace-distinct inputs must have distinct promises');
  assert.ok(harness.blocks.every((block, index) => block.dataset.codeSourceIndex === String(index)));
  assert.ok(harness.warnings.some(([message]) => String(message).includes('group left visible')));
  assert.equal(harness.events[0]?.detail?.groups, 0);
});

test('unavailable crypto preserves the unchanged-code fallback without digest calls', async () => {
  const harness = createHarness({ texts: ['same source', 'same source'], cryptoMode: 'missing' });

  await harness.ready();

  assert.equal(harness.calls.length, 0);
  assert.ok(harness.blocks.every(block => Object.keys(block.dataset).length === 0));
  assert.ok(harness.warnings.some(([message]) => String(message).includes('fingerprints have changed or are unavailable')));
  assert.equal(harness.events[0]?.detail?.groups, 0);
});

test('a rejected shared digest follows the existing safe enhancement fallback', async () => {
  const harness = createHarness({ texts: ['same source', 'same source'], cryptoMode: 'reject' });

  await harness.ready();

  assert.equal(harness.calls.length, 1);
  assert.equal(harness.calls[0].text, 'same source');
  assert.ok(harness.blocks.every(block => Object.keys(block.dataset).length === 0));
  assert.ok(harness.warnings.some(([message]) => String(message).includes('enhancements unavailable')));
  assert.equal(harness.events[0]?.detail?.groups, 0);
});
