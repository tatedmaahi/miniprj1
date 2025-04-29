import os
import pytest
from analyzer import load_config, analyze_markdown, generate_html_report, print_report

CONFIG_PATH = "config.json"
MARKDOWN_FILE = "example.md"

def test_load_config():
    config = load_config(CONFIG_PATH)
    assert isinstance(config, dict)
    assert "analysis" in config
    assert "link_validation" in config
    assert "visual_report" in config

def test_analyze_markdown():
    config = load_config(CONFIG_PATH)
    report = analyze_markdown(MARKDOWN_FILE, config)

    assert report["file"] == MARKDOWN_FILE
    assert isinstance(report["words"], int)
    assert isinstance(report["headings"], int)
    assert isinstance(report["links"], int)
    assert isinstance(report["images"], int)
    assert isinstance(report["broken_links"], list)

    assert report["words"] >= 10
    assert report["headings"] == 2
    assert report["links"] == 2
    assert report["images"] == 1
    assert any("nonexistent.example.com" in url for url in report["broken_links"])

def test_generate_html_report_and_files_cleanup():
    config = load_config(CONFIG_PATH)
    report = analyze_markdown(MARKDOWN_FILE, config)

    output_file = config["visual_report"]["default_output_file"]
    chart_file = "chart.png"

    # Generate report
    generate_html_report(report, config)

    # Check if files were created
    assert os.path.exists(output_file)
    assert os.path.exists(chart_file)

    # Clean up
    os.remove(output_file)
    os.remove(chart_file)

def test_print_report_output(capfd):
    config = load_config(CONFIG_PATH)
    report = analyze_markdown(MARKDOWN_FILE, config)
    print_report(report)
    captured = capfd.readouterr()

    assert "Analysis Report for" in captured.out
    assert "- Words:" in captured.out
    assert "- Headings:" in captured.out
    assert "- Links:" in captured.out
    assert "- Images:" in captured.out
    assert "- Broken Links:" in captured.out or "- No broken links" in captured.out