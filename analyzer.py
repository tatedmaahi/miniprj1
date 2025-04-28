import markdown
import re
import requests
from bs4 import BeautifulSoup
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_config(config_path="config.json"):
    """Load the configuration file from the specified path."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in '{config_path}'. Please check the file format.")

def analyze_markdown(file_path, config):
    """Analyze a Markdown file for content statistics (words, headings, links, images, broken links)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file '{file_path}' was not found.")
    except UnicodeDecodeError:
        raise UnicodeDecodeError(f"Unable to decode '{file_path}' with UTF-8 encoding.")

    # Word count with min_word_length
    words = [word for word in content.split() if len(word) >= config["analysis"]["min_word_length"]]
    word_count = len(words)

    # Heading count (if enabled)
    heading_count = 0
    if config["analysis"]["include_headings"]:
        heading_count = len(re.findall(r'^#{1,6}\s', content, re.MULTILINE))

    # Convert Markdown to HTML
    html = markdown.markdown(content)
    soup = BeautifulSoup(html, 'html.parser')

    # Link count and validation (if enabled)
    link_count = 0
    broken_links = []
    if config["analysis"]["include_links"]:
        links = soup.find_all('a')
        link_count = len(links)
        if config["link_validation"]["validate_links"]:
            for link in links:
                url = link.get('href')
                if url and url.startswith('http'):
                    try:
                        headers = {'User-Agent': config["link_validation"]["user_agent"]}
                        response = requests.head(url, timeout=config["link_validation"]["timeout"],
                                               allow_redirects=config["link_validation"]["allow_redirects"],
                                               headers=headers)
                        if response.status_code >= 400:
                            broken_links.append(url)
                    except requests.RequestException:
                        broken_links.append(url)

    # Image count (if enabled)
    image_count = 0
    if config["analysis"]["include_images"]:
        images = soup.find_all('img')
        image_count = len(images)

    return {
        'file': file_path,
        'words': word_count,
        'headings': heading_count,
        'links': link_count,
        'images': image_count,
        'broken_links': broken_links
    }

def generate_html_report(report, config):
    """Generate an HTML report with visualizations."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Markdown Analysis Report</title>
        <style>
            body {{ font-family: {config['visual_report']['font_family']}; margin: {config['visual_report']['margin']}; }}
            h1 {{ color: #333; }}
            .chart {{ margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report for {report['file']}</h1>
        <ul>
            <li>Words: {report['words']}</li>
            <li>Headings: {report['headings']}</li>
            <li>Links: {report['links']}</li>
            <li>Images: {report['images']}</li>
            <li>Broken Links: {', '.join(report['broken_links']) if report['broken_links'] else 'None'}</li>
        </ul>
        <div class="chart">
            <img src="chart.png" alt="Analysis Chart">
        </div>
    </body>
    </html>
    """
    
    # Generate bar chart
    plt.figure(figsize=(config["visual_report"]["chart_width"], config["visual_report"]["chart_height"]))
    sns.barplot(x=['Words', 'Headings', 'Links', 'Images'], 
                y=[report['words'], report['headings'], report['links'], report['images']],
                color=config["visual_report"]["content_color"])
    plt.title("Markdown Content Analysis")
    plt.savefig("chart.png")
    plt.close()

    # Save HTML report
    with open(config["visual_report"]["default_output_file"], 'w', encoding='utf-8') as f:
        f.write(html_content)

def print_report(report):
    """Print the analysis report in a formatted manner."""
    print(f"Analysis Report for {report['file']}:")
    print(f"- Words: {report['words']}")
    print(f"- Headings: {report['headings']}")
    print(f"- Links: {report['links']}")
    print(f"- Images: {report['images']}")
    if report['broken_links']:
        print(f"- Broken Links: {', '.join(report['broken_links'])}")
    else:
        print("- No broken links found.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python analyzer.py <file.md>")
    else:
        config = load_config()
        report = analyze_markdown(sys.argv[1], config)
        print_report(report)
        generate_html_report(report, config)