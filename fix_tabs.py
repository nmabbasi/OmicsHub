import os
import glob
from bs4 import BeautifulSoup

def update_navbar_active_state(filepath):
    with open(filepath, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    filename = os.path.basename(filepath)
    is_index = filename == 'index.html'

    # Active and inactive classes
    active_class = "nav-link text-blue-600 bg-blue-50 px-3 py-2 rounded-md font-medium"
    inactive_class = "nav-link text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200"

    # Find Desktop Navigation
    desktop_nav = soup.find('div', class_=lambda c: c and 'hidden' in c and 'md:flex' in c and 'items-center' in c)
    if desktop_nav:
        links = desktop_nav.find_all('a', class_='nav-link')
        for link in links:
            # Determine which link should be active
            href = link.get('href', '')
            text = link.get_text(strip=True)

            should_be_active = False
            if is_index and text == 'Home':
                should_be_active = True
            elif filename == 'about.html' and text == 'About':
                should_be_active = True
            elif filename == 'contact.html' and text == 'Contact':
                should_be_active = True

            if should_be_active:
                link['class'] = active_class
            else:
                link['class'] = inactive_class

    # Same for Mobile Navigation
    mobile_nav = soup.find('div', id='mobile-menu')
    if mobile_nav:
        mobile_links = mobile_nav.find_all('a')
        for link in mobile_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if text in ['Home', 'Tutorials', 'About', 'Contact']:
                # Mobile active state
                mobile_active = "text-blue-600 font-bold bg-blue-50 px-4 py-2 rounded-md block"
                mobile_inactive = "text-gray-700 hover:text-blue-600 hover:bg-gray-50 px-4 py-2 rounded-md block transition-colors duration-200"

                should_be_active = False
                if is_index and text == 'Home':
                    should_be_active = True
                elif filename == 'about.html' and text == 'About':
                    should_be_active = True
                elif filename == 'contact.html' and text == 'Contact':
                    should_be_active = True

                if should_be_active:
                    link['class'] = mobile_active
                else:
                    link['class'] = mobile_inactive

    with open(filepath, 'w') as f:
        f.write(str(soup))

html_files = glob.glob('*.html')
for filepath in html_files:
    update_navbar_active_state(filepath)
