import markdown
import re
import requests
from bs4 import BeautifulSoup

def analyze_markdown(file_path):
    """Analyze a Markdown file for content statistics (words, headings, links, images, broken links)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Unable to decode '{file_path}' with UTF-8 encoding.")
        
    word_count = len(content.split())
    heading_count = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))
    link_count = 0
    image_count = 0
    broken_links = []

    html = markdown.markdown(content)
    soup = BeautifulSoup(html, 'html.parser')

    links = soup.find_all('a')
    link_count = len(links)
    images = soup.find_all('img')
    image_count = len(images)

    for link in links:
        url = link.get('href')
        if url and url.startswith('http'):
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    broken_links.append(url)
            except requests.RequestException:
                broken_links.append(url)

    report = {
        'file': file_path,
        'words': word_count,
        'headings': heading_count,
        'links': link_count,
        'images': image_count,
        'broken_links': broken_links
    }
def print_report(report):
    """Print the analysis report in a formatted manner."""
    print(f"Analysis Report for {report['file']}:")
    print(f"- Words: {report['words']}")
    print(f"- Headings: {report['headings']}")
    print(f"- Links: {report['links']}")
    print(f"- Images: {report['images']}")
    if report['broken_links']:
        print(f"- Broken Links: {', '.join(broken_links)}")
    else:
        print("- No broken links found.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <file.md>")
    else:
        report = analyze_markdown(sys.argv[1])
        print_report(report)
        