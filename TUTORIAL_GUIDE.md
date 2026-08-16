# Tutorial Creation Guide for OmicsHub

Complete guide for creating and adding new bioinformatics tutorials to your OmicsHub website.

## 📝 Tutorial Structure

Every tutorial follows a consistent structure to ensure quality and readability:

### 1. Front Matter (Required)

Start every tutorial with YAML front matter:

```yaml
---
title: "Your Tutorial Title: Descriptive and SEO-Friendly"
date: "YYYY-MM-DD"
author: "Author Name"
category: "Category Name"
excerpt: "Brief 1-2 sentence description that appears in tutorial listings and search results"
image: "images/tutorial-image.png"
---
```

**Field Descriptions**:
- `title`: Clear, descriptive title (60-80 characters for SEO)
- `date`: Publication date in YYYY-MM-DD format
- `author`: Author name (can be "OmicsHub Team" or individual name)
- `category`: One of the predefined categories (see categories section)
- `excerpt`: 150-200 character summary for listings and meta descriptions
- `image`: Path to tutorial header image (relative to project root)

### 2. Tutorial Content Structure

Follow this recommended structure for consistency:

```markdown
# Tutorial Title (H1 - matches front matter title)

![Tutorial Image](images/your-image.png)

## Introduction/Overview
Brief introduction explaining what readers will learn and why it matters.

## Prerequisites (if applicable)
List what readers should know or have installed before starting.

## Main Content Sections
Break content into logical sections with H2 headers (##).

### Subsections
Use H3 headers (###) for subsections within main topics.

## Practical Examples
Include hands-on examples with code blocks.

## Troubleshooting (if applicable)
Common issues and solutions.

## Conclusion
Summary of what was covered and next steps.

## Next Steps/Related Tutorials
Links to related content.

---
*Footer with contact/feedback information*
```

## 📂 File Organization

### Naming Convention

Use this format for tutorial files:
```
YYYY-MM-DD-tutorial-slug.md
```

**Examples**:
- `2024-08-15-introduction-to-bioinformatics.html`
- `2024-08-14-command-line-part1.html`
- `2024-08-13-conda-mamba-part1.html`

**Rules**:
- Use hyphens (not underscores or spaces)
- Keep slugs descriptive but concise
- Use lowercase letters only
- Date should match the `date` field in front matter

### Directory Structure

```
lessons/
├── 2024-08-15-introduction-to-bioinformatics.html
├── 2024-08-14-command-line-part1.html
├── 2024-08-13-conda-mamba-part1.html
└── 2024-08-12-scrna-seq-basics.html

images/
├── bioinformatics-intro.png
├── command-line-terminal.png
├── conda-environment.png
└── single-cell-analysis.png
```

## 🏷️ Categories

Use these predefined categories to ensure consistency:

### Primary Categories
- **Bioinformatics**: General bioinformatics concepts and workflows
- **Shell Commands**: Command line tutorials and Unix/Linux skills
- **Conda**: Package management with Conda and Mamba
- **Single-cell RNA-seq**: Single-cell analysis techniques and tools
- **HPC**: High-performance computing and cluster usage
- **R Programming**: R language tutorials for bioinformatics
- **Python Programming**: Python tutorials for computational biology
- **Statistics**: Statistical methods in bioinformatics
- **Genomics**: Genome analysis and genomic data processing
- **Transcriptomics**: RNA-seq and gene expression analysis

### Adding New Categories

To add a new category:
1. Use it in tutorial front matter
2. The website automatically detects and lists new categories
3. Consider if it fits with existing categories first
4. Update this guide with the new category

## 🖼️ Images and Media

### Image Guidelines

**Technical Requirements**:
- **Format**: PNG or JPG
- **Size**: 1200x630px for header images (optimal for social sharing)
- **File size**: Under 500KB (optimize for web)
- **Naming**: Use descriptive, hyphenated names

**Content Guidelines**:
- Use professional, clean illustrations
- Ensure images are relevant to tutorial content
- Include alt text for accessibility
- Consider color contrast and readability

### Creating Tutorial Images

**Option 1: Generate with AI**
Use the provided image generation tools to create custom illustrations:

```markdown
Generate a professional illustration showing [describe your concept]
- Use clean, modern design
- Include relevant scientific elements
- Use a professional color palette
- Make it suitable for educational content
```

**Option 2: Use Free Resources**
- **Unsplash**: High-quality free photos
- **Pixabay**: Free images and illustrations
- **Bioicons**: Scientific icons and illustrations
- **Freepik**: Professional illustrations (attribution required)

### Image Optimization

Before adding images:

