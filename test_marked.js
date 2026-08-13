const fs = require('fs');
const marked = require('marked');
const text = fs.readFileSync('/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/lessons/scrna-seq-basics.md', 'utf8');
console.log(marked.parse(text).substring(500, 1500));
