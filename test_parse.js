const fs = require('fs');

function parseTutorial(content, filename) {
    const frontMatterMatch = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    if (!frontMatterMatch) {
        console.log("No frontmatter match");
        return;
    }
    const frontMatter = frontMatterMatch[1];
    const metadata = {};
    frontMatter.split('\n').forEach(line => {
        const match = line.match(/^(\w+):\s*(.+)$/);
        if (match) {
            metadata[match[1]] = match[2].replace(/^["']|["']$/g, '');
        } else {
            console.log("Failed to match line:", JSON.stringify(line));
        }
    });
    console.log(metadata);
}

const content = fs.readFileSync('lessons/conda-bioinformatics-guide.md', 'utf8');
parseTutorial(content, 'conda-bioinformatics-guide.md');
