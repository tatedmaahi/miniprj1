# Markdown File Analyzer

A simple tool to analyze .md files, counting words, headings, links, images, validating links and to Output a summary.

## Features
- Counts words, headings, links, and images.
- Checks for broken links.
- Outputs a summary report.

## Installation
```bash
git clone https://github.com/tatedmaahi/miniprj1.git
cd markdown-analyzer
pip install -r requirements.txt 

## Weather Dashboard CLI

A command-line Python tool that fetches current weather and 24-hour forecasts for any city using the OpenWeatherMap API. It also maintains a local history of past queries.

## Features

- Current weather conditions (temperature, humidity, wind, etc.)
- 24-hour forecast (next 8 data points, 3-hour interval)
- JSON-based history logging
- Easy-to-use CLI interface
- Environment variable support for API key security

## Requirements

- Python 3.7+
- OpenWeatherMap API Key(https://openweathermap.org/api)
- Internet connection

## Installation

1. Clone the repository or download the script.
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate        # On Windows

   # Personal Task Manager (Mini-Project #3)

A simple CLI-based Task Manager for SEM4-Software Engineering. Manage tasks using a SQLite database with CRUD operations and statistics.

## Features
- Add, view, update, and delete tasks (description, priority, due date).
- View task statistics (total, pending, completed).
- User-friendly CLI with screen clearing.

## Requirements
- Python 3.6+
- SQLite (included with Python)

## Setup
<<<<<<< HEAD
1. Clone the repo (if applicable): git clone https://github.com/tatedmaahi/miniprj1.git
2. Set up a virtual environment: python -m venv venv and .\venv\Scripts\activate (Windows)
3. Run: python task_manager.py

## Usage Example
Task Manager
1.  Add Task  2. View Tasks  3. Mark Completed  4. Delete Task  5. Stats  6. Exit Choose (1-6): 1 Description: Finish Project Priority (Low/Medium/High): High Due Date (YYYY-MM-DD): 2025-05-10 Task added!

## Project Structure
- database.py: Initializes SQLite database.
- task_manager.py: Main application.
- tasks.db: SQLite database (auto-created).
- README.md: Documentation.

## Screenshots
- Create: ![Create](create_screenshot.png)
- Read: ![Read](read_screenshot.png)
- Update: ![Update](update_screenshot.png)
- Delete: ![Delete](delete_screenshot.png)

# Document Management System

A simple system to upload PDF and .md files, built for a capstone project.

## Setup
1. Clone the repo: `git clone https://github.com/tatedmaahi/miniprj1.git && cd document-management-system`
2. Switch to branch: `git checkout feature/document-upload`
3. Create virtual environment: `python -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize database: `sqlite3 documents.db < database.sql`
6. Run the app: `python app.py`

## Testing with Postman
- Open Postman in VSCode.
- Create a POST request to `http://127.0.0.1:5000/upload`.
- In the body, select `form-data`:
  - Key: `file`, Type: File, Value: Choose a .pdf or .md file.
  - Key: `category`, Type: Text, Value: Work.
- Send the request and check for `{"message": "File uploaded successfully"}`.

## Browser Testing
- Open `http://127.0.0.1:5000/upload`.
- Choose a file, select a category, and click Upload.
- Look for a green success message.