@echo off
REM Installation script for Serbian Questionnaire Scraper
REM Run this file to automatically install all Python dependencies

echo ============================================================
echo   Serbian Questionnaire Scraper - Installation Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [1/3] Checking Python installation...
python --version
echo.

echo [2/3] Installing Python dependencies from requirements.txt...
echo This may take a few minutes...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Try running: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying Tesseract-OCR installation...
echo.

tesseract --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Tesseract-OCR not found in PATH
    echo.
    echo You need to download and install Tesseract-OCR separately:
    echo.
    echo 1. Go to: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Download the Windows installer
    echo 3. Run the installer
    echo 4. Use the default installation path: C:\Program Files\Tesseract-OCR
    echo 5. After installation, verify: tesseract --version
    echo.
    echo.
    pause
) else (
    echo Tesseract-OCR found:
    tesseract --version
    echo.
)

echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Make sure Tesseract-OCR is installed (see above if needed)
echo 2. Run the application: python questionnaire_scraper.py
echo 3. See README.md for usage instructions
echo 4. Check SETUP_GUIDE.md if you encounter issues
echo.
echo ============================================================

pause
