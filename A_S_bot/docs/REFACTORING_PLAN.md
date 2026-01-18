# Refactoring Plan - Convert to Background Helper Script

## Overview

The current codebase implements a GUI-based questionnaire corrector. However, the actual requirement is a **background helper script** that:
- Runs invisibly
- Reads questions from screen (OCR)
- Looks up correct answers (database read-only)
- Auto-corrects wrong clicks
- Never writes to database

This document outlines the refactoring needed.

---

## Current Issues

### 1. GUI Architecture (WRONG ❌)
**Current**: `main.py` has Tkinter GUI with buttons
**Problem**: Script should run in background invisibly
**Solution**: Remove all GUI code, create CLI-based script

### 2. Database Writing (WRONG ❌)
**Current**: `log_correction()` writes to database
**Problem**: Script should only read
**Solution**: Remove all write operations

### 3. User Interaction Required (WRONG ❌)
**Current**: User clicks "Setup Regions" → "Start Monitoring"
**Problem**: Should be fully automatic
**Solution**: Auto-detect regions or use config/CLI args

### 4. Visible Monitoring (WRONG ❌)
**Current**: Shows status, statistics, corrections
**Problem**: Should be invisible
**Solution**: Silent background operation, optional logging to file

---

## Refactoring Steps

### Phase 1: Remove GUI Components

#### Files to Modify
- `src/main.py` - **REMOVE GUI ENTIRELY**

#### Changes
1. Remove Tkinter imports
2. Remove all GUI classes (AutoTestCorrector)
3. Remove create_gui() method
4. Remove update_stats() and logging to display
5. Keep only core logic:
   - OCRProcessor
   - ShapeDetector
   - AnswerBlockDetector
   - HybridDatabaseManager usage

#### Result
No GUI window, silent operation

---

### Phase 2: Convert to Read-Only Database

#### Files to Modify
- `src/hybrid_database.py` - Keep read methods only
- `src/main.py` - Remove write calls

#### Changes
Remove these methods from usage:
- ❌ `create_question()` - Never call
- ❌ `update_question()` - Never call
- ❌ `delete_question()` - Never call
- ❌ `add_answer()` - Never call
- ❌ `log_correction()` - Never call
- ❌ `import_existing_data()` - Never call

Keep these methods:
- ✅ `get_all_questions()` - Load question DB into memory
- ✅ `get_question()` - Lookup by ID
- ✅ `search_questions()` - Fuzzy match
- ✅ `get_answers()` - Get correct answers

#### Result
Script only reads from database, never writes

---

### Phase 3: Create Background Helper Script

#### New File: `src/helper.py`

```python
"""Background questionnaire helper script"""

import sys
import time
import argparse
import pyautogui
import cv2
from ocr_processor import OCRProcessor
from database_reader import DatabaseReader
from screen_monitor import ScreenMonitor

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Questionnaire Helper")
    parser.add_argument('--config', type=str, help='Config file path')
    parser.add_argument('--question-region', type=str, help='x:y:w:h')
    parser.add_argument('--answers-region', type=str, help='x:y:w:h')
    args = parser.parse_args()

    # Load configuration
    if args.config:
        config = load_config(args.config)
    else:
        config = parse_regions_args(args)

    # Initialize components
    ocr = OCRProcessor(config)
    db = DatabaseReader(config)  # READ-ONLY
    monitor = ScreenMonitor(config)

    # Load all questions into memory (once)
    all_questions = db.get_all_questions()
    answers_db = {q['id']: q['answers'] for q in all_questions}

    print("[*] Questionnaire helper started")
    print("[*] Question region:", config['question_region'])
    print("[*] Answers region:", config['answers_region'])

    try:
        while True:
            # Get current screenshot
            screenshot = monitor.capture_screen()

            # Extract question text
            question_text = ocr.extract_question(screenshot, config)

            # Find matching question in database
            matching_q = find_question(question_text, all_questions)

            if matching_q:
                # Get correct answers
                correct_answers = [a['text'] for a in matching_q['answers'] if a['is_correct']]

                # Check user clicks
                user_clicked = monitor.detect_click()
                if user_clicked:
                    user_answer = ocr.extract_clicked_answer(screenshot, config, user_clicked)

                    # If user clicked wrong answer → auto-correct
                    if user_answer not in correct_answers:
                        correct_location = find_answer_location(screenshot, correct_answers[0], config)
                        pyautogui.click(correct_location[0], correct_location[1])
                        print(f"[!] Auto-corrected: {user_answer} → {correct_answers[0]}")

            time.sleep(0.5)  # Monitor interval

    except KeyboardInterrupt:
        print("[*] Helper stopped")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

---

### Phase 4: Create Modular Components

#### New File: `src/screen_monitor.py`
```python
"""Screen monitoring and click detection"""