1. **Resize appropriately**:
   ```bash
   # Using ImageMagick
   convert large-image.png -resize 1200x630^ -gravity center -extent 1200x630 optimized-image.png
   ```

2. **Compress for web**:
   - Use tools like TinyPNG or ImageOptim
   - Aim for under 500KB file size
   - Balance quality vs. file size

3. **Add to repository**:
   ```bash
   # Add image to images directory
   cp optimized-image.png images/tutorial-name-image.png
   ```

## ✍️ Writing Guidelines

### Tone and Style

**Target Audience**: Researchers and students learning bioinformatics
**Tone**: Professional but approachable, educational, encouraging
**Style**: Clear, concise, practical

### Writing Best Practices

#### 1. Use Clear, Descriptive Headers
```markdown
# Good
## Installing Conda on macOS: Step-by-Step Guide

# Avoid
## Installation
```

#### 2. Write Engaging Introductions
Start with why the topic matters:
```markdown
# Good
Single-cell RNA sequencing has revolutionized our understanding of cellular heterogeneity. Instead of measuring average gene expression across millions of cells, scRNA-seq allows us to peek inside individual cells and measure their unique molecular signatures.

# Avoid
This tutorial covers single-cell RNA-seq analysis.
```

#### 3. Use Active Voice
```markdown
# Good
Run the following command to install the package:

# Avoid
The following command should be run to install the package:
```

#### 4. Include Practical Examples
Always provide concrete, runnable examples:
```markdown
# Good
```bash
# Count sequences in a FASTA file
grep -c ">" sequences.fasta
# Output: 1250
```

# Avoid
Use grep to count sequences.
```

#### 5. Explain the "Why" Not Just the "How"
```markdown
# Good
We use the `-c` flag with grep because it counts matching lines instead of displaying them. This is much faster for large files and gives us exactly the information we need.

# Avoid
Use `grep -c` to count lines.
```

### Code Block Guidelines

#### Syntax Highlighting
Always specify the language for proper highlighting:

```markdown
```bash
# Bash commands
ls -la
```

```r
# R code
library(Seurat)
data <- Read10X("data/")
```

```python
# Python code
import pandas as pd
df = pd.read_csv("data.csv")
```
```

#### Code Comments
Include helpful comments in code blocks:
```bash
# Download the reference genome
wget https://example.com/genome.fa.gz

# Extract the compressed file
gunzip genome.fa.gz

# Index the genome for alignment
bwa index genome.fa
```

#### Expected Output
Show expected output when helpful:
```bash
$ ls -la
total 24
drwxr-xr-x  4 user user 4096 Aug 15 10:30 .
drwxr-xr-x  3 user user 4096 Aug 15 10:29 ..
-rw-r--r--  1 user user 1234 Aug 15 10:30 data.txt
```

## 🔍 SEO and Discoverability

### SEO Best Practices

#### 1. Optimize Titles
- Include primary keyword
- Keep under 60 characters
- Make it descriptive and compelling

#### 2. Write Compelling Excerpts
- 150-200 characters
- Include main keywords
- Summarize key benefits/learnings

#### 3. Use Descriptive Headers
- Include relevant keywords naturally
- Structure content logically
- Use H2, H3 hierarchy properly

#### 4. Internal Linking
Link to related tutorials:
```markdown
For more background on command line basics, see our [detailed command line tutorial](command-line-part1.html).
```

#### 5. External Linking
Link to authoritative sources:
```markdown
For more information, see the [official Conda documentation](https://docs.conda.io/).
```

## 🧪 Testing Your Tutorial

### Content Review Checklist

Before publishing, verify:

- [ ] **Accuracy**: All commands and code work as described
- [ ] **Completeness**: Tutorial covers promised topics thoroughly
- [ ] **Clarity**: Instructions are clear and unambiguous
- [ ] **Flow**: Logical progression from basic to advanced concepts
- [ ] **Examples**: Include practical, relevant examples
- [ ] **Links**: All internal and external links work
- [ ] **Images**: All images display correctly and are relevant
- [ ] **Code**: All code blocks have proper syntax highlighting
- [ ] **Grammar**: Proofread for spelling and grammar errors

### Technical Testing

1. **Local Testing**:
   ```bash
   # Start local server
   python -m http.server 8000

   # Test in browser
   open http://localhost:8000
   ```

2. **Verify Tutorial Loading**:
   - Check tutorial appears in listings
   - Verify category filtering works
   - Test search functionality
   - Confirm images load properly

3. **Mobile Testing**:
   - Test on mobile devices
   - Verify responsive design
   - Check code block scrolling

## 📊 Tutorial Performance

### Tracking Success

Monitor tutorial performance through:

