// Homepage-only CSS optimization; never alters the original shared stylesheet.
// PurgeCSS: https://github.com/FullHuman/purgecss (MIT).
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const {PurgeCSS} = require('purgecss');
const postcss = require('postcss');
const cssnano = require('cssnano');
const root = path.resolve(__dirname, '..');
const content = ['index.html', 'script.js', 'subscribe-fab.js', 'cookie-consent.js', 'mobile-navigation.js'];
(async () => {
  const result = await new PurgeCSS().purge({
    content: content.map(file => path.join(root, file)),
    css: [path.join(root, 'style.css')],
    defaultExtractor: value => value.match(/[^<>"'`\s]*[^<>"'`\s:]/g) || [],
    safelist: {greedy: [/subscribe/, /telegram/, /legal-menu/, /mobile-menu/, /cookie-consent/, /search-/, /hero-/, /nav-active/, /footer/]},
    dynamicAttributes: ['aria-expanded', 'aria-selected', 'aria-label', 'data-category', 'data-cookie-choice'],
    keyframes: false, variables: false, fontFace: false,
  });
  const min = await postcss([cssnano({preset: ['default', {
    mergeRules: false, mergeLonghand: false, reduceInitial: false,
    convertValues: false, normalizeUrl: false, discardDuplicates: false,
  }]})]).process(result[0].css, {from: undefined});
  const hash = crypto.createHash('sha256');
  for (const file of ['style.css', ...content]) hash.update(fs.readFileSync(path.join(root, file)));
  const output = '/* Homepage-only subset of style.css; generated with PurgeCSS. Original retained. Source SHA256: ' + hash.digest('hex') + ' */\n' + min.css + '\n';
  fs.writeFileSync(path.join(root, 'home-page.min.css'), output);
  console.log('Homepage stylesheet:', Buffer.byteLength(output), 'bytes; original:', fs.statSync(path.join(root, 'style.css')).size, 'bytes');
})().catch(error => {console.error(error); process.exit(1);});