import pyautogui
import cv2
import numpy as np

class ScreenMonitor:
    def __init__(self, config):
        self.question_region = config['question_region']
        self.answers_region = config['answers_region']
        self.last_click = None

    def capture_screen(self):
        """Capture current screen as image"""
        return pyautogui.screenshot()

    def detect_click(self):
        """Detect if user clicked in answers region"""
        # Monitor mouse position
        # Return click location if detected
        pass

    def extract_region(self, image, region):
        """Extract specific region from image"""
        x, y, w, h = region
        return image.crop((x, y, x+w, y+h))
```

#### New File: `src/database_reader.py`
```python
"""Read-only database interface"""

class DatabaseReader:
    def __init__(self, config):
        self.db = HybridDatabaseManager(
            sqlite_path=config['database_file'],
            api_url=config.get('api_url'),
            use_api=config.get('use_api', True)
        )

    def get_all_questions(self):
        """Load all questions from DB (read-only)"""
        return self.db.get_all_questions(include_answers=True)

    def search_questions(self, text):
        """Search for questions (read-only)"""
        return self.db.search_questions(text)

    def get_question(self, question_id):
        """Get specific question (read-only)"""
        return self.db.get_question(question_id)

    # NO WRITE METHODS - READ ONLY
```

---

### Phase 5: Update Configuration

#### `docs/config.json`
```json
{
  "tesseract_path": "C:\\dt\\Tesseract-OCR\\tesseract.exe",
  "database_file": "data/test_questions.db",
  "api_url": "https://question-database-api.onrender.com",
  "use_api": true,
  "fuzzy_match_threshold": 85,
  "monitoring_interval_seconds": 0.5,
  "ocr_language": "srp+eng"
}
```

**Note**: No GUI or write-related settings

---

### Phase 6: Update Documentation

#### Files to Create
1. **`docs/HELPER_USAGE.md`** - How to run the helper
2. **`docs/CLI_REFERENCE.md`** - Command-line arguments
3. **`docs/CONFIGURATION.md`** - Config file format

#### Files to Update
1. **`README.md`** - Change to describe helper script
2. **`docs/SETUP_INSTRUCTIONS.md`** - CLI setup instead of GUI

---

## File Organization After Refactoring

```
src/
├── helper.py                    ← Main background script (NEW)
├── ocr_processor.py             ← OCR reading (MODIFIED - keep only read)
├── screen_monitor.py            ← Screen capture & click detection (NEW)
├── database_reader.py           ← Read-only DB access (NEW)
├── answer_detector.py           ← Answer detection (KEEP)
├── shape_detector.py            ← Shape detection (KEEP)
├── remote_database.py           ← API client (KEEP - but read-only usage)
├── hybrid_database.py           ← DB manager (KEEP - but read-only usage)
├── test_integration.py          ← Update tests for helper (MODIFIED)
└── cpp_extensions/              ← Keep optional performance boost
```

---

## Step-by-Step Implementation

### Step 1: Create `src/database_reader.py`
Read-only wrapper around hybrid_database

### Step 2: Create `src/screen_monitor.py`
Screen capture and click detection

### Step 3: Create `src/helper.py`
Main background script

### Step 4: Simplify `src/ocr_processor.py`
Remove GUI-related code

### Step 5: Remove GUI from `src/main.py`
Delete all Tkinter code, keep only helper logic

### Step 6: Create `docs/HELPER_USAGE.md`
Usage documentation

### Step 7: Update `docs/CLI_REFERENCE.md`
CLI arguments documentation

### Step 8: Update `src/test_integration.py`
Tests for helper script

### Step 9: Update `README.md`
Describe as background helper, not program

### Step 10: Update `docs/SETUP_INSTRUCTIONS.md`
CLI-based setup instructions

---

## Comparison: Before and After

### Before (Current - WRONG)
```
Terminal: python src/main.py
    ↓
