const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'script.js'), 'utf8');
const start = source.indexOf('function normalizeSearchText(');
const end = source.indexOf('function filterTutorialCards(', start);
assert.ok(start >= 0 && end > start);
const context = {};
vm.runInNewContext(source.slice(start, end) + '\nthis.api = {normalizeSearchText, searchTextMatches};', context);
const {normalizeSearchText, searchTextMatches} = context.api;
const reporting = normalizeSearchText('research-reporting-interpretation Research Reporting and Interpretation');
const unrelated = normalizeSearchText('metagenomics-kraken2-bracken Metagenomics Classification');

for (const query of ['R Markdown', 'RMarkdown', 'rmarkdown', 'Rmd', '.Rmd', 'R-Markdown']) {
  test(`${query} finds the real reporting lesson, not an unrelated lesson`, () => {
    const terms = normalizeSearchText(query).split(' ').filter(Boolean);
    assert.equal(searchTextMatches(reporting, terms), true);
    assert.equal(searchTextMatches(unrelated, terms), false);
  });
}
test('existing RNA-seq and HPC aliases keep working', () => {
  assert.equal(searchTextMatches('single cell rna seq', ['scrnaseq']), true);
  assert.equal(searchTextMatches('high performance computing', ['hpc']), true);
  assert.equal(searchTextMatches('whole exome sequencing', ['wes']), true);
});
test('empty and literal queries keep their original behavior', () => {
  assert.equal(searchTextMatches(reporting, []), true);
  assert.equal(searchTextMatches(reporting, ['research', 'reporting']), true);
  assert.equal(searchTextMatches(reporting, ['not', 'present']), false);
});
