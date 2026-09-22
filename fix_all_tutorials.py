with open("index.html", "r", encoding="utf-8") as file:
    content = file.read()

new_content = content.replace('href="#all-tutorials"', 'href="tutorials.html"')

if new_content != content:
    with open("index.html", "w", encoding="utf-8") as file:
        file.write(new_content)
    print("Fixed #all-tutorials in index.html")
