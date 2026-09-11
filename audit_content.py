import glob
from html.parser import HTMLParser

class TutorialParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_pre = False
        self.in_code = False
        self.code_classes = []
        self.pre_without_lang = 0
        self.text_content = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == 'pre':
            self.in_pre = True
        elif tag == 'code' and self.in_pre:
            self.in_code = True
            classes = dict(attrs).get('class', '')
            self.code_classes.append(classes)
            if 'language-' not in classes:
                self.pre_without_lang += 1

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.in_pre = False
        elif tag == 'code':
            self.in_code = False

    def handle_data(self, data):
        self.text_content += data + " "

def audit():
    files = glob.glob('*.html')
    ignore = ['index.html', 'about.html', 'contact.html', 'services.html', 'start-here.html', '404.html', 'success.html']
    tutorials = [f for f in files if f not in ignore]
    
    issues = []
    
    for f in tutorials:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            parser = TutorialParser()
            parser.feed(content)
            
            # Check tabs
            if parser.pre_without_lang > 0:
                issues.append(f"{f}: Found {parser.pre_without_lang} <pre><code> blocks missing a 'language-*' class (breaks code tabs).")
                
            # Check sections
            text = parser.text_content.lower()
            if "learning objectives" not in text:
                issues.append(f"{f}: Missing 'Learning Objectives' section.")
            if "knowledge check" not in text:
                issues.append(f"{f}: Missing 'Knowledge Check' section.")
                
    if issues:
        print("Issues Found:")
        for i in issues:
            print("- " + i)
    else:
        print("All tutorials passed structural and tab audits.")

if __name__ == '__main__':
    audit()
