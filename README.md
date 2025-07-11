# File Download Service

A web service that downloads files from URLs, stores them locally, and serves them via custom URLs with periodic refresh capabilities.

## Features

- Download files from any URL and save to local storage
- Serve downloaded files via custom URL paths
- Web UI for easy configuration and management
- Periodic automatic downloads with customizable intervals
- Manual download triggers
- Persistent configuration storage

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python app.py
```

3. Open http://localhost:5000 in your browser

## Usage

### Web UI
- Access the web interface at http://localhost:5000
- Add new downloads by specifying:
  - URL to download
  - Local file path
  - Serve URL path
  - Optional periodic download interval (in minutes)

### API Endpoints
- `GET /api/downloads` - List all download configurations
- `POST /api/downloads` - Add new download configuration
- `DELETE /api/downloads/<id>` - Delete download configuration
- `POST /api/downloads/<id>/download` - Trigger manual download
- `GET /files/<path>` - Access downloaded files

## File Structure
- `app.py` - Main Flask application
- `templates/index.html` - Web UI
- `downloads/` - Directory for downloaded files
- `downloads_config.json` - Configuration persistence