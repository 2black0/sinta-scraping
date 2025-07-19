#!/usr/bin/env python3
"""
SINTA Scraper Web Interface
Simple launcher script from project root
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the web interface"""
    print("🚀 Starting SINTA Scraper Web Interface...")
    
    # Get the web directory path
    project_root = Path(__file__).parent
    web_dir = project_root / 'web'
    
    if not web_dir.exists():
        print("❌ Error: Web directory not found!")
        print(f"   Expected location: {web_dir}")
        sys.exit(1)
    
    # Run the web interface launcher
    launcher_script = web_dir / 'run.py'
    
    if not launcher_script.exists():
        print("❌ Error: Web launcher script not found!")
        print(f"   Expected location: {launcher_script}")
        sys.exit(1)
    
    try:
        subprocess.run([sys.executable, str(launcher_script)], cwd=web_dir)
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped")
    except Exception as e:
        print(f"❌ Error running web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
