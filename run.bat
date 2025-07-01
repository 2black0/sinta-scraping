@echo off
setlocal enabledelayedexpansion

:: SINTA Scraping Setup and Run Script for Windows
:: Automatically checks dependencies, downloads tools, and runs the scraping application

title SINTA Scraping Setup

:: Colors for output (Windows 10+ with ANSI support)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

:: Function equivalents using labels
goto :main

:print_status
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:print_header
echo.
echo %BLUE%=== %~1 ===%NC%
goto :eof

:detect_platform
call :print_status "Detected platform: Windows"
set OS=win

:: Detect architecture
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set ARCH=64
) else if "%PROCESSOR_ARCHITEW6432%"=="AMD64" (
    set ARCH=64
) else (
    set ARCH=32
)

call :print_status "Architecture: %ARCH%-bit"
goto :eof

:check_conda
call :print_header "Checking Conda Installation"

where conda >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('conda --version 2^>nul') do set conda_version=%%a
    call :print_success "Conda found: !conda_version!"
    goto :eof
) else (
    call :print_error "Conda is not installed or not in PATH"
    call :print_error "Please install Anaconda or Miniconda first:"
    call :print_error "- Anaconda: https://www.anaconda.com/products/distribution"
    call :print_error "- Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    call :print_error "After installation, restart your command prompt and run this script again."
    pause
    exit /b 1
)

:check_python
call :print_header "Checking Python Installation"

where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%a in ('python --version 2^>nul') do set python_version=%%a
    call :print_success "Python found: !python_version!"
    
    :: Check if version is >= 3.8
    python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        call :print_success "Python version is compatible (>= 3.8)"
    ) else (
        call :print_warning "Python version should be >= 3.8. Current: !python_version!"
    )
) else (
    call :print_error "Python not found. Please install Python 3.8 or higher."
    call :print_error "Download from: https://www.python.org/downloads/"
    pause
    exit /b 1
)
goto :eof

:check_pip_packages
call :print_header "Checking Python Packages"

if exist "requirements.txt" (
    call :print_status "Installing Python packages from requirements.txt"
    pip install -r requirements.txt
    if !errorlevel! equ 0 (
        call :print_success "Python packages installed/updated"
    ) else (
        call :print_error "Failed to install packages from requirements.txt"
        exit /b 1
    )
) else (
    call :print_warning "requirements.txt not found, installing essential packages"
    pip install selenium requests beautifulsoup4 pyyaml python-dotenv
    if !errorlevel! equ 0 (
        call :print_success "Essential packages installed"
    ) else (
        call :print_error "Failed to install essential packages"
        exit /b 1
    )
)
goto :eof

:download_chromedriver
call :print_header "Checking ChromeDriver"

:: Create config directory if it doesn't exist
if not exist "config" mkdir config

set CHROMEDRIVER_PATH=config\chromedriver.exe

:: Check if ChromeDriver already exists
if exist "%CHROMEDRIVER_PATH%" (
    call :print_success "ChromeDriver already exists at %CHROMEDRIVER_PATH%"
    goto :eof
)

call :print_status "ChromeDriver not found, downloading..."

:: Determine download URL based on architecture
if "%ARCH%"=="64" (
    set DOWNLOAD_URL=https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/win64/chromedriver-win64.zip
    set EXTRACT_FOLDER=chromedriver-win64
) else (
    set DOWNLOAD_URL=https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.92/win32/chromedriver-win32.zip
    set EXTRACT_FOLDER=chromedriver-win32
)

call :print_status "Downloading ChromeDriver from: %DOWNLOAD_URL%"

:: Download using PowerShell
powershell -Command "& {try { Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile 'config\chromedriver.zip' -UseBasicParsing } catch { exit 1 }}"
if !errorlevel! neq 0 (
    call :print_error "Failed to download ChromeDriver"
    exit /b 1
)

:: Extract ChromeDriver using PowerShell
call :print_status "Extracting ChromeDriver..."
powershell -Command "& {Expand-Archive -Path 'config\chromedriver.zip' -DestinationPath 'config\' -Force}"
if !errorlevel! neq 0 (
    call :print_error "Failed to extract ChromeDriver"
    exit /b 1
)

:: Move the executable to the correct location
move "config\%EXTRACT_FOLDER%\chromedriver.exe" "%CHROMEDRIVER_PATH%" >nul
rmdir /s /q "config\%EXTRACT_FOLDER%"
del "config\chromedriver.zip"

call :print_success "ChromeDriver downloaded and extracted to %CHROMEDRIVER_PATH%"
goto :eof

:check_env_file
call :print_header "Checking Environment Configuration"

if exist ".env" (
    call :print_success ".env file found"
    
    :: Check if required variables are set
    findstr "SINTA_USERNAME=" .env >nul 2>&1
    set username_found=!errorlevel!
    findstr "SINTA_PASSWORD=" .env >nul 2>&1
    set password_found=!errorlevel!
    
    if !username_found! equ 0 if !password_found! equ 0 (
        call :print_success "SINTA credentials configured in .env"
    ) else (
        call :print_warning "SINTA credentials not found in .env file"
        call :print_warning "Please add your SINTA credentials to .env:"
        echo SINTA_USERNAME=your_username_or_email
        echo SINTA_PASSWORD=your_password
    )
) else (
    call :print_warning ".env file not found"
    if exist ".env.example" (
        call :print_status "Copying .env.example to .env"
        copy ".env.example" ".env" >nul
        call :print_warning "Please edit .env file and add your SINTA credentials"
    ) else (
        call :print_status "Creating .env file template"
        (
            echo # SINTA Login Credentials
            echo SINTA_USERNAME=your_username_or_email
            echo SINTA_PASSWORD=your_password
        ) > .env
        call :print_warning "Please edit .env file and add your SINTA credentials"
    )
)
goto :eof

:check_website_status
call :print_header "Checking SINTA Website Status"

set SINTA_URL=https://sinta.kemdikbud.go.id/

call :print_status "Checking %SINTA_URL%"

:: Check website status using PowerShell
powershell -Command "& {try { $response = Invoke-WebRequest -Uri '%SINTA_URL%' -UseBasicParsing -TimeoutSec 10; exit $response.StatusCode } catch { exit 0 }}"
set HTTP_STATUS=!errorlevel!

if !HTTP_STATUS! equ 200 (
    call :print_success "SINTA website is accessible (HTTP !HTTP_STATUS!)"
) else (
    call :print_warning "SINTA website may be unreachable (HTTP !HTTP_STATUS!)"
    call :print_warning "You may encounter issues during scraping."
)
goto :eof

:main
call :print_header "SINTA Scraping Setup and Execution"
call :print_status "Starting automated setup..."

:: Detect platform
call :detect_platform

:: Check all requirements
call :check_conda
if !errorlevel! neq 0 exit /b 1

call :check_python
if !errorlevel! neq 0 exit /b 1

call :check_pip_packages
if !errorlevel! neq 0 exit /b 1

call :download_chromedriver
if !errorlevel! neq 0 exit /b 1

call :check_env_file

call :check_website_status

call :print_header "Running SINTA Scraping Application"
call :print_status "All checks completed successfully!"
call :print_status "Starting main.py..."

:: Run the main application
python main.py

if !errorlevel! equ 0 (
    call :print_success "Script execution completed!"
) else (
    call :print_error "Script execution failed with error code !errorlevel!"
)

pause
