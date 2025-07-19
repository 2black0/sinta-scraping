#!/usr/bin/env python3
"""
SINTA Scraper Web Interface Launcher
Quick start script for the web interface
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Map package names to their import names
    required_packages = {
        'flask': 'flask',
        'requests': 'requests', 
        'beautifulsoup4': 'bs4',
        'python-dotenv': 'dotenv'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} (missing)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install'
            ] + missing_packages)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            print("   Please run: pip install flask requests beautifulsoup4 python-dotenv")
            sys.exit(1)

def check_env_file():
    """Check if .env file exists"""
    parent_dir = Path(__file__).parent.parent
    env_file = parent_dir / '.env'
    
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("   Creating sample .env file...")
        
        sample_env = """# SINTA Login Credentials
SINTA_USERNAME=your_email@example.com
SINTA_PASSWORD=your_password

# Note: Ganti dengan kredensial SINTA Anda yang sebenarnya
"""
        
        with open(env_file, 'w') as f:
            f.write(sample_env)
        
        print(f"   ✅ Sample .env file created at: {env_file}")
        print("   📝 Please edit .env with your actual SINTA credentials")
    else:
        print("✅ .env file found")

def check_dosen_file():
    """Check if dosen.txt file exists"""
    parent_dir = Path(__file__).parent.parent
    dosen_file = parent_dir / 'dosen.txt'
    
    if not dosen_file.exists():
        print("⚠️  Warning: dosen.txt file not found")
        print("   Creating sample dosen.txt file...")
        
        sample_dosen = """# Daftar ID SINTA Dosen
# Satu ID per baris
# ID SINTA dari URL profil: https://sinta.kemdikbud.go.id/authors/profile/ID

6726725
# 7654321
# 8765432
"""
        
        with open(dosen_file, 'w') as f:
            f.write(sample_dosen)
        
        print(f"   ✅ Sample dosen.txt file created at: {dosen_file}")
        print("   📝 Please edit dosen.txt with actual lecturer IDs")
    else:
        print("✅ dosen.txt file found")

def main():
    """Main launcher function"""
    print("🚀 SINTA Scraper Web Interface Launcher")
    print("=" * 50)
    
    # Check system requirements
    check_python_version()
    check_dependencies()
    check_env_file()
    check_dosen_file()
    
    print("\n🌐 Starting web interface...")
    print("=" * 50)
    
    # Change to web directory
    web_dir = Path(__file__).parent
    os.chdir(web_dir)
    
    # Start Flask app
    try:
        from app import app
        print("📂 Web interface files loaded successfully")
        print("🌍 Starting Flask development server...")
        print("🔗 Open your browser and go to: http://localhost:5000")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n\n👋 Web interface stopped")
    except ImportError as e:
        print(f"❌ Error importing Flask app: {e}")
        print("   Please check that all dependencies are installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
