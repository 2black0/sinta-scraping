#!/usr/bin/env python3
"""
SINTA Scraping Web Interface
Flask-based web application for SINTA data scraping with elegant UI
"""

import os
import sys
import json
import subprocess
import threading
import time
import requests
from datetime import datetime
from pathlib import Path

try:
    from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
    from werkzeug.utils import secure_filename
except ImportError as e:
    print(f"❌ Error: Missing required dependencies. Please install Flask:")
    print("   pip install flask requests")
    sys.exit(1)

# Add parent directory to path to import sinta-cli modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sinta-scraping-web-2025'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Global variables for tracking scraping status
scraping_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'results': {},
    'start_time': None,
    'output_dir': None
}

def get_output_dir():
    """Get current output directory name"""
    today = datetime.now()
    date_str = today.strftime('%d%m%Y')
    return f'output-{date_str}'

def get_available_outputs():
    """Get list of available output directories"""
    outputs = []
    parent_dir = Path(__file__).parent.parent
    
    for item in parent_dir.iterdir():
        if item.is_dir() and item.name.startswith('output-'):
            try:
                # Extract date from directory name
                date_part = item.name.replace('output-', '')
                date_obj = datetime.strptime(date_part, '%d%m%Y')
                
                # Count CSV files
                csv_files = list(item.glob('*.csv'))
                
                outputs.append({
                    'name': item.name,
                    'date': date_obj.strftime('%d %B %Y'),
                    'path': str(item),
                    'files_count': len(csv_files),
                    'files': [f.name for f in csv_files]
                })
            except ValueError:
                continue
    
    # Sort by date (newest first)
    outputs.sort(key=lambda x: x['name'], reverse=True)
    return outputs

def load_lecturer_ids():
    """Load lecturer IDs from dosen.txt"""
    parent_dir = Path(__file__).parent.parent
    dosen_file = parent_dir / 'dosen.txt'
    
    lecturers = []
    if dosen_file.exists():
        with open(dosen_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    lecturers.append(line)
    
    return lecturers

def save_lecturer_ids(lecturer_ids):
    """Save lecturer IDs to dosen.txt"""
    parent_dir = Path(__file__).parent.parent
    dosen_file = parent_dir / 'dosen.txt'
    
    with open(dosen_file, 'w', encoding='utf-8') as f:
        f.write("# Daftar ID SINTA Dosen\n")
        f.write("# Satu ID per baris\n")
        f.write("# ID SINTA dari URL profil: https://sinta.kemdikbud.go.id/authors/profile/ID\n\n")
        
        for lecturer_id in lecturer_ids:
            if lecturer_id.strip():
                f.write(f"{lecturer_id.strip()}\n")

def run_scraping_command(categories):
    """Run scraping command in background"""
    global scraping_status
    
    try:
        scraping_status['running'] = True
        scraping_status['progress'] = 0
        scraping_status['message'] = 'Initializing scraping...'
        scraping_status['start_time'] = datetime.now()
        scraping_status['output_dir'] = get_output_dir()
        
        parent_dir = Path(__file__).parent.parent
        
        # Build command
        cmd = [sys.executable, str(parent_dir / 'sinta-cli.py')]
        
        if categories and len(categories) > 0:
            for category in categories:
                if category == 'publikasi-scopus':
                    cmd.append('--publikasi-scopus')
                elif category == 'publikasi-gs':
                    cmd.append('--publikasi-gs')
                elif category == 'publikasi-wos':
                    cmd.append('--publikasi-wos')
                elif category == 'publikasi':
                    cmd.append('--publikasi')
                else:
                    cmd.append(f'--{category}')
        
        scraping_status['message'] = f'Running command: {" ".join(cmd)}'
        scraping_status['progress'] = 10
        
        # Run the command
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(parent_dir)
        )
        
        scraping_status['progress'] = 20
        scraping_status['message'] = 'Scraping in progress...'
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            scraping_status['progress'] = 100
            scraping_status['message'] = 'Scraping completed successfully!'
            scraping_status['results']['success'] = True
            scraping_status['results']['output'] = stdout
        else:
            scraping_status['message'] = f'Scraping failed: {stderr}'
            scraping_status['results']['success'] = False
            scraping_status['results']['error'] = stderr
            
    except Exception as e:
        scraping_status['message'] = f'Error: {str(e)}'
        scraping_status['results']['success'] = False
        scraping_status['results']['error'] = str(e)
    
    finally:
        scraping_status['running'] = False

@app.route('/')
def index():
    """Redirect to simple interface"""
    return redirect(url_for('simple_interface'))

