#!/usr/bin/env python3
"""
SINTA Scraping Main Application

Aplikasi untuk melakukan scraping data dari SINTA (Sistem Informasi Riset Nasional).
Mendukung scraping berbagai kategori data: buku, HAKI, publikasi, penelitian, PPM, dan profil.

Usage:
    python main.py                      # Scrape semua kategori untuk semua dosen
    python main.py --buku               # Scrape hanya data buku
    python main.py --haki               # Scrape hanya data HAKI
    python main.py --publikasi          # Scrape semua jenis publikasi (Scopus, Google Scholar, WoS)
    python main.py --publikasi-scopus   # Scrape hanya publikasi Scopus
    python main.py --publikasi-gs       # Scrape hanya publikasi Google Scholar
    python main.py --publikasi-wos      # Scrape hanya publikasi Web of Science
    python main.py --penelitian         # Scrape hanya data penelitian
    python main.py --ppm                # Scrape hanya data pengabdian masyarakat
    python main.py --profil             # Scrape hanya data profil dosen

Author: Refactored from multiple modules
Date: July 2025
"""

import os
import sys
import time
import json
import argparse
import yaml
import csv
import re
from datetime import datetime
from pathlib import Path

# External libraries
import requests
from bs4 import BeautifulSoup

# Selenium imports for auto login
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from dotenv import load_dotenv
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


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
                    with open(config_path, 'r', encoding='utf-8') as file:
                        self.config = yaml.safe_load(file)
                    print(f"✅ Loaded configuration from {config_path}")
                    config_loaded = True
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
            'webdriver': {
                'chrome_driver_path': 'config/chromedriver',
                'headless': True,
                'timeout': 30,
                'page_load_timeout': 60,
                'implicit_wait': 10
            },
            'session': {
                'test_url': 'https://sinta.kemdikbud.go.id/authors',
                'login_url': 'https://sinta.kemdikbud.go.id/logins',
                'session_file': 'config/session_data.json'
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
                'config_file': 'config/dosen.yaml'
            },
            'logging': {
                'level': 'INFO',
                'show_emoji': True
            }
        }
    
    def get(self, key_path, default=None):
        """Get configuration value by dot notation (e.g., 'webdriver.edge_driver_path')"""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_chrome_driver_path(self) -> str:
        """Get ChromeDriver path from config"""
        path = self.get('webdriver.chrome_driver_path', 'config/chromedriver')
        return str(path) if path is not None else 'config/chromedriver'
    
    def get_webdriver_options(self) -> dict:
        """Get WebDriver options from config"""
        timeout_val = self.get('webdriver.timeout', 30)
        page_load_timeout_val = self.get('webdriver.page_load_timeout', 60)
        implicit_wait_val = self.get('webdriver.implicit_wait', 10)
        
        return {
            'headless': bool(self.get('webdriver.headless', True)),
            'timeout': int(timeout_val) if isinstance(timeout_val, (int, float, str)) else 30,
            'page_load_timeout': int(page_load_timeout_val) if isinstance(page_load_timeout_val, (int, float, str)) else 60,
            'implicit_wait': int(implicit_wait_val) if isinstance(implicit_wait_val, (int, float, str)) else 10
        }
    
    def get_session_config(self) -> dict:
        """Get session configuration"""
        return {
            'test_url': str(self.get('session.test_url', 'https://sinta.kemdikbud.go.id/authors')),
            'login_url': str(self.get('session.login_url', 'https://sinta.kemdikbud.go.id/logins')),
            'session_file': str(self.get('session.session_file', 'session_data.json'))
        }
    
    def get_user_agent(self) -> str:
        """Get User Agent from config"""
        user_agent = self.get('scraping.user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36')
        return str(user_agent) if user_agent is not None else 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'


# Global config instance
config = ConfigManager()


