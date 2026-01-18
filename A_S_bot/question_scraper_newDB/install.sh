#!/bin/bash

# Installation script for Serbian Questionnaire Scraper
# For Linux and macOS

echo "============================================================"
echo "  Serbian Questionnaire Scraper - Installation Script"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Install Python 3.8+ from:"
    echo "  Ubuntu/Debian: sudo apt-get install python3-pip"
    echo "  macOS: brew install python3"
    echo "  Or: https://www.python.org"
    exit 1
fi

echo "[1/4] Checking Python installation..."
python3 --version
echo ""

echo "[2/4] Installing Python dependencies..."
echo "This may take a few minutes..."
echo ""

pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Try running: pip3 install -r requirements.txt"
    exit 1
fi

echo ""
echo "[3/4] Installing Tesseract-OCR..."
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Detected: macOS"
    if ! command -v tesseract &> /dev/null; then
        echo "Installing Tesseract using Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "ERROR: Homebrew not installed"
            echo "Install from: https://brew.sh"
            exit 1
        fi
        brew install tesseract
    else
        echo "Tesseract already installed"
        tesseract --version
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "Detected: Linux"
    if ! command -v tesseract &> /dev/null; then
        echo "Installing Tesseract..."
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr libtesseract-dev
        elif command -v yum &> /dev/null; then
            # Red Hat/CentOS
            sudo yum install -y tesseract
        elif command -v pacman &> /dev/null; then
            # Arch
            sudo pacman -S tesseract
        else
            echo "Could not auto-detect package manager"
            echo "Please install tesseract manually:"
            echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
            echo "  CentOS: sudo yum install tesseract"
            echo "  Arch: sudo pacman -S tesseract"
        fi
    else
        echo "Tesseract already installed"
        tesseract --version
    fi
fi

echo ""
echo "[4/4] Verifying Tesseract installation..."
echo ""

if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract-OCR not found in PATH"
    echo ""
    echo "Please install Tesseract-OCR:"
    echo "  macOS: brew install tesseract"
    echo "  Ubuntu: sudo apt-get install tesseract-ocr"
    echo "  CentOS: sudo yum install tesseract"
    echo ""
    echo "After installation, verify: tesseract --version"
else
    tesseract --version
fi

echo ""
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Make sure Tesseract-OCR is installed (see above if needed)"
echo "2. Run the application: python3 questionnaire_scraper.py"
echo "3. See README.md for usage instructions"
echo "4. Check SETUP_GUIDE.md if you encounter issues"
echo ""
echo "============================================================"