1. **Google Analytics** (if configured):
   - Page views and time on page
   - Bounce rate
   - User engagement

2. **GitHub Repository**:
   - Star count and forks
   - Issues and discussions
   - Community feedback

3. **User Feedback**:
   - Comments and questions
   - Social media mentions
   - Email feedback

### Updating Tutorials

Keep tutorials current by:

1. **Regular Review**: Check tutorials quarterly for outdated information
2. **Software Updates**: Update version numbers and installation instructions
3. **User Feedback**: Address common questions and issues
4. **Link Maintenance**: Verify external links still work

## 📋 Tutorial Templates

### Basic Tutorial Template

```markdown
---
title: "Tutorial Title: Clear and Descriptive"
date: "2024-MM-DD"
author: "Your Name"
category: "Appropriate Category"
excerpt: "Brief description of what readers will learn and why it's valuable."
image: "images/tutorial-image.png"
---

# Tutorial Title

![Tutorial Image](images/tutorial-image.png)

## Introduction

Brief introduction explaining the importance and scope of the tutorial.

## Prerequisites

What readers should know or have installed:
- Prerequisite 1
- Prerequisite 2
- Prerequisite 3

## Main Section 1

Content with examples:

```bash
# Example command
command --option value
```

### Subsection

More detailed information.

## Main Section 2

Continue with logical progression.

## Troubleshooting

Common issues and solutions:

**Problem**: Description of issue
**Solution**: How to fix it

## Conclusion

Summary of what was covered and key takeaways.

## Next Steps

Suggestions for further learning:
- [Related Tutorial 1](link)
- [Related Tutorial 2](link)

---

*Questions about this tutorial? [Contact us](contact.html) for help!*
```

### Advanced Tutorial Template

For complex, multi-part tutorials:

```markdown
---
title: "Advanced Topic: Comprehensive Guide"
date: "2024-MM-DD"
author: "Expert Name"
category: "Advanced Category"
excerpt: "In-depth guide covering advanced concepts with practical applications."
image: "images/advanced-tutorial.png"
---

# Advanced Topic: Comprehensive Guide

![Advanced Tutorial](images/advanced-tutorial.png)

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Part 1: Foundation](#part-1-foundation)
4. [Part 2: Implementation](#part-2-implementation)
5. [Part 3: Advanced Techniques](#part-3-advanced-techniques)
6. [Real-World Applications](#real-world-applications)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Conclusion](#conclusion)

## Overview

Comprehensive introduction to the topic.

## Prerequisites

Detailed list of requirements:
- Technical prerequisites
- Software requirements
- Background knowledge needed

## Part 1: Foundation

Build understanding step by step.

## Part 2: Implementation

Practical implementation with examples.

## Part 3: Advanced Techniques

Advanced concepts and techniques.

## Real-World Applications

How to apply these concepts in research.

## Best Practices

Professional recommendations and tips.

## Troubleshooting

Comprehensive troubleshooting guide.

## Conclusion

Summary and next steps.

---

*This is an advanced tutorial. Need help getting started? Check out our [beginner tutorials](tutorials.html) first.*
```

## 🎯 Content Strategy

### Tutorial Series Planning

Plan related tutorials as a series:

1. **Beginner Series**:
   - Introduction to concepts
   - Basic tools and setup
   - Simple examples

2. **Intermediate Series**:
   - Practical applications
   - Common workflows
   - Problem-solving

3. **Advanced Series**:
   - Complex analyses
   - Optimization techniques
   - Research applications

### Content Calendar

Plan tutorial releases:
- **Weekly releases**: Maintain engagement
- **Seasonal topics**: Align with academic calendar
- **Trending topics**: Address current research interests
- **User requests**: Respond to community needs

## 🤝 Community Engagement

### Encouraging Feedback

Include calls-to-action in tutorials:
```markdown
## Your Turn!

Try this tutorial and let us know how it goes:
- Share your results on social media with #OmicsHub
- Ask questions in our [GitHub discussions](link)
- Suggest improvements via [email](contact.html)
```

### Building Community

- Respond to questions promptly
- Acknowledge contributions
- Feature user success stories
- Create collaborative tutorials

## 📈 Continuous Improvement

### Regular Updates

1. **Monthly Review**: Check for outdated information
2. **Quarterly Refresh**: Update screenshots and examples
3. **Annual Overhaul**: Major updates for significant changes

### Quality Metrics

Track tutorial quality:
- User engagement time
- Completion rates
- Feedback scores
- Error reports

---

**Ready to create your first tutorial? Start with our [basic template](#basic-tutorial-template) and remember: great tutorials combine clear explanations with practical examples. Happy writing! 📝**

