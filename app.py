import os
import json
import requests
from datetime import datetime
from threading import Lock
from flask import Flask, request, render_template, jsonify, send_file, abort
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

app = Flask(__name__)
scheduler = BackgroundScheduler()
scheduler.start()

# Configuration storage
config_file = 'downloads_config.json'
downloads_dir = 'downloads'
data_lock = Lock()

# Ensure downloads directory exists
os.makedirs(downloads_dir, exist_ok=True)

def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

def download_file(url, local_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        full_path = os.path.join(downloads_dir, local_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True, f"Downloaded successfully to {full_path}"
    except Exception as e:
        return False, str(e)

def periodic_download(config_id):
    with data_lock:
        config = load_config()
        if config_id in config:
            item = config[config_id]
            success, message = download_file(item['url'], item['local_path'])
            item['last_download'] = datetime.now().isoformat()
            item['last_status'] = 'success' if success else 'error'
            item['last_message'] = message
            save_config(config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/downloads', methods=['GET'])
def get_downloads():
    return jsonify(load_config())

@app.route('/api/downloads', methods=['POST'])
def add_download():
    data = request.json
    url = data.get('url')
    local_path = data.get('local_path')
    serve_url = data.get('serve_url')
    period = data.get('period', 0)
    
    if not all([url, local_path, serve_url]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    config_id = str(len(load_config()) + 1)
    
    with data_lock:
        config = load_config()
        config[config_id] = {
            'url': url,
            'local_path': local_path,
            'serve_url': serve_url,
            'period': period,
            'created': datetime.now().isoformat(),
            'last_download': None,
            'last_status': None,
            'last_message': None
        }
        save_config(config)
    
    # Schedule periodic download if period > 0
    if period > 0:
        scheduler.add_job(
            func=periodic_download,
            trigger=IntervalTrigger(minutes=period),
            args=[config_id],
            id=f'download_{config_id}',
            replace_existing=True
        )
    
    return jsonify({'id': config_id, 'message': 'Download configuration added'})

@app.route('/api/downloads/<config_id>', methods=['DELETE'])
def delete_download(config_id):
    with data_lock:
        config = load_config()
        if config_id in config:
            del config[config_id]
            save_config(config)
            
            # Remove scheduled job
            try:
                scheduler.remove_job(f'download_{config_id}')
            except:
                pass
            
            return jsonify({'message': 'Download configuration deleted'})
    
    return jsonify({'error': 'Configuration not found'}), 404

@app.route('/api/downloads/<config_id>/download', methods=['POST'])
def manual_download(config_id):
    config = load_config()
    if config_id not in config:
        return jsonify({'error': 'Configuration not found'}), 404
    
    item = config[config_id]
    success, message = download_file(item['url'], item['local_path'])
    
    with data_lock:
        config = load_config()
        config[config_id]['last_download'] = datetime.now().isoformat()
        config[config_id]['last_status'] = 'success' if success else 'error'
        config[config_id]['last_message'] = message
        save_config(config)
    
    return jsonify({'success': success, 'message': message})

@app.route('/files/<path:subpath>')
def serve_file(subpath):
    config = load_config()
    
    # Find which configuration serves this URL
    for item in config.values():
        if item['serve_url'].lstrip('/') == subpath:
            file_path = os.path.join(downloads_dir, item['local_path'])
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                abort(404, description="File not found")
    
    abort(404, description="Serve URL not configured")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)