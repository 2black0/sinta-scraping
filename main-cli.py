#!/usr/bin/env python3
"""
SINTA Scraping Main Application - CLI Version

Aplikasi untuk melakukan scraping data dari SINTA (Sistem Informasi Riset Nasional).
Versi CLI yang menggunakan request untuk login tanpa Selenium.
Mendukung scraping berbagai kategori data: buku, HAKI, publikasi, penelitian, PPM, dan profil.

Usage:
    python main-cli.py                      # Scrape semua kategori untuk semua dosen
    python main-cli.py --buku               # Scrape hanya data buku
    python main-cli.py --haki               # Scrape hanya data HAKI
    python main-cli.py --publikasi          # Scrape semua jenis publikasi (Scopus, Google Scholar, WoS)
    python main-cli.py --publikasi-scopus   # Scrape hanya publikasi Scopus
    python main-cli.py --publikasi-gs       # Scrape hanya publikasi Google Scholar
    python main-cli.py --publikasi-wos      # Scrape hanya publikasi Web of Science
    python main-cli.py --penelitian         # Scrape hanya data penelitian
    python main-cli.py --ppm                # Scrape hanya data pengabdian masyarakat
    python main-cli.py --profil             # Scrape hanya data profil dosen

Author: Refactored from main.py
Date: July 2025
"""

import os
import sys
import time
import json
import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

# External libraries
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


