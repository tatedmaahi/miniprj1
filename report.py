import markdown
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os

def analyze_markdown(file_path):
    """Analyze a Markdown file for content statistics (words, headings, links, images, broken links)."""
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
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code >= 400:
                    broken_links.append(url)
            except requests.RequestException:
                broken_links.append(url)

    return {
        'file': file_path,
        'words': word_count,
        'headings': heading_count,
        'links': link_count,
        'images': image_count,
        'broken_links': broken_links
    }

def generate_html_report(report, output_path='report.html'):
    """Generate an HTML report with charts for the Markdown analysis."""
    # Prepare data for the bar chart
    stats_data = {
        'Metric': ['Words', 'Headings', 'Links', 'Images'],
        'Count': [report['words'], report['headings'], report['links'], report['images']]
    }
    stats_df = pd.DataFrame(stats_data)

    # Generate bar chart using Plotly
    fig = px.bar(stats_df, x='Metric', y='Count', title='Markdown Content Statistics',
                 labels={'Count': 'Count', 'Metric': 'Metric'},
                 color='Metric', color_discrete_sequence=px.colors.qualitative.Pastel)
    chart_html = pio.to_html(fig, full_html=False)

    # Prepare broken links table
    broken_links_df = pd.DataFrame(report['broken_links'], columns=['Broken Links']) if report['broken_links'] else pd.DataFrame(columns=['Broken Links'])
    broken_links_table = broken_links_df.to_html(index=False, classes='table table-striped')

    # Generate the full HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Markdown Analysis Report</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
        <style>
            body {{ margin: 20px; font-family: Arial, sans-serif; }}
            h1 {{ color: #333; }}
            .container {{ max-width: 900px; margin: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Markdown Analysis Report for {report['file']}</h1>
            <h3>Content Statistics</h3>
            {chart_html}
            <h3>Broken Links</h3>
            {broken_links_table if report['broken_links'] else '<p>No broken links found.</p>'}
        </div>
    </body>
    </html>
    """

    # Write the HTML report to a file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return output_path

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python report_generator.py <file.md>")
    else:
        report = analyze_markdown(sys.argv[1])
        output_file = generate_html_report(report)
        print(f"HTML report generated: {output_file}")