class SintaAutoLogin:
    """Auto login functionality for SINTA using Selenium"""
    
    def __init__(self, headless=None, timeout=None):
        # Use config values if not provided
        webdriver_options = config.get_webdriver_options()
        
        self.headless = headless if headless is not None else webdriver_options['headless']
        self.timeout = timeout if timeout is not None else webdriver_options['timeout']
        self.driver = None
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
    
    def setup_driver(self):
        """Setup Chrome WebDriver with options"""
        try:
            # Get ChromeDriver path and options from config
            CHROME_DRIVER_PATH = config.get_chrome_driver_path()
            webdriver_options = config.get_webdriver_options()
            
            if not os.path.exists(CHROME_DRIVER_PATH):
                print(f"❌ ChromeDriver not found at {CHROME_DRIVER_PATH}")
                print("💡 Update the path in config.yaml under webdriver.chrome_driver_path")
                print("📝 Or run the setup script to auto-download ChromeDriver")
                return False
            
            chrome_options = ChromeOptions()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'--user-agent={self.headers["User-Agent"]}')
            
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            })

            service = ChromeService(executable_path=CHROME_DRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Use timeouts from config
            self.driver.set_page_load_timeout(webdriver_options['page_load_timeout'])
            self.driver.implicitly_wait(webdriver_options['implicit_wait'])
            
            print("✅ Chrome WebDriver initialized successfully")
            print(f"📁 Using ChromeDriver from: {CHROME_DRIVER_PATH}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Chrome WebDriver: {e}")
            print("💡 Check the ChromeDriver path in config.yaml")
            return False
    
    def login(self, username, password):
        """Perform automatic login to SINTA"""
        try:
            # Get session config
            session_config = config.get_session_config()
            login_url = session_config['login_url']
            
            print("🌐 Navigating to SINTA login page...")
            
            max_retries_val = config.get('scraping.max_retries', 3)
            max_retries = int(max_retries_val) if isinstance(max_retries_val, (int, float, str)) else 3
            for attempt in range(max_retries):
                try:
                    print(f"   🔄 Attempt {attempt + 1}/{max_retries}")
                    self.driver.get(login_url)
                    print("   ✅ Page loaded successfully")
                    break
                except TimeoutException:
                    if attempt < max_retries - 1:
                        print(f"   ⚠️ Timeout on attempt {attempt + 1}, retrying...")
                        time.sleep(2)
                        continue
                    else:
                        print("   ❌ All page load attempts failed")
                        return False
            
            wait = WebDriverWait(self.driver, self.timeout)
            
            print("🔍 Looking for login form...")
            username_field = None
            selectors = [
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.ID, "username"),
                (By.ID, "email"),
                (By.CSS_SELECTOR, "input[name='username']"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.XPATH, "//input[@name='username' or @name='email']")
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    username_field = wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    print(f"   ✅ Found username field with {selector_type}={selector_value}")
                    break
                except TimeoutException:
                    continue
            
            if username_field is None:
                print("❌ Could not find username field")
                return False
            
            # Find password field
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Fill in credentials
            print("📝 Filling login credentials...")
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Find and click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            print("⏳ Waiting for login to complete...")
            time.sleep(5)
            
            # Check if login was successful
            if "authors" in self.driver.current_url or "dashboard" in self.driver.current_url:
                print("✅ Login successful!")
                return True
            else:
                print("❌ Login failed")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_session_data(self):
        """Extract cookies and session data"""
        try:
            cookies_dict = {}
            for cookie in self.driver.get_cookies():
                cookies_dict[cookie['name']] = cookie['value']
            
            return {
                'cookies': cookies_dict,
                'headers': self.headers
            }
        except Exception as e:
            print(f"❌ Error getting session data: {e}")
            return None
    
    def auto_login_flow(self):
        """Complete auto login flow"""
        try:
            # Load environment variables
            load_dotenv()
            
            username = os.getenv('SINTA_USERNAME')
            password = os.getenv('SINTA_PASSWORD')
            
            if not username or not password:
                print("❌ SINTA credentials not found in .env file")
                print("💡 Create .env file with SINTA_USERNAME and SINTA_PASSWORD")
                return None
            
            if not self.setup_driver():
                return None
            
            if not self.login(username, password):
                return None
            
            session_data = self.get_session_data()
            
            # Save session data
            if session_data:
                with open('session_data.json', 'w') as f:
                    json.dump(session_data, f)
                print("💾 Session data saved")
            
            return session_data
            
        except Exception as e:
            print(f"❌ Auto login flow error: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()


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


class SessionManager:
    """Manage SINTA session (login and cookies)"""
    
    def __init__(self):
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
    
    def initialize_session(self, force_new_login=False):
        """Initialize SINTA session using automatic login"""
        if not SELENIUM_AVAILABLE:
            print("❌ Auto login not available. Install selenium and python-dotenv.")
            return False
        
        try:
            print("🚀 Initializing SINTA session with auto login...")
            
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
                    self.headers = session_data['headers']
                    
                    # Test if session is still valid
                    if self.test_session():
                        print("✅ Using existing valid session")
                        return True
                    else:
                        print("⚠️ Existing session expired, creating new session...")
                except Exception as e:
                    print(f"⚠️ Error loading existing session: {e}")
            
            # Perform auto login
            webdriver_options = config.get_webdriver_options()
            auto_login = SintaAutoLogin(headless=webdriver_options['headless'])
            session_data = auto_login.auto_login_flow()
            
            if session_data:
                self.cookies = session_data['cookies']
                self.headers = session_data['headers']
                print("✅ Session initialized successfully")
                return True
            else:
                print("❌ Failed to initialize session with auto login")
                return False
                
        except Exception as e:
            print(f"❌ Error during auto login: {e}")
            return False
    
    def test_session(self):
        """Test if current session is valid"""
        try:
            print("🧪 Testing session validity...")
            
            # Get test URL from config
            session_config = config.get_session_config()
            test_url = session_config['test_url']
            
            response = requests.get(
                test_url,
                cookies=self.cookies,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Session is valid")
                return True
            else:
                print(f"❌ Session invalid: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session test failed: {e}")
            return False


class LecturerManager:
    """Manage lecturer data from YAML configuration"""
    
    def __init__(self, config_file="config/dosen.yaml"):
        self.config_file = config_file
        self.lecturers = []
    
    def load_lecturers(self):
        """Load lecturers from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                self.lecturers = [(lecturer['id'], lecturer['name']) for lecturer in data['lecturers']]
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
            response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
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
        response = requests.get(url, cookies=self.session.cookies, headers=self.session.headers)
        soup = BeautifulSoup(response.content, "html.parser")

        try:
            table = soup.find('table', class_='stat-table')
            rows = table.find_all('tr')

            data = {
                "Nama Sinta": author_name,
                "ID Sinta": author_id
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
            fieldnames = ["Nama Sinta", "ID Sinta", "Scopus Article", "Scopus Citation", "Scopus Cited Document", "Scopus H-Index", "Scopus i10-Index", "Scopus G-Index", "GScholar Article", "GScholar Citation", "GScholar Cited Document", "GScholar H-Index", "GScholar i10-Index", "GScholar G-Index"]
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
        print("🚀 SINTA Scraping Application")
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
        
        for author_id, author_name in self.lecturer_manager.get_lecturers():
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
        
        for author_id, author_name in self.lecturer_manager.get_lecturers():
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
            
            for author_id, author_name in self.lecturer_manager.get_lecturers():
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
            print(f"💾 Saved {len(all_results)} {pub_type.upper} records to {csv_filename}")
    
    def scrape_penelitian(self):
        """Scrape research data for all lecturers"""
        print("\n🔬 Scraping Research Data...")
        print("-" * 30)
        
        scraper = self.scrapers['penelitian']
        all_results = []
        
        for author_id, author_name in self.lecturer_manager.get_lecturers():
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
        
        for author_id, author_name in self.lecturer_manager.get_lecturers():
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
        
        for author_id, author_name in self.lecturer_manager.get_lecturers():
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
        description='SINTA Scraping Application - Scrape data dari SINTA untuk berbagai kategori',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     # Scrape semua kategori
  python main.py --buku              # Scrape hanya data buku
  python main.py --haki              # Scrape hanya data HAKI
  python main.py --publikasi         # Scrape semua publikasi
  python main.py --publikasi-scopus  # Scrape hanya Scopus
  python main.py --publikasi-gs      # Scrape hanya Google Scholar
  python main.py --publikasi-wos     # Scrape hanya Web of Science
  python main.py --penelitian        # Scrape hanya penelitian
  python main.py --ppm               # Scrape hanya PPM
  python main.py --profil            # Scrape hanya profil
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
    parser.add_argument('--config', default='dosen.yaml', help='Path to lecturer configuration file (default: dosen.yaml)')
    
    return parser


def main():
    """Main application entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Create the application instance
    app = SintaScrapingApp()
    
    # Set lecturer config file if specified
    if args.config != 'dosen.yaml':
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
