import glob
from html.parser import HTMLParser

class ImgParser(HTMLParser):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.errors = []
        self.images = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images += 1
            attr_dict = dict(attrs)
            if 'src' not in attr_dict:
                self.errors.append("Missing src attribute")
            if 'class' in attr_dict:
                classes = attr_dict['class']
                if '  ' in classes:
                    # Not a fatal error, but just checking
                    pass

def check_files(pattern):
    files = glob.glob(pattern)
    total_imgs = 0
    total_errors = 0
    
    for f in files:
        with open(f, 'r') as file:
            content = file.read()
        
        # Check for malformed tags like <img ... > > or missing >
        parser = ImgParser(f)
        try:
            parser.feed(content)
            total_imgs += parser.images
            if parser.errors:
                print(f"Errors in {f}: {parser.errors}")
                total_errors += len(parser.errors)
        except Exception as e:
            print(f"HTML parsing error in {f}: {e}")
            total_errors += 1
            
    print(f"Checked {len(files)} files matching '{pattern}'. Found {total_imgs} images. Total errors: {total_errors}")

check_files("*.html")
check_files("tutorials/*.html")