@app.route('/api/lecturers', methods=['GET', 'POST'])
def manage_lecturers():
    """API endpoint for managing lecturer IDs"""
    if request.method == 'GET':
        lecturer_ids = load_lecturer_ids()
        return jsonify({'lecturer_ids': lecturer_ids})
    
    elif request.method == 'POST':
        data = request.get_json()
        lecturer_ids = data.get('lecturer_ids', [])
        
        try:
            save_lecturer_ids(lecturer_ids)
            return jsonify({'success': True, 'message': 'Lecturer IDs saved successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    """Start scraping process"""
    global scraping_status
    
    if scraping_status['running']:
        return jsonify({'success': False, 'error': 'Scraping is already running'})
    
    data = request.get_json()
    categories = data.get('categories', [])
    
    # Reset status
    scraping_status = {
        'running': False,
        'progress': 0,
        'message': '',
        'results': {},
        'start_time': None,
        'output_dir': None
    }
    
    # Start scraping in background thread
    thread = threading.Thread(target=run_scraping_command, args=(categories,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Scraping started'})

@app.route('/api/scraping-status')
def get_scraping_status():
    """Get current scraping status"""
    status = scraping_status.copy()
    
    if status['start_time']:
        elapsed = datetime.now() - status['start_time']
        status['elapsed_time'] = str(elapsed).split('.')[0]  # Remove microseconds
    
    return jsonify(status)

@app.route('/api/outputs')
def get_outputs():
    """Get available output directories"""
    available_outputs = get_available_outputs()
    return jsonify({'outputs': available_outputs})

@app.route('/download/<path:output_dir>/<filename>')
def download_file(output_dir, filename):
    """Download a specific CSV file"""
    parent_dir = Path(__file__).parent.parent
    file_path = parent_dir / output_dir / filename
    
    if file_path.exists() and file_path.suffix == '.csv':
        return send_file(str(file_path), as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/csv-data/<path:output_dir>/<filename>')
def get_csv_data(output_dir, filename):
    """Get CSV data for display"""
    parent_dir = Path(__file__).parent.parent
    file_path = parent_dir / output_dir / filename
    
    if not file_path.exists() or file_path.suffix != '.csv':
        return jsonify({'error': 'File not found'}), 404
    
    try:
        import csv
        
        data = []
        columns = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            columns = csv_reader.fieldnames
            
            for row in csv_reader:
                # Clean empty values
                cleaned_row = {k: v if v else '-' for k, v in row.items()}
                data.append(cleaned_row)
        
        # Basic statistics
        stats = {
            'total_rows': len(data),
            'total_columns': len(columns),
            'file_size': f"{file_path.stat().st_size / 1024:.1f} KB"
        }
        
        # Category-specific stats
        if 'profil' in filename.lower() and data:
            if 'Universitas' in columns:
                universities = set(row.get('Universitas', '') for row in data if row.get('Universitas'))
                stats['universities'] = len(universities)
            
            if 'SINTA Score Overall' in columns:
                try:
                    scores = [float(row.get('SINTA Score Overall', 0)) for row in data 
                             if row.get('SINTA Score Overall') and row.get('SINTA Score Overall').replace('.', '').isdigit()]
                    if scores:
                        stats['avg_sinta_score'] = round(sum(scores) / len(scores), 1)
                except:
                    stats['avg_sinta_score'] = 'N/A'
        
        elif 'publikasi' in filename.lower() and data:
            if 'Tahun' in columns:
                try:
                    years = [int(row.get('Tahun', 0)) for row in data 
                            if row.get('Tahun') and str(row.get('Tahun')).isdigit()]
                    if years:
                        stats['year_range'] = f"{min(years)} - {max(years)}"
                except:
                    stats['year_range'] = 'N/A'
            
            if 'Jurnal' in columns:
                journals = set(row.get('Jurnal', '') for row in data if row.get('Jurnal'))
                stats['unique_journals'] = len(journals)
        
        return jsonify({
            'success': True,
            'data': data,
            'columns': columns,
            'stats': stats,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to read CSV: {str(e)}'}), 500

@app.route('/viewer')
def csv_viewer():
    """CSV viewer page"""
    available_outputs = get_available_outputs()
    return render_template('viewer.html', available_outputs=available_outputs)

@app.route('/simple')
def simple_interface():
    """Simple operational interface"""
    lecturer_ids = load_lecturer_ids()
    available_outputs = get_available_outputs()
    
    return render_template('simple.html', 
                         lecturer_ids=lecturer_ids,
                         available_outputs=available_outputs,
                         current_output_dir=get_output_dir())

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("🚀 SINTA Scraping Web Interface")
    print("=" * 50)
    print("🌐 Starting Flask server...")
    print("📁 Open http://localhost:5000 in your browser")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
