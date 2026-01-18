# Running the Questionnaire Scraper as .EXE

## Quick Start

Your executable file is ready to use!

**File Location**: `d:\Project\question_scraper_newDB\dist\Serbian Questionnaire Scraper.exe`

**Size**: 63 MB (includes all Python libraries)

**To Run**: Simply double-click the .exe file - no Python needed!

---

## Installation Steps

### Step 1: Verify Tesseract-OCR is Installed

The executable needs Tesseract-OCR to work.

**Check if installed**:
- Open Windows Explorer
- Navigate to: `C:\Program Files\Tesseract-OCR`
- Should see: `tesseract.exe` file

**If not installed**:
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Accept default location: `C:\Program Files\Tesseract-OCR`
4. Restart your computer

### Step 2: Run the Application

**Method 1: Direct Click**
1. Open Windows Explorer
2. Navigate to: `d:\Project\question_scraper_newDB\dist\`
3. Double-click: `Serbian Questionnaire Scraper.exe`
4. Application opens in ~5-10 seconds

**Method 2: Create Desktop Shortcut** (Recommended)
1. Navigate to: `d:\Project\question_scraper_newDB\dist\`
2. Right-click on: `Serbian Questionnaire Scraper.exe`
3. Select: "Create shortcut"
4. A shortcut file will be created
5. Cut and paste to: Desktop
6. Double-click shortcut to run

**Method 3: Create Start Menu Shortcut**
1. Navigate to: `d:\Project\question_scraper_newDB\dist\`
2. Right-click on: `Serbian Questionnaire Scraper.exe`
3. Select: "Pin to Start"
4. Find in Start Menu
5. Click to launch

**Method 4: Command Line**
```bash
"d:\Project\question_scraper_newDB\dist\Serbian Questionnaire Scraper.exe"
```

### Step 3: First Time Setup

When you run for the first time:
1. App checks for Tesseract-OCR
2. App checks for API connection
3. Window opens with interface
4. Ready to use!

---

## Troubleshooting

### Issue: "Tesseract is not found"
**Solution**:
1. Tesseract must be at: `C:\Program Files\Tesseract-OCR`
2. Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
3. Use default installation path
4. Restart app

### Issue: "API Disconnected"
**Solution**:
1. Check internet connection
2. Render.com API might be down
3. Try again in a few moments

### Issue: App runs but window doesn't appear
**Solution**:
1. Wait 5-10 seconds (first launch is slow)
2. App is starting, loading all Python libraries
3. Window should appear

### Issue: "Could not extract text"
**Solution**:
1. Tesseract is installed but not working
2. Reinstall Tesseract
3. Make sure you selected full installation

### Issue: "Windows protected your PC"
**Solution** (if Windows shows security warning):
1. Click "More info"
2. Click "Run anyway"
3. This is normal for new executables
4. Safe to ignore (you created this file)

---

## File Information

| Property | Value |
|----------|-------|
| Filename | Serbian Questionnaire Scraper.exe |
| Size | 63 MB |
| Location | d:\Project\question_scraper_newDB\dist\ |
| Type | Windows Executable |
| Architecture | 64-bit |
| Python Version | 3.13 (embedded) |
| External Dependency | Tesseract-OCR |

**Why 63 MB?**
- Includes complete Python 3.13 runtime
- Includes all required libraries (numpy, OpenCV, PIL, etc.)
- All libraries are bundled inside the exe

---

## What's Included in the EXE

✓ Python 3.13 runtime
✓ All dependencies:
  - requests (HTTP client)
  - Pillow (image processing)
  - pytesseract (OCR interface)
  - pynput (keyboard listener)
  - opencv-python (computer vision)
  - numpy (numerical operations)
✓ Your questionnaire scraper code
✓ All features (capture, preview, sync)

**What's NOT included** (must install separately):
✗ Tesseract-OCR (must install from GitHub)
✗ Internet connection (must have for SYNC)

---

## Usage Instructions

Once the application is running, follow the normal workflow:

1. **Click START** - Listening enabled
2. **Press SPACEBAR** - Begin capture
3. **Draw rectangle** around question
4. **Draw rectangle** around answers
5. **Status shows** - Success!
6. **Press SPACEBAR again** - Next question
7. **Click STOP** - End session
8. **Click PREVIEW** - Review data
9. **Click SYNC** - Upload to database

See `QUICK_START.md` for detailed usage guide.

---

## Performance

| Metric | Time |
|--------|------|
| First startup | 5-10 seconds (loading libraries) |
| Normal startup | 2-3 seconds |
| Per question capture | ~5 seconds |
| 10 questions | ~50 seconds |
| API upload | 1-2 seconds per question |

---

## Creating Additional Shortcuts

### Desktop Shortcut

1. Navigate to: `d:\Project\question_scraper_newDB\dist\`
2. Right-click on: `Serbian Questionnaire Scraper.exe`
3. Create shortcut
4. Drag to Desktop

### Quick Access

1. Open File Explorer
2. Navigate to: `d:\Project\question_scraper_newDB\dist\`
3. Right-click on: `Serbian Questionnaire Scraper.exe`
4. Select: "Add to Quick Access"

### Batch File (Optional)

Create `run_scraper.bat` with:
```batch
@echo off
"d:\Project\question_scraper_newDB\dist\Serbian Questionnaire Scraper.exe"
```

Double-click to run.

---

## Rebuilding the EXE

If you modify the Python code and want to rebuild:

```bash
cd d:\Project\question_scraper_newDB
pyinstaller --onefile --windowed --name "Serbian Questionnaire Scraper" questionnaire_scraper.py
```

New exe will be in: `dist\` folder

---

## Frequently Asked Questions

**Q: Do I need Python installed?**
A: No! Python is embedded in the exe.

**Q: Why is the exe so large (63 MB)?**
A: It includes the entire Python runtime and all libraries.

**Q: Can I share this exe with others?**
A: Yes! As long as they have Tesseract-OCR installed.

**Q: Does it work on other computers?**
A: Yes, on Windows 10/11 64-bit with Tesseract installed.

**Q: Can I run it without clicking?**
A: Yes, from command line or batch file.

**Q: Is it safe?**
A: Yes, you created it yourself. It's your code compiled.

**Q: Can I delete the source Python files?**
A: Yes, the exe is standalone. Keep backup though.

**Q: Will updates require rebuilding?**
A: Only if you modify the Python code.

---

## Next Steps

1. **Ensure Tesseract-OCR is installed**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\Program Files\Tesseract-OCR`

2. **Test the executable**
   - Double-click: `Serbian Questionnaire Scraper.exe`
   - Check if window opens
   - Verify API shows "Connected"

3. **Create desktop shortcut** (optional)
   - Makes it easier to access
   - See instructions above

4. **Start capturing**
   - Click START
   - Follow the workflow
   - Enjoy!

---

## Support

If you encounter issues:

1. **Check Tesseract installation**
   - Must be at: `C:\Program Files\Tesseract-OCR`
   - Verify tesseract.exe exists there

2. **Check internet connection**
   - SYNC requires internet
   - API needs connectivity

3. **Check database**
   - Run: `python test_database.py` (from source directory)
   - Verify write operations work

4. **Reinstall if needed**
   - Delete entire dist folder
   - Run pyinstaller again (see "Rebuilding" section)

---

## Summary

✓ **Executable ready**: `Serbian Questionnaire Scraper.exe`
✓ **Size**: 63 MB (self-contained)
✓ **No Python needed**: Embedded in exe
✓ **Just click**: Double-click and run
✓ **Easy shortcuts**: Desktop or Start menu

**Location**: `d:\Project\question_scraper_newDB\dist\`

**Next**: Install Tesseract-OCR, then run the exe!
