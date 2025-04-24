import markdown
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px

def analyze_markdown(file_path):
    """Check a Markdown file for words, headings, links, and images."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
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
                response = requests.head(url, timeout=5)
                if response.status_code >= 400:
                    broken_links.append(url)
            except:
                broken_links.append(url)

    return {
        'file': file_path,
        'words': word_count,
        'headings': heading_count,
        'links': link_count,
        'images': image_count,
        'broken_links': broken_links
    }

def make_visual_report(report, file_name='visrep.html'):
    """Make a simple HTML report with a chart."""
    # Make a chart for words, headings, links, and images
    data = {
        'Thing': ['Words', 'Headings', 'Links', 'Images'],
        'Number': [report['words'], report['headings'], report['links'], report['images']]
    }
    df = pd.DataFrame(data)
    chart = px.bar(df, x='Thing', y='Number', title='File Stats')
    chart_html = chart.to_html(full_html=False)

    # Add broken links as text
    broken_text = '<p>Broken Links: ' + ', '.join(report['broken_links']) + '</p>' if report['broken_links'] else '<p>No broken links.</p>'

    # Put it all in an HTML file
    html = f"""
    <html>
    <head><title>Visual Report</title></head>
    <body>
        <h1>Report for {report['file']}</h1>
        {chart_html}
        {broken_text}
    </body>
    </html>
    """
    with open(file_name, 'w', encoding='utf-8') as f:  # Added encoding='utf-8'
        f.write(html)
    print(f"Report saved as {file_name}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Use: python report.py <file.md>")
    else:
        result = analyze_markdown(sys.argv[1])
        make_visual_report(result)