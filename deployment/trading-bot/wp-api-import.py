import requests
from bs4 import BeautifulSoup
import json
import base64

# WordPress site details
wp_url = 'https://lightpink-turkey-164531.hostingersite.com'
wp_user = 'realqualityads@gmail.com'
wp_pass = '3|qXPZG?'

# Source HTML page
source_url = 'https://historicaviationmilitary.com/burtonwoodhome897.html'

def get_html_content():
    """Fetch and parse the source HTML page"""
    try:
        response = requests.get(source_url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching HTML: {e}")
        return None

def extract_main_content(html):
    """Extract main content from HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find main content table
    main_content = None
    for table in soup.find_all('table'):
        # Look for substantial content
        text_content = table.get_text(strip=True)
        if len(text_content) > 200:
            main_content = str(table)
            break
    
    return main_content

def create_wp_page(content):
    """Create a test page in WordPress"""
    # Authentication
    credentials = base64.b64encode(f"{wp_user}:{wp_pass}".encode()).decode()
    
    # API endpoint
    api_url = f"{wp_url}/wp-json/wp/v2/pages"
    
    # Page data
    data = {
        'title': 'Test Import - Burtonwood',
        'content': content,
        'status': 'draft'
    }
    
    # Headers
    headers = {
        'Authorization': f'Basic {credentials}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error creating WordPress page: {e}")
        return None

def main():
    print("Starting import process...")
    
    # Get HTML content
    html_content = get_html_content()
    if not html_content:
        print("Failed to fetch HTML content")
        return
    
    # Extract main content
    main_content = extract_main_content(html_content)
    if not main_content:
        print("Failed to extract main content")
        return
    
    # Create WordPress page
    result = create_wp_page(main_content)
    if result:
        print(f"Test page created successfully!")
        print(f"Page ID: {result.get('id')}")
        print(f"Preview Link: {result.get('link')}")
    else:
        print("Failed to create WordPress page")

if __name__ == "__main__":
    main()
