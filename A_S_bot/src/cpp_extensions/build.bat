@echo off
REM Build script for Windows
REM Requires: Python 3.7+, Visual Studio Build Tools, pybind11

echo ============================================
echo Building C++ Extensions for Auto Test Corrector
echo ============================================
echo.

REM Check if pybind11 is installed
python -c "import pybind11" 2>nul
if errorlevel 1 (
    echo [ERROR] pybind11 not found!
    echo Installing pybind11...
    pip install pybind11
    if errorlevel 1 (
        echo [ERROR] Failed to install pybind11
        exit /b 1
    )
)

echo [INFO] Building extensions...
python setup.py build_ext --inplace

if errorlevel 1 (
    echo [ERROR] Build failed!
    echo.
    echo Make sure you have Visual Studio Build Tools installed:
    echo https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
    exit /b 1
)

echo.
echo ============================================
echo Build successful!
echo ============================================
echo.
echo Generated files:
dir /b *.pyd 2>nul
echo.
echo To use in Python:
echo   import fast_ocr_cpp
echo   import fast_color_detection_cpp
echo.

pause
