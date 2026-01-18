@echo off
REM Serbian Questionnaire Scraper - Quick Launch
REM Double-click this file to run the application

echo Starting Serbian Questionnaire Scraper...
echo.

REM Check if exe exists
if not exist "dist\Serbian Questionnaire Scraper.exe" (
    echo ERROR: Executable not found!
    echo Expected location: dist\Serbian Questionnaire Scraper.exe
    echo.
    echo Please ensure the dist folder exists with the compiled executable.
    pause
    exit /b 1
)

REM Check if Tesseract is installed
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo WARNING: Tesseract-OCR not found!
    echo.
    echo Tesseract must be installed at: C:\Program Files\Tesseract-OCR
    echo.
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Continue anyway? (May fail if Tesseract is not installed)
    pause
)

REM Run the executable
"dist\Serbian Questionnaire Scraper.exe"

REM If exe fails, show error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    echo Check the output above for details.
    pause
)