GUI window opens with buttons
    ↓
User clicks "Setup Regions"
    ↓
User draws regions on screen
    ↓
User clicks "Start Monitoring"
    ↓
GUI shows status, corrections, statistics
    ↓
Database modified with correction logs
    ↓
User clicks "Stop Monitoring"
```

### After (Correct - RIGHT)
```
Terminal: python src/helper.py --config docs/config.json
    ↓
Script starts silently (no output, no window)
    ↓
Loads questions from database into memory
    ↓
Begins background monitoring loop
    ↓
Monitors user clicks continuously
    ↓
Auto-corrects wrong answers instantly
    ↓
No database writes
    ↓
No GUI updates
    ↓
User takes questionnaire normally
    ↓
Ctrl+C to stop (or questionnaire closes)
```

---

## Database Access Changes

### Current (WRONG)
```python
# In main.py
self.db.create_question(...)        # ❌ Writing
self.db.log_correction(...)         # ❌ Writing
self.db.import_existing_data()      # ❌ Writing
```

### After (RIGHT)
```python
# In helper.py (read-only)
all_questions = db.get_all_questions()          # ✅ Reading
matching_q = db.search_questions(text)          # ✅ Reading
correct_answers = db.get_question(q_id)         # ✅ Reading

# NEVER WRITE:
# db.log_correction(...)    # ❌ NO
# db.create_question(...)   # ❌ NO
# db.add_answer(...)        # ❌ NO
```

---

## Summary of Changes

| Component | Current | After | Status |
|-----------|---------|-------|--------|
| GUI | Tkinter window | None | Delete |
| Database | Write + Read | Read-only | Restrict |
| Startup | User clicks button | Auto-start CLI | Refactor |
| Output | Status display | Silent/logging | Simplify |
| Config | GUI buttons | CLI args + file | Create |
| Monitoring | Manual start/stop | Auto continuous | Automate |

---

## Estimated Effort

- **Phase 1** (Remove GUI): 2 hours
- **Phase 2** (Read-only DB): 1 hour
- **Phase 3** (Create helper): 3 hours
- **Phase 4** (Modular components): 2 hours
- **Phase 5** (Configuration): 1 hour
- **Phase 6** (Documentation): 2 hours
- **Testing**: 2 hours

**Total**: ~13 hours of refactoring

---

## Benefits After Refactoring

✅ **Correct Purpose** - Helper script, not application
✅ **Silent Operation** - No GUI, no visible windows
✅ **Automatic** - Starts and runs without user interaction
✅ **Read-Only** - Never modifies database
✅ **Background** - Invisible to user
✅ **Simple** - CLI-based, easy to use
✅ **Proper Design** - Matches actual requirement

---

## Risk Assessment

⚠️ **High-Impact Changes**:
- Removing entire GUI architecture
- Changing operation model (manual to automatic)
- Changing database model (write to read-only)

✅ **Mitigation**:
- Keep backup of original code
- Create comprehensive tests
- Document all changes
- Test thoroughly before deployment

---

## Next Actions

1. Review this plan
2. Confirm approach with user
3. Start Phase 1: Remove GUI
4. Continue through phases in order
5. Test after each phase
6. Update documentation continuously

**Status**: Plan Created ✓
**Next**: Await user approval to begin refactoring

---

**Key Insight**: This is not a program with a GUI. It's a background helper script that should be invisible to the user and read-only from the database.
