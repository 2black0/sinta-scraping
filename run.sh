#!/bin/bash

# SINTA Scraping Setup and Run Script
# Automatically checks dependencies, downloads tools, and runs the scraping application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Detect OS and architecture
detect_platform() {
    OS="unknown"
    ARCH="unknown"
    
    case "$(uname -s)" in
        Darwin*)
            OS="mac"
            if [[ "$(uname -m)" == "arm64" ]]; then
                ARCH="arm64"
            else
                ARCH="x64"
            fi
            ;;
        Linux*)
            OS="linux"
            ARCH="64"
            ;;
        *)
            print_error "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
    
    print_status "Detected platform: $OS-$ARCH"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check conda installation
check_conda() {
    print_header "Checking Conda Installation"
    
    if command_exists conda; then
        conda_version=$(conda --version)
        print_success "Conda found: $conda_version"
        return 0
    else
        print_error "Conda is not installed or not in PATH"
        print_error "Please install Anaconda or Miniconda first:"
        print_error "- Anaconda: https://www.anaconda.com/products/distribution"
        print_error "- Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        print_error "After installation, restart your terminal and run this script again."
        exit 1
    fi
}

# Check Python version
check_python() {
    print_header "Checking Python Installation"
    
    if command_exists python; then
        python_version=$(python --version)
        print_success "Python found: $python_version"
        
        # Check if version is >= 3.8
        python_major=$(python -c "import sys; print(sys.version_info.major)")
        python_minor=$(python -c "import sys; print(sys.version_info.minor)")
        
        if [[ $python_major -eq 3 && $python_minor -ge 8 ]]; then
            print_success "Python version is compatible (>= 3.8)"
        else
            print_warning "Python version should be >= 3.8. Current: $python_version"
        fi
    else
        print_error "Python not found. Please install Python 3.8 or higher."
        exit 1
    fi
}

# Check and install pip packages
check_pip_packages() {
    print_header "Checking Python Packages"
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing Python packages from requirements.txt"
        pip install -r requirements.txt
        print_success "Python packages installed/updated"
    else
        print_warning "requirements.txt not found, installing essential packages"
        pip install selenium requests beautifulsoup4 pyyaml python-dotenv
        print_success "Essential packages installed"
    fi
}

# Download ChromeDriver
download_chromedriver() {
    print_header "Checking ChromeDriver"
    
    # Create config directory if it doesn't exist
    mkdir -p config
    
    CHROMEDRIVER_PATH="config/chromedriver"
    
    # Check if ChromeDriver already exists
    if [ -f "$CHROMEDRIVER_PATH" ]; then
        print_success "ChromeDriver already exists at $CHROMEDRIVER_PATH"
        chmod +x "$CHROMEDRIVER_PATH"
        return 0
    fi
    
    print_status "ChromeDriver not found, downloading..."
    
    # Determine download URL based on platform
    case "$OS-$ARCH" in
        "mac-arm64")
            DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/mac-arm64/chromedriver-mac-arm64.zip"
            ;;
        "mac-x64")
            DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/mac-x64/chromedriver-mac-x64.zip"
            ;;
        "linux-64")
            DOWNLOAD_URL="https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/linux64/chromedriver-linux64.zip"
            ;;
        *)
            print_error "Unsupported platform for automatic ChromeDriver download: $OS-$ARCH"
            print_error "Please download ChromeDriver manually from:"
            print_error "https://developer.chrome.com/docs/chromedriver/downloads"
            print_error "And place it at: $CHROMEDRIVER_PATH"
            exit 1
            ;;
    esac
    
    # Download ChromeDriver
    print_status "Downloading ChromeDriver from: $DOWNLOAD_URL"
    
    if command_exists curl; then
        curl -L -o "config/chromedriver.zip" "$DOWNLOAD_URL"
    elif command_exists wget; then
        wget -O "config/chromedriver.zip" "$DOWNLOAD_URL"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
    
    # Extract ChromeDriver
    print_status "Extracting ChromeDriver..."
    
    if command_exists unzip; then
        cd config
        unzip -q chromedriver.zip
        
        # Move the executable to the correct location
        case "$OS-$ARCH" in
            "mac-arm64")
                mv chromedriver-mac-arm64/chromedriver .
                rm -rf chromedriver-mac-arm64
                ;;
            "mac-x64")
                mv chromedriver-mac-x64/chromedriver .
                rm -rf chromedriver-mac-x64
                ;;
            "linux-64")
                mv chromedriver-linux64/chromedriver .
                rm -rf chromedriver-linux64
                ;;
        esac
        
        rm chromedriver.zip
        chmod +x chromedriver
        cd ..
        
        print_success "ChromeDriver downloaded and extracted to $CHROMEDRIVER_PATH"
    else
        print_error "unzip command not found. Please install unzip."
        exit 1
    fi
}

# Check .env file
check_env_file() {
    print_header "Checking Environment Configuration"
    
    if [ -f ".env" ]; then
        print_success ".env file found"
        
        # Check if required variables are set
        if grep -q "SINTA_USERNAME=" .env && grep -q "SINTA_PASSWORD=" .env; then
            print_success "SINTA credentials configured in .env"
        else
            print_warning "SINTA credentials not found in .env file"
            print_warning "Please add your SINTA credentials to .env:"
            echo "SINTA_USERNAME=your_username_or_email"
            echo "SINTA_PASSWORD=your_password"
        fi
    else
        print_warning ".env file not found"
        if [ -f ".env.example" ]; then
            print_status "Copying .env.example to .env"
            cp .env.example .env
            print_warning "Please edit .env file and add your SINTA credentials"
        else
            print_status "Creating .env file template"
            cat > .env << EOF
# SINTA Login Credentials
SINTA_USERNAME=your_username_or_email
SINTA_PASSWORD=your_password
EOF
            print_warning "Please edit .env file and add your SINTA credentials"
        fi
    fi
}

# Check website status
check_website_status() {
    print_header "Checking SINTA Website Status"
    
    SINTA_URL="https://sinta.kemdikbud.go.id/"
    
    print_status "Checking $SINTA_URL"
    
    if command_exists curl; then
        HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 "$SINTA_URL" || echo "000")
    elif command_exists wget; then
        HTTP_STATUS=$(wget --spider --server-response --timeout=10 "$SINTA_URL" 2>&1 | grep "HTTP/" | tail -1 | awk '{print $2}' || echo "000")
    else
        print_warning "Neither curl nor wget found. Skipping website status check."
        return 0
    fi
    
    if [[ "$HTTP_STATUS" == "200" ]]; then
        print_success "SINTA website is accessible (HTTP $HTTP_STATUS)"
    else
        print_warning "SINTA website may be unreachable (HTTP $HTTP_STATUS)"
        print_warning "You may encounter issues during scraping."
    fi
}

# Main execution
main() {
    print_header "SINTA Scraping Setup and Execution"
    print_status "Starting automated setup..."
    
    # Detect platform
    detect_platform
    
    # Check all requirements
    check_conda
    check_python
    check_pip_packages
    download_chromedriver
    check_env_file
    check_website_status
    
    print_header "Running SINTA Scraping Application"
    print_status "All checks completed successfully!"
    print_status "Starting main.py..."
    
    # Run the main application
    python main.py
    
    print_success "Script execution completed!"
}

# Run main function
main "$@"