class ConfigManager:
    """Manage application configuration from YAML file"""
    
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            # Try to load from config directory first, then root
            config_paths = [
                os.path.join("config", self.config_file),
                self.config_file
            ]
            
            config_loaded = False
            for config_path in config_paths:
                if os.path.exists(config_path):
                    try:
                        import yaml
                        with open(config_path, 'r', encoding='utf-8') as file:
                            self.config = yaml.safe_load(file)
                        print(f"✅ Loaded configuration from {config_path}")
                        config_loaded = True
                        break
                    except ImportError:
                        print(f"⚠️ PyYAML not installed, using default configuration")
                        break
            
            if not config_loaded:
                print(f"⚠️ Config file {self.config_file} not found, using defaults")
                self._load_default_config()
                
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using defaults")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration"""
        self.config = {
            'session': {
                'test_url': 'https://sinta.kemdikbud.go.id/authors',
                'login_url': 'https://sinta.kemdikbud.go.id/logins',
                'session_file': '.config/session_data.json'
            },
            'scraping': {
                'request_delay': 1,
                'max_retries': 3,
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            },
            'output': {
                'directory_format': 'output-{date}',
                'date_format': '%d%m%Y',
                'csv_encoding': 'utf-8'
            },
            'lecturers': {
                'config_file': 'dosen.txt'
            },
            'logging': {
                'level': 'INFO',
                'show_emoji': True
            }
        }
    
    def get(self, key_path, default=None):
        """Get configuration value by dot notation (e.g., 'session.test_url')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_session_config(self) -> dict:
        """Get session configuration"""
        return {
            'test_url': str(self.get('session.test_url', 'https://sinta.kemdikbud.go.id/authors')),
            'login_url': str(self.get('session.login_url', 'https://sinta.kemdikbud.go.id/logins')),
            'session_file': str(self.get('session.session_file', '.config/session_data.json'))
        }
    
    def get_user_agent(self) -> str:
        """Get User Agent from config"""
        user_agent = self.get('scraping.user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36')
        return str(user_agent) if user_agent is not None else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'


# Global config instance
config = ConfigManager()


class SintaRequestLogin:
    """Login functionality for SINTA using requests only"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': config.get_user_agent(),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Google Chrome";v="138", "Chromium";v="138", "Not:A-Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"'
        }
        self.session.headers.update(self.headers)
    
    def get_csrf_token(self, login_url):
        """Get CSRF token from login page"""
        try:
            print("🔍 Getting CSRF token from login page...")
            response = self.session.get(login_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: Save login page for inspection
            print(f"🔍 Debug: Login page length = {len(response.text)} characters")
            
            # Look for CSRF token in meta tags
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                token = csrf_meta.get('content')
                print(f"✅ Found CSRF token: {token[:20]}...")
                return token
            
            # Look for CSRF token in input fields
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                token = csrf_input.get('value')
                print(f"✅ Found CSRF token in input: {token[:20]}...")
                return token
            
            # Look for CSRF token in form
            csrf_form = soup.find('input', {'name': 'csrf_token'})
            if csrf_form:
                token = csrf_form.get('value')
                print(f"✅ Found CSRF token in form: {token[:20]}...")
                return token
            
            # Debug: Look for login form fields
            print("🔍 Debug: Looking for login form fields...")
            forms = soup.find_all('form')
            for i, form in enumerate(forms):
                print(f"   Form {i}: action={form.get('action')}")
                inputs = form.find_all('input')
                for inp in inputs:
                    print(f"     Input: name={inp.get('name')}, type={inp.get('type')}, value={inp.get('value', '')[:20]}...")
                
            print("⚠️ No CSRF token found, proceeding without it")
            return None
            
        except Exception as e:
            print(f"⚠️ Error getting CSRF token: {e}")
            return None
    
    def login(self, username, password):
        """Perform login to SINTA using requests"""
        try:
            session_config = config.get_session_config()
            login_page_url = session_config['login_url']
            
            print("🌐 Accessing SINTA login page...")
            
            # Get CSRF token and find correct form action
            response = self.session.get(login_page_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find login form and its action URL
            login_form = soup.find('form')
            if login_form:
                form_action = login_form.get('action')
                if form_action:
                    if form_action.startswith('http'):
                        login_url = form_action
                    else:
                        login_url = f"https://sinta.kemdikbud.go.id{form_action}"
                else:
                    login_url = login_page_url
            else:
                login_url = login_page_url
            
            # Get CSRF token (simplified version)
            csrf_token = self.get_csrf_token_simple(login_page_url)
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data['_token'] = csrf_token
                self.session.headers['X-CSRF-TOKEN'] = csrf_token
            
            print("📝 Submitting login credentials...")
            
            # Update headers for POST request
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://sinta.kemdikbud.go.id',
                'Referer': login_page_url
            })
            
            # Submit login form
            response = self.session.post(login_url, data=login_data, timeout=30, allow_redirects=True)
            
            # Check if login was successful
            if response.status_code == 200:
                # Check if we're redirected to dashboard or authors page
                if 'authors' in response.url or 'dashboard' in response.url or 'profile' in response.url:
                    print("✅ Login successful!")
                    return True
                elif 'login' in response.url:
                    print("❌ Login failed - redirected back to login page")
                    # Try to find error message
                    soup = BeautifulSoup(response.content, 'html.parser')
                    error_msg = soup.find('div', {'class': 'alert-danger'})
                    if error_msg:
                        print(f"   Error: {error_msg.get_text().strip()}")
                    return False
                else:
                    print("✅ Login successful!")
                    return True
            else:
                print(f"❌ Login failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_csrf_token_simple(self, login_url):
        """Get CSRF token from login page (simplified)"""
        try:
            response = self.session.get(login_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for CSRF token in meta tags
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta:
                return csrf_meta.get('content')
            
            # Look for CSRF token in input fields
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                return csrf_input.get('value')
            
            return None
            
        except Exception as e:
            return None
    
    def get_session_data(self):
        """Extract cookies and session data"""
        try:
            cookies_dict = dict(self.session.cookies)
            return {
                'cookies': cookies_dict,
                'headers': dict(self.session.headers)
            }
        except Exception as e:
            print(f"❌ Error getting session data: {e}")
            return None
    
    def test_session(self):
        """Test if current session is valid"""
        try:
            session_config = config.get_session_config()
            test_url = session_config['test_url']
            
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                # Check if we're not redirected to login
                if 'login' not in response.url:
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"❌ Session test failed: {e}")
            return False


class Utils:
    """Utility functions for the scraping application"""
    
    @staticmethod
    def get_output_dir():
        """Get output directory name with current date"""
        today = datetime.now()
        
        # Get date format from config with type safety
        date_format_val = config.get('output.date_format', '%d%m%Y')
        date_format = str(date_format_val) if date_format_val is not None else '%d%m%Y'
        date_str = today.strftime(date_format)
        
        # Get directory format from config with type safety
        directory_format_val = config.get('output.directory_format', 'output-{date}')
        directory_format = str(directory_format_val) if directory_format_val is not None else 'output-{date}'
        return directory_format.format(date=date_str)
    
    @staticmethod
    def ensure_output_dir():
        """Create output directory if it doesn't exist"""
        output_dir = Utils.get_output_dir()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        else:
            print(f"📁 Using existing output directory: {output_dir}")
        return output_dir
    
    @staticmethod
    def get_output_file(filename_base):
        """Get full output file path"""
        output_dir = Utils.get_output_dir()
        filename = f"{filename_base}.csv"
        return os.path.join(output_dir, filename)
    
    @staticmethod
    def get_author_name(session, author_id):
        """Get real author name from SINTA profile"""
        try:
            url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
            response = session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Extract name from profile
            profile_section = soup.find('div', class_='col-lg col-md')
            if profile_section:
                name_element = profile_section.find('h3').find('a')
                if name_element:
                    return name_element.text.strip()
            
            return f"Author_{author_id}"
        except Exception as e:
            print(f"   ⚠️ Error getting author name for ID {author_id}: {e}")
            return f"Author_{author_id}"


class SessionManager:
    """Manage SINTA session (login and cookies)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.cookies = {}
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': config.get_user_agent()
        }
        self.session.headers.update(self.headers)
    
    def initialize_session(self, force_new_login=False):
        """Initialize SINTA session using request-based login"""
        try:
            print("🚀 Initializing SINTA session with request-based login...")
            
            # Load environment variables
            load_dotenv()
            
            username = os.getenv('SINTA_USERNAME')
            password = os.getenv('SINTA_PASSWORD')
            
            if not username or not password:
                print("❌ SINTA credentials not found in .env file")
                print("💡 Create .env file with SINTA_USERNAME and SINTA_PASSWORD")
                return False
            
            # Get session config
            session_config = config.get_session_config()
            session_file = session_config['session_file']
            
            # Delete saved session if force new login
            if force_new_login and os.path.exists(session_file):
                os.remove(session_file)
                print("🗑️ Removed old session data")
            
            # Try to load existing session first
            if os.path.exists(session_file) and not force_new_login:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    self.cookies = session_data['cookies']
                    self.session.cookies.update(self.cookies)
                    
                    # Test if session is still valid
                    if self.test_session():
                        print("✅ Using existing valid session")
                        return True
                    else:
                        print("⚠️ Existing session expired, creating new session...")
                except Exception as e:
                    print(f"⚠️ Error loading existing session: {e}")
            
            # Perform request-based login
            login_handler = SintaRequestLogin()
            if login_handler.login(username, password):
                session_data = login_handler.get_session_data()
                
                if session_data:
                    self.cookies = session_data['cookies']
                    self.session.cookies.update(self.cookies)
                    
                    # Save session data
                    os.makedirs(os.path.dirname(session_file), exist_ok=True)
                    with open(session_file, 'w') as f:
                        json.dump(session_data, f)
                    print("💾 Session data saved")
                    
                    print("✅ Session initialized successfully")
                    return True
                else:
                    print("❌ Failed to get session data")
                    return False
            else:
                print("❌ Failed to login")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {e}")
            return False
    
    def test_session(self):
        """Test if current session is valid"""
        try:
            print("🧪 Testing session validity...")
            
            # Get test URL from config
            session_config = config.get_session_config()
            test_url = session_config['test_url']
            
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                # Check if we're not redirected to login
                if 'login' not in response.url:
                    print("✅ Session is valid")
                    return True
                else:
                    print("❌ Session invalid - redirected to login")
                    return False
            else:
                print(f"❌ Session invalid: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session test failed: {e}")
            return False


class LecturerManager:
    """Manage lecturer data from TXT file"""
    
    def __init__(self, config_file="dosen.txt"):
        self.config_file = config_file
        self.lecturers = []
    
    def load_lecturers(self):
        """Load lecturers from TXT file (one ID per line)"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.lecturers = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        try:
                            lecturer_id = int(line)
                            # Store only ID, name will be fetched when needed
                            self.lecturers.append((lecturer_id, None))
                        except ValueError:
                            print(f"⚠️ Skipping invalid ID: {line}")
                            continue
            print(f"✅ Loaded {len(self.lecturers)} lecturers from {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Error loading lecturers from {self.config_file}: {e}")
            return False
    
    def get_lecturers(self):
        """Get list of lecturers"""
        return self.lecturers


class BookScraper:
    """Scraper for book data"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_books(self, author_id, author_name):
        """Scrape book data for a specific author"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?page=1&view=books"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check pagination
        pagination_elem = soup.find(class_='pagination-text')
        if pagination_elem:
            total_pages = int(pagination_elem.text.split('of')[-1].strip().split()[0])
        else:
            total_pages = 1

        all_results = []

        for page in range(1, total_pages + 1):
            print(f"   📖 Processing page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=books"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    title = item.find('div', class_='ar-title').text.strip()
                    category = item.find('a', string=lambda text: 'Category' in text).text.split(':')[-1].strip()

                    # Extract authors
                    authors = []
                    ar_meta_divs = item.find_all('div', class_='ar-meta')
                    for meta_div in ar_meta_divs:
                        for author_link in meta_div.find_all('a', href="#!"):
                            if not author_link.has_attr('class'):
                                authors.append(author_link.text.strip())
                    authors = ", ".join(authors)

                    # Clean up authors
                    if ',' in authors:
                        authors = authors.split(',', 1)[1].strip()

                    publisher = item.find('a', class_='ar-pub').text.strip()
                    year = item.find('a', class_='ar-year').text.strip()
                    city = item.find('a', class_='ar-cited').text.strip()
                    isbn = item.find('a', class_='ar-quartile').text.split(':')[-1].strip()

                    all_results.append({
                        "Judul Buku": title,
                        "Kategori Buku": category,
                        "Penulis": authors,
                        "Penerbit": publisher,
                        "Tahun": year,
                        "Kota": city,
                        "ISBN": isbn,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing book item: {e}")
                    continue

        return all_results
    
    def save_to_csv(self, data, filename):
        """Save book data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ["Judul Buku", "Kategori Buku", "Penulis", "Penerbit", "Tahun", "Kota", "ISBN", "ID Sinta", "Nama Sinta"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                row["Penulis"] = str(row["Penulis"])
                writer.writerow(row)


class HakiScraper:
    """Scraper for HAKI (Intellectual Property Rights) data"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_haki(self, author_id, author_name):
        """Scrape HAKI data for a specific author"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?view=iprs"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check pagination
        pagination_elem = soup.find(class_='pagination-text')
        if pagination_elem:
            total_pages = int(pagination_elem.text.split('of')[-1].strip().split()[0])
        else:
            total_pages = 1

        all_results = []

        for page in range(1, total_pages + 1):
            print(f"   🏛️ Processing page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=iprs"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    title = item.find('div', class_='ar-title').text.strip()
                    inventor = item.find('a', string=lambda text: 'Inventor :' in text).text.split(':')[-1].strip()
                    year = item.find('a', class_='ar-year').text.strip()
                    application_number = item.find('a', class_='ar-cited').text.split(':')[-1].strip()
                    haki_type = item.find('a', class_='ar-quartile').text.strip()

                    all_results.append({
                        "Judul HAKI": title,
                        "Penemu": inventor,
                        "Jenis HAKI": haki_type,
                        "Nomor HAKI": application_number,
                        "Tahun": year,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing HAKI item: {e}")
                    continue

        return all_results
    
    def save_to_csv(self, data, filename):
        """Save HAKI data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ["Judul HAKI", "Penemu", "Jenis HAKI", "Nomor HAKI", "Tahun", "ID Sinta", "Nama Sinta"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


class PublicationScraper:
    """Scraper for publication data (Scopus, Google Scholar, Web of Science)"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_scopus(self, author_id, author_name):
        """Scrape Scopus publications"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?page=1&view=scopus"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        pagination_elem = soup.find(class_='pagination-text')
        all_results = []

        if pagination_elem:
            pagination_text = pagination_elem.text.strip()
            page_info = pagination_text.split('|')[0].strip()
            total_pages = int(page_info.split()[-1])
        else:
            total_pages = 1

        print(f"   📚 Scopus Total Pages: {total_pages}")

        for page in range(1, total_pages + 1):
            print(f"   📚 Processing Scopus page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=scopus"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    judul = item.find(class_='ar-title').text.strip()
                    link = item.find(class_='ar-pub')['href']
                    journal = item.find(class_='ar-pub').text.strip()
                    quartile = item.find(class_='ar-quartile').text.strip()
                    creator_elem = item.find('a', string=lambda text: text and 'Creator :' in text)
                    penulis = creator_elem.parent.text.split(':')[-1].strip() if creator_elem else None
                    tahun = item.find(class_='ar-year').text.strip().split()[-1]
                    sitasi = item.find(class_='ar-cited').text.strip()

                    all_results.append({
                        "Judul Artikel": judul,
                        "Nama Jurnal": journal,
                        "Quartile": quartile,
                        "Penulis": penulis,
                        "Tahun": tahun,
                        "Sitasi": sitasi,
                        "Link": link,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing Scopus item: {e}")
                    continue

        return all_results
    
    def scrape_google_scholar(self, author_id, author_name):
        """Scrape Google Scholar publications"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?page=1&view=googlescholar"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        pagination_elem = soup.find(class_='pagination-text')
        all_results = []

        if pagination_elem:
            pagination_text = pagination_elem.text.strip()
            page_info = pagination_text.split('|')[0].strip()
            total_pages = int(page_info.split()[-1])
        else:
            total_pages = 1

        print(f"   🎓 Google Scholar Total Pages: {total_pages}")

        for page in range(1, total_pages + 1):
            print(f"   🎓 Processing Google Scholar page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=googlescholar"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    judul = item.find('div', class_='ar-title').text.strip()
                    link = item.find('div', class_='ar-title').a['href']
                    jurnal = item.find('div', class_='ar-meta').find('a', class_='ar-pub').text
                    penulis = item.find('a', string=re.compile(r'Authors')).text.split(':')[-1].strip()
                    tahun = item.find('a', class_='ar-year').text.strip().split()[-1]
                    sitasi = item.find('a', class_='ar-cited').text.strip().split()[0]

                    all_results.append({
                        "Judul Artikel": judul,
                        "Nama Jurnal": jurnal,
                        "Penulis": penulis,
                        "Tahun": tahun,
                        "Sitasi": sitasi,
                        "Link": link,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing Google Scholar item: {e}")
                    continue

        return all_results
    
    def scrape_wos(self, author_id, author_name):
        """Scrape Web of Science publications"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?page=1&view=wos"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")
        pagination_elem = soup.find(class_='pagination-text')
        all_results = []

        if pagination_elem:
            pagination_text = pagination_elem.text.strip()
            page_info = pagination_text.split('|')[0].strip()
            total_pages = int(page_info.split()[-1])
        else:
            total_pages = 1

        print(f"   🔬 Web of Science Total Pages: {total_pages}")

        for page in range(1, total_pages + 1):
            print(f"   🔬 Processing Web of Science page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=wos"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    link = item.find('div', class_='ar-title').a['href']
                    judul = item.find('div', class_='ar-title').text.strip()
                    quartile_elem = item.find('a', class_='ar-quartile')
                    quartile = quartile_elem.text.strip() if quartile_elem else "N/A"
                    edisi = item.find('a', class_='ar-pub').text.strip()
                    jurnal = item.find('div', class_='ar-meta').find_all('a', class_='ar-pub')[-1].text.strip()
                    link_jurnal = item.find('div', class_='ar-meta').find_all('a', class_='ar-pub')[-1]['href']
                    urutan_penulis, total_penulis = map(int, re.findall(r'\d+', item.find('a', string=re.compile(r'Author Order')).text))
                    author_tag = item.find('div', class_='ar-meta').find_all('a')
                    penulis = None
                    for tag in author_tag:
                        if re.search(r'Authors\s*:', tag.text):
                            penulis = tag.text.split(':')[-1].strip()
                            break
                    tahun = item.find('a', class_='ar-year').text.strip().split()[-1]
                    sitasi = item.find('a', class_='ar-cited').text.strip().split()[-2]
                    terindex_scopus = "Yes" if item.find('span', class_='scopus-indexed') else "No"
                    doi_tag = item.find('a', class_='ar-sinta')
                    doi = doi_tag.text.strip().split(':')[-1] if doi_tag else "N/A"

                    all_results.append({
                        "Judul Artikel": judul,
                        "Nama Jurnal": jurnal,
                        "Quartile": quartile,
                        "Edition": edisi,
                        "Link Jurnal": link_jurnal,
                        "Penulis": penulis,
                        "Urutan Penulis": urutan_penulis,
                        "Total Penulis": total_penulis,
                        "Tahun": tahun,
                        "Sitasi": sitasi,
                        "Terindex Scopus": terindex_scopus,
                        "DOI": doi,
                        "Link": link,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing WoS item: {e}")
                    continue

        return all_results
    
    def save_to_csv(self, data, filename, publication_type):
        """Save publication data to CSV"""
        fieldnames = {
            "scopus": ["Judul Artikel", "Nama Jurnal", "Quartile", "Penulis", "Tahun", "Sitasi", "Link", "ID Sinta", "Nama Sinta"],
            "gs": ["Judul Artikel", "Nama Jurnal", "Penulis", "Tahun", "Sitasi", "Link", "ID Sinta", "Nama Sinta"],
            "wos": ["Judul Artikel", "Nama Jurnal", "Quartile", "Edition", "Link Jurnal", "Penulis", "Urutan Penulis", "Total Penulis", "Tahun", "Sitasi", "Terindex Scopus", "DOI", "Link", "ID Sinta", "Nama Sinta"]
        }
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames[publication_type])
            writer.writeheader()
            writer.writerows(data)


class ResearchScraper:
    """Scraper for research data"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_research(self, author_id, author_name):
        """Scrape research data for a specific author"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?page=1&view=researches"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check pagination
        pagination_elem = soup.find(class_='pagination-text')
        if pagination_elem:
            total_pages = int(pagination_elem.text.split('of')[-1].strip().split()[0])
        else:
            total_pages = 1

        all_results = []

        for page in range(1, total_pages + 1):
            print(f"   🔬 Processing page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=researches"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    def clean_text(text):
                        return re.sub(r"[\n\r]+", " ", text.strip())

                    title = clean_text(item.find('div', class_='ar-title').text)
                    leader = clean_text(item.find('a', string=lambda text: 'Leader :' in text).text.split(':')[-1])
                    funding_info = clean_text(item.find('a', class_='ar-pub').text)
                    personnel = [clean_text(p.text) for p in item.find_all('a', href=lambda href: href and '/authors/profile/' in href)]
                    year = clean_text(item.find('a', class_='ar-year').text)
                    funding = clean_text(item.find_all('a', class_='ar-quartile')[0].text)
                    status = clean_text(item.find_all('a', class_='ar-quartile')[1].text)
                    source = clean_text(item.find_all('a', class_='ar-quartile')[2].text)

                    all_results.append({
                        "Judul Penelitian": title,
                        "Ketua Penelitian": leader,
                        "Sumber Dana": funding_info,
                        "Anggota Penelitian": "; ".join(personnel),
                        "Tahun": year,
                        "Besar Dana": funding,
                        "Status": status,
                        "Sumber": source,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing research item: {e}")
                    continue

        return all_results
    
    def save_to_csv(self, data, filename):
        """Save research data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ["Judul Penelitian", "Ketua Penelitian", "Sumber Dana", "Anggota Penelitian", "Tahun", "Besar Dana", "Status", "Sumber", "ID Sinta", "Nama Sinta"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


class CommunityServiceScraper:
    """Scraper for community service (PPM) data"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_services(self, author_id, author_name):
        """Scrape community service data for a specific author"""
        base_url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        url = f"{base_url}?view=services"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")

        # Check pagination
        pagination_elem = soup.find(class_='pagination-text')
        if pagination_elem:
            total_pages = int(pagination_elem.text.split('of')[-1].strip().split()[0])
        else:
            total_pages = 1

        all_results = []

        for page in range(1, total_pages + 1):
            print(f"   🤝 Processing page {page} of {total_pages}")
            url = f"{base_url}?page={page}&view=services"
            response = self.session.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all(class_='ar-list-item')

            for item in items:
                try:
                    title = item.find('div', class_='ar-title').text.strip().replace('\"', '"').replace('\n', ' ')
                    leader = item.find('a', string=lambda text: 'Leader :' in text).text.split(':')[-1].strip()
                    skim = item.find('a', class_='ar-pub').text.strip()
                    personnel = [p.text.strip() for p in item.find_all('a', href=lambda href: href and '/authors/profile/' in href)]
                    year = item.find('a', class_='ar-year').text.strip()
                    funding = item.find_all('a', class_='ar-quartile')[0].text.strip()
                    status = item.find_all('a', class_='ar-quartile')[1].text.strip()
                    source = item.find_all('a', class_='ar-quartile')[2].text.strip()

                    all_results.append({
                        "Judul PPM": re.sub(r'\s+', ' ', title),
                        "Ketua PPM": leader,
                        "Skim PPM": skim,
                        "Anggota PPM": "; ".join(personnel),
                        "Tahun": year,
                        "Besar Dana": funding,
                        "Status": status,
                        "Sumber": source,
                        "ID Sinta": author_id,
                        "Nama Sinta": author_name
                    })
                except Exception as e:
                    print(f"   ⚠️ Error processing community service item: {e}")
                    continue

        return all_results
    
    def save_to_csv(self, data, filename):
        """Save community service data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ["Judul PPM", "Ketua PPM", "Skim PPM", "Anggota PPM", "Tahun", "Besar Dana", "Status", "Sumber", "ID Sinta", "Nama Sinta"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                cleaned_row = {}
                for key, value in row.items():
                    if isinstance(value, str):
                        cleaned_row[key] = value.replace('\n', ' ').replace('\"', '\"')
                    else:
                        cleaned_row[key] = value
                writer.writerow(cleaned_row)


class ProfileScraper:
    """Scraper for profile data"""
    
    def __init__(self, session_manager):
        self.session = session_manager
    
    def scrape_profile(self, author_id, author_name):
        """Scrape profile data for a specific author"""
        url = f"https://sinta.kemdikbud.go.id/authors/profile/{author_id}"
        response = self.session.session.get(url, timeout=30)
        soup = BeautifulSoup(response.content, "html.parser")

        try:
            # Extract profile information
            profile_section = soup.find('div', class_='col-lg col-md')
            
            # Extract name
            name_element = profile_section.find('h3').find('a')
            real_name = name_element.text.strip() if name_element else author_name
            
            # Extract university
            university_element = profile_section.find('a', href=lambda x: x and 'affiliations/profile' in x)
            university = university_element.text.strip().replace('Universitas ', '') if university_element else "N/A"
            
            # Extract study program
            prodi_element = profile_section.find('a', href=lambda x: x and 'departments/profile' in x)
            prodi = prodi_element.text.strip() if prodi_element else "N/A"
            
            # Extract SINTA Scores
            sinta_score_overall = "N/A"
            sinta_score_3yr = "N/A"
            
            # Find SINTA Score sections - look for the specific score pattern
            score_rows = soup.find_all('div', class_='row no-gutters')
            for row in score_rows:
                # Look for pr-txt elements containing score text
                pr_txt_elements = row.find_all('div', class_='pr-txt')
                pr_num_elements = row.find_all('div', class_='pr-num')
                
                for i, pr_txt in enumerate(pr_txt_elements):
                    text_content = pr_txt.text.strip()
                    if 'SINTA Score Overall' in text_content:
                        # Find corresponding pr-num element
                        if i < len(pr_num_elements):
                            sinta_score_overall = pr_num_elements[i].text.strip()
                    elif 'SINTA Score 3Yr' in text_content:
                        # Find corresponding pr-num element
                        if i < len(pr_num_elements):
                            sinta_score_3yr = pr_num_elements[i].text.strip()
            
            # Alternative method if first method fails
            if sinta_score_overall == "N/A" or sinta_score_3yr == "N/A":
                # Try to find by pattern matching
                all_pr_divs = soup.find_all('div', class_='pr-txt')
                for pr_div in all_pr_divs:
                    if 'SINTA Score Overall' in pr_div.text:
                        # Get the sibling pr-num div
                        parent = pr_div.parent
                        pr_num = parent.find('div', class_='pr-num')
                        if pr_num and sinta_score_overall == "N/A":
                            sinta_score_overall = pr_num.text.strip()
                    elif 'SINTA Score 3Yr' in pr_div.text:
                        # Get the sibling pr-num div  
                        parent = pr_div.parent
                        pr_num = parent.find('div', class_='pr-num')
                        if pr_num and sinta_score_3yr == "N/A":
                            sinta_score_3yr = pr_num.text.strip()
            
            # Extract statistics table
            table = soup.find('table', class_='stat-table')
            rows = table.find_all('tr')

            data = {
                "Nama Sinta": real_name,
                "ID Sinta": author_id,
                "Universitas": university,
                "Program Studi": prodi,
                "SINTA Score Overall": sinta_score_overall,
                "SINTA Score 3Yr": sinta_score_3yr
            }

            metrics = ["Article", "Citation", "Cited Document", "H-Index", "i10-Index", "G-Index"]
            sources = ["Scopus", "GScholar"]

            for i, metric in enumerate(metrics):
                for j, source in enumerate(sources):
                    value = rows[i + 1].find_all('td')[j + 1].text.strip()
                    data[f"{source} {metric}"] = value

            return data
        except Exception as e:
            print(f"   ⚠️ Error processing profile for {author_name}: {e}")
            return {
                "Nama Sinta": author_name,
                "ID Sinta": author_id,
                "Universitas": "N/A",
                "Program Studi": "N/A",
                "SINTA Score Overall": "N/A",
                "SINTA Score 3Yr": "N/A",
                "Scopus Article": "N/A",
                "Scopus Citation": "N/A",
                "Scopus Cited Document": "N/A",
                "Scopus H-Index": "N/A",
                "Scopus i10-Index": "N/A",
                "Scopus G-Index": "N/A",
                "GScholar Article": "N/A",
                "GScholar Citation": "N/A",
                "GScholar Cited Document": "N/A",
                "GScholar H-Index": "N/A",
                "GScholar i10-Index": "N/A",
                "GScholar G-Index": "N/A"
            }
    
    def save_to_csv(self, data, filename):
        """Save profile data to CSV"""
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ["Nama Sinta", "ID Sinta", "Universitas", "Program Studi", "SINTA Score Overall", "SINTA Score 3Yr", "Scopus Article", "Scopus Citation", "Scopus Cited Document", "Scopus H-Index", "Scopus i10-Index", "Scopus G-Index", "GScholar Article", "GScholar Citation", "GScholar Cited Document", "GScholar H-Index", "GScholar i10-Index", "GScholar G-Index"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


class SintaScrapingApp:
    """Main application class for SINTA scraping"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.lecturer_manager = LecturerManager()
        self.scrapers = {
            'buku': BookScraper(self.session_manager),
            'haki': HakiScraper(self.session_manager),
            'publikasi': PublicationScraper(self.session_manager),
            'penelitian': ResearchScraper(self.session_manager),
            'ppm': CommunityServiceScraper(self.session_manager),
            'profil': ProfileScraper(self.session_manager)
        }
    
    def initialize(self):
        """Initialize the application"""
        print("🚀 SINTA Scraping Application - CLI Version")
        print("=" * 50)
        
        # Load lecturers
        if not self.lecturer_manager.load_lecturers():
            return False
        
        # Initialize session
        if not self.session_manager.initialize_session():
            return False
        
        # Ensure output directory exists
        Utils.ensure_output_dir()
        
        return True
    
    def scrape_buku(self):
        """Scrape book data for all lecturers"""
        print("\n📖 Scraping Book Data...")
        print("-" * 30)
        
        scraper = self.scrapers['buku']
        all_results = []
        
        for author_id, _ in self.lecturer_manager.get_lecturers():
            # Get real author name
            author_name = Utils.get_author_name(self.session_manager.session, author_id)
            print(f"👤 Processing: {author_name} (ID: {author_id})")
            results = scraper.scrape_books(author_id, author_name)
            all_results.extend(results)
            print(f"   ✅ Found {len(results)} books")
        
        # Save to CSV
        csv_filename = Utils.get_output_file("buku")
        scraper.save_to_csv(all_results, csv_filename)
        print(f"💾 Saved {len(all_results)} book records to {csv_filename}")
    
    def scrape_haki(self):
        """Scrape HAKI data for all lecturers"""
        print("\n🏛️ Scraping HAKI Data...")
        print("-" * 30)
        
        scraper = self.scrapers['haki']
        all_results = []
        
        for author_id, _ in self.lecturer_manager.get_lecturers():
            # Get real author name
            author_name = Utils.get_author_name(self.session_manager.session, author_id)
            print(f"👤 Processing: {author_name} (ID: {author_id})")
            results = scraper.scrape_haki(author_id, author_name)
            all_results.extend(results)
            print(f"   ✅ Found {len(results)} HAKI records")
        
        # Save to CSV
        csv_filename = Utils.get_output_file("haki")
        scraper.save_to_csv(all_results, csv_filename)
        print(f"💾 Saved {len(all_results)} HAKI records to {csv_filename}")
    
    def scrape_publikasi(self, publication_types=None):
        """Scrape publication data for all lecturers"""
        if publication_types is None:
            publication_types = ['scopus', 'gs', 'wos']
        
        print(f"\n📚 Scraping Publication Data: {', '.join(publication_types)}")
        print("-" * 50)
        
        scraper = self.scrapers['publikasi']
        
        for pub_type in publication_types:
            print(f"\n📊 Processing {pub_type.upper()} publications...")
            all_results = []
            
            for author_id, _ in self.lecturer_manager.get_lecturers():
                # Get real author name
                author_name = Utils.get_author_name(self.session_manager.session, author_id)
                print(f"👤 Processing: {author_name} (ID: {author_id})")
                
                if pub_type == 'scopus':
                    results = scraper.scrape_scopus(author_id, author_name)
                elif pub_type == 'gs':
                    results = scraper.scrape_google_scholar(author_id, author_name)
                elif pub_type == 'wos':
                    results = scraper.scrape_wos(author_id, author_name)
                
                all_results.extend(results)
                print(f"   ✅ Found {len(results)} {pub_type.upper()} publications")
            
            # Save to CSV
            csv_filename = Utils.get_output_file(f"publikasi_{pub_type}")
            scraper.save_to_csv(all_results, csv_filename, pub_type)
            print(f"💾 Saved {len(all_results)} {pub_type.upper()} records to {csv_filename}")
    
    def scrape_penelitian(self):
        """Scrape research data for all lecturers"""
        print("\n🔬 Scraping Research Data...")
        print("-" * 30)
        
        scraper = self.scrapers['penelitian']
        all_results = []
        
        for author_id, _ in self.lecturer_manager.get_lecturers():
            # Get real author name
            author_name = Utils.get_author_name(self.session_manager.session, author_id)
            print(f"👤 Processing: {author_name} (ID: {author_id})")
            results = scraper.scrape_research(author_id, author_name)
            all_results.extend(results)
            print(f"   ✅ Found {len(results)} research records")
        
        # Save to CSV
        csv_filename = Utils.get_output_file("penelitian")
        scraper.save_to_csv(all_results, csv_filename)
        print(f"💾 Saved {len(all_results)} research records to {csv_filename}")
    
    def scrape_ppm(self):
        """Scrape community service data for all lecturers"""
        print("\n🤝 Scraping Community Service Data...")
        print("-" * 40)
        
        scraper = self.scrapers['ppm']
        all_results = []
        
        for author_id, _ in self.lecturer_manager.get_lecturers():
            # Get real author name
            author_name = Utils.get_author_name(self.session_manager.session, author_id)
            print(f"👤 Processing: {author_name} (ID: {author_id})")
            results = scraper.scrape_services(author_id, author_name)
            all_results.extend(results)
            print(f"   ✅ Found {len(results)} community service records")
        
        # Save to CSV
        csv_filename = Utils.get_output_file("ppm")
        scraper.save_to_csv(all_results, csv_filename)
        print(f"💾 Saved {len(all_results)} community service records to {csv_filename}")
    
    def scrape_profil(self):
        """Scrape profile data for all lecturers"""
        print("\n👤 Scraping Profile Data...")
        print("-" * 30)
        
        scraper = self.scrapers['profil']
        all_results = []
        
        for author_id, _ in self.lecturer_manager.get_lecturers():
            # Get real author name
            author_name = Utils.get_author_name(self.session_manager.session, author_id)
            print(f"👤 Processing: {author_name} (ID: {author_id})")
            result = scraper.scrape_profile(author_id, author_name)
            all_results.append(result)
            print(f"   ✅ Profile data collected")
        
        # Save to CSV
        csv_filename = Utils.get_output_file("profil")
        scraper.save_to_csv(all_results, csv_filename)
        print(f"💾 Saved {len(all_results)} profile records to {csv_filename}")
    
    def scrape_all(self):
        """Scrape all categories for all lecturers"""
        print("\n🎯 Scraping ALL Categories...")
        print("=" * 50)
        
        self.scrape_buku()
        self.scrape_haki()
        self.scrape_publikasi()
        self.scrape_penelitian()
        self.scrape_ppm()
        self.scrape_profil()
        
        print("\n✅ All scraping completed successfully!")
        print(f"📁 Results saved in: {Utils.get_output_dir()}")


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='SINTA Scraping Application - CLI Version - Scrape data dari SINTA untuk berbagai kategori',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main-cli.py                     # Scrape semua kategori
  python main-cli.py --buku              # Scrape hanya data buku
  python main-cli.py --haki              # Scrape hanya data HAKI
  python main-cli.py --publikasi         # Scrape semua publikasi
  python main-cli.py --publikasi-scopus  # Scrape hanya Scopus
  python main-cli.py --publikasi-gs      # Scrape hanya Google Scholar
  python main-cli.py --publikasi-wos     # Scrape hanya Web of Science
  python main-cli.py --penelitian        # Scrape hanya penelitian
  python main-cli.py --ppm               # Scrape hanya PPM
  python main-cli.py --profil            # Scrape hanya profil
        """
    )
    
    # Category arguments
    parser.add_argument('--buku', action='store_true', help='Scrape data buku')
    parser.add_argument('--haki', action='store_true', help='Scrape data HAKI')
    parser.add_argument('--publikasi', action='store_true', help='Scrape semua publikasi (Scopus, Google Scholar, WoS)')
    parser.add_argument('--publikasi-scopus', action='store_true', help='Scrape publikasi Scopus saja')
    parser.add_argument('--publikasi-gs', action='store_true', help='Scrape publikasi Google Scholar saja')
    parser.add_argument('--publikasi-wos', action='store_true', help='Scrape publikasi Web of Science saja')
    parser.add_argument('--penelitian', action='store_true', help='Scrape data penelitian')
    parser.add_argument('--ppm', action='store_true', help='Scrape data pengabdian masyarakat')
    parser.add_argument('--profil', action='store_true', help='Scrape data profil dosen')
    
    # Additional options
    parser.add_argument('--force-login', action='store_true', help='Force new login (ignore saved session)')
    parser.add_argument('--config', default='dosen.txt', help='Path to lecturer configuration file (default: dosen.txt)')
    
    return parser


def main():
    """Main application entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create the application instance
    app = SintaScrapingApp()
    
    # Set lecturer config file if specified
    if args.config != 'dosen.txt':
        app.lecturer_manager.config_file = args.config
    
    # Initialize the application
    if not app.initialize():
        print("❌ Failed to initialize application")
        sys.exit(1)
    
    # Force new login if requested
    if args.force_login:
        app.session_manager.initialize_session(force_new_login=True)
    
    # Determine what to scrape based on arguments
    scrape_something = False
    
    if args.buku:
        app.scrape_buku()
        scrape_something = True
    
    if args.haki:
        app.scrape_haki()
        scrape_something = True
    
    if args.publikasi:
        app.scrape_publikasi()
        scrape_something = True
    
    if args.publikasi_scopus:
        app.scrape_publikasi(['scopus'])
        scrape_something = True
    
    if args.publikasi_gs:
        app.scrape_publikasi(['gs'])
        scrape_something = True
    
    if args.publikasi_wos:
        app.scrape_publikasi(['wos'])
        scrape_something = True
    
    if args.penelitian:
        app.scrape_penelitian()
        scrape_something = True
    
    if args.ppm:
        app.scrape_ppm()
        scrape_something = True
    
    if args.profil:
        app.scrape_profil()
        scrape_something = True
    
    # If no specific category was specified, scrape all
    if not scrape_something:
        app.scrape_all()
    
    print("\n🎉 SINTA Scraping completed successfully!")
    print(f"📁 Check results in: {Utils.get_output_dir()}")


if __name__ == "__main__":
    main()
