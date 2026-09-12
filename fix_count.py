with open("index.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('aria-label="57 tutorials">57</span>', 'aria-label="58 tutorials">58</span>')

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)
