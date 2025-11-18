# Auto Test Corrector - Complete Reference Guide

**Version:** MVP 1.0  
**Last Updated:** 2025-10-24  
**Language:** Python 3.8+

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Database Schema](#database-schema)
5. [Core Components](#core-components)
6. [Key Algorithms](#key-algorithms)
7. [Configuration](#configuration)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)
10. [Future Enhancements](#future-enhancements)
11. [Code Locations](#code-locations)

---

## 1. Project Overview

### Purpose
Real-time test monitoring system that watches screen activity, detects user answer selections, validates against a database, and automatically corrects wrong answers by clicking the correct one.

### Key Features
- ✅ Background screen monitoring
- ✅ Serbian (latinica) OCR support
- ✅ Fuzzy question matching (85%+ similarity)
- ✅ Automatic wrong answer correction
- ✅ SQLite database with import capabilities
- ✅ Activity logging and statistics
- ✅ User-defined region selection

### Technology Stack
- **GUI:** Tkinter
- **Screen Capture:** PyAutoGUI
- **Image Processing:** OpenCV (cv2)
- **OCR:** Tesseract (Serbian + English)
- **Database:** SQLite3
- **Fuzzy Matching:** fuzzywuzzy
- **Threading:** Python threading module

---

## 2. Architecture

### System Flow
```
┌─────────────────┐
│   GUI Control   │ ← User interaction
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │  Monitoring Thread   │ ← Background process
    │  (continuous loop)   │
    └────┬─────────────────┘
         │
    ┌────▼────────────────┐
    │  Screen Capture     │ ← PyAutoGUI
    │  (0.5s interval)    │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  OCR Processing     │ ← Tesseract
    │  (question region)  │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  Database Matching  │ ← SQLite + Fuzzy
    │  (85% threshold)    │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  Answer Detection   │ ← Screen diff
    │  (wait for click)   │
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  Validation         │ ← Compare w/ DB
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │  Auto-Correction    │ ← PyAutoGUI click
    │  (if wrong)         │
    └─────────────────────┘
```

### Thread Management
- **Main Thread:** GUI event loop (Tkinter)
- **Monitor Thread:** Background monitoring (daemon thread)
- **Communication:** `root.after()` for thread-safe GUI updates

---

## 3. Installation & Setup

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Pip packages
pip install opencv-python
pip install pytesseract
pip install pyautogui
pip install pillow
pip install fuzzywuzzy
pip install python-Levenshtein
```

### Tesseract OCR Setup
1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\dt\Tesseract-OCR\` (or update path in code)
3. Download Serbian language pack: `srp.traineddata`
4. Place in: `C:\dt\Tesseract-OCR\tessdata\`

### Verify Installation
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\dt\Tesseract-OCR\tesseract.exe"
print(pytesseract.get_languages())  # Should include 'srp' and 'eng'
```

### File Structure
```
project/
├── auto_test_corrector.py       # Main program
├── test_questions.db            # SQLite database (auto-created)
├── qa_data.json                 # Optional import source
├── reference.md                 # This file
└── README.md                    # User guide
```

---

## 4. Database Schema

### Tables

#### `questions`
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,           -- Full question text
    question_type TEXT DEFAULT 'single',   -- 'single' or 'multi'
    required_answers INTEGER DEFAULT 1,    -- How many correct answers needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `answers`
```sql
CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,                   -- Foreign key to questions
    answer_text TEXT NOT NULL,             -- Answer text
    is_correct BOOLEAN,                    -- 1 = correct, 0 = wrong
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
```

#### `correction_log`
```sql
CREATE TABLE correction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    question_text TEXT,                    -- What question
    wrong_answer TEXT,                     -- What user clicked
    correct_answer TEXT,                   -- What was auto-clicked
    correction_successful BOOLEAN          -- Did correction work
);
```

### Sample Data
```sql
-- Insert question
INSERT INTO questions (question_text, question_type, required_answers)
VALUES ('Koji je glavni grad Srbije?', 'single', 1);

-- Insert answers
INSERT INTO answers (question_id, answer_text, is_correct)
VALUES (1, 'Beograd', 1);

INSERT INTO answers (question_id, answer_text, is_correct)
VALUES (1, 'Niš', 0);

INSERT INTO answers (question_id, answer_text, is_correct)
VALUES (1, 'Novi Sad', 0);
```

---

## 5. Core Components

### 5.1 AutoTestCorrector Class

Main class managing the entire system.

**Key Attributes:**
- `monitoring` (bool): Monitoring state
- `question_region` (tuple): (x1, y1, x2, y2) coordinates
- `answers_region` (tuple): (x1, y1, x2, y2) coordinates
- `current_question_id` (int): Matched question ID
- `answer_positions` (list): Detected answer locations
- `correction_count` (int): Total corrections made
- `total_questions` (int): Total questions processed

**Key Methods:**

#### `init_database()`
Creates SQLite database and tables if they don't exist.

#### `start_monitoring()`
Launches background monitoring thread.

#### `monitor_loop()`
Main background loop:
1. Captures question region
2. Detects changes (hash comparison)
3. OCRs new questions
4. Matches against database
5. Waits for user answer
6. Validates and corrects

#### `ocr_text(img)`
Extracts text from image using Tesseract.
- Uses Serbian + English languages
- Preprocesses with grayscale, resize, threshold
- Cleans special markers

#### `match_question(question_text)`
Fuzzy matches question against database.
- Returns: question_id or None
- Threshold: 85% similarity (fuzz.ratio)

#### `scan_answer_positions(screenshot_cv)`
Detects and stores answer block positions.
- Finds green/red color blocks
- OCRs each block
- Stores absolute screen coordinates

#### `wait_for_user_answer(screenshot_before)`
Monitors for screen changes indicating user clicked.
- Compares screenshots every 0.1s
- Threshold: change > 5 (normalized difference)
- Triggers validation on change

#### `validate_and_correct(screenshot_cv)`
Core correction logic:
1. Gets correct answers from DB
2. Detects which answer is selected
3. Fuzzy matches against correct/wrong lists
4. If wrong: finds correct answer position
5. Auto-clicks correct answer
6. Logs correction

#### `is_answer_selected(block_img)`
Heuristic to detect if answer block is selected.
- Checks for blue/dark color patterns
- Returns: True if selected

---

## 6. Key Algorithms

### 6.1 Fuzzy Question Matching

**Purpose:** Match OCR-extracted questions against database despite OCR errors.

**Algorithm:**
```python
def match_question(question_text):
    best_match = None
    best_score = 0
    
    for db_question in database:
        score = fuzz.ratio(question_text.lower(), db_question.lower())
        if score > best_score:
            best_score = score
            best_match = db_question
    
    return best_match if best_score >= 85 else None
```

**Threshold:** 85% similarity
- Higher = fewer false matches, may miss valid questions
- Lower = more matches, but more false positives

**Library:** `fuzzywuzzy.fuzz.ratio`
- Levenshtein distance based
- Case-insensitive comparison

### 6.2 Color Block Detection

**Purpose:** Find answer buttons by color (green = correct in preview, red = wrong in preview).

**Algorithm:**
```python
def detect_color_blocks(img, color_name):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    if color_name == "green":
        mask = cv2.inRange(hsv, [25, 20, 20], [95, 255, 255])
    else:  # red
        mask1 = cv2.inRange(hsv, [0, 20, 20], [25, 255, 255])
        mask2 = cv2.inRange(hsv, [155, 20, 20], [180, 255, 255])
        mask = mask1 + mask2
    
    # Morphological closing to fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    blocks = []
    for contour in contours:
        if area > 150 and width > 40 and height > 10:
            blocks.append({'x': x, 'y': y, 'w': w, 'h': h})
    
    return sorted(blocks, key=lambda b: b['y'])  # Top to bottom
```

**HSV Ranges:**
- Green: H=25-95, S=20-255, V=20-255
- Red: H=0-25 or 155-180, S=20-255, V=20-255

**Minimum Block Size:**
- Area: 150 pixels
- Width: 40 pixels
- Height: 10 pixels

### 6.3 Screen Change Detection

**Purpose:** Detect when user clicks an answer.

**Algorithm:**
```python
def wait_for_user_answer(screenshot_before):
    while monitoring:
        current_screenshot = capture_screen()
        
        before_region = screenshot_before[y1:y2, x1:x2]
        current_region = current_screenshot[y1:y2, x1:x2]
        
        diff = cv2.absdiff(before_region, current_region)
        change = np.sum(diff) / diff.size
        
        if change > 5:  # Threshold
            validate_and_correct(current_screenshot)
            break
        
        time.sleep(0.1)
```

**Change Metric:** Sum of absolute pixel differences, normalized by region size.
**Threshold:** 5 (empirical value, adjust if needed)

### 6.4 Answer Selection Detection

**Purpose:** Identify which answer is currently selected on screen.

**Heuristic:**
```python
def is_answer_selected(block_img):
    hsv = cv2.cvtColor(block_img, cv2.COLOR_BGR2HSV)
    
    # Check for blue selection highlight
    mask_blue = cv2.inRange(hsv, [90, 50, 50], [130, 255, 255])
    blue_ratio = np.sum(mask_blue > 0) / mask_blue.size
    
    # Check for dark/filled appearance
    mask_dark = cv2.inRange(hsv, [0, 0, 0], [180, 255, 100])
    dark_ratio = np.sum(mask_dark > 0) / mask_dark.size
    
    return blue_ratio > 0.1 or dark_ratio > 0.3
```

**Note:** This heuristic may need adjustment based on specific test UI appearance.

---

## 7. Configuration

### Adjustable Parameters

#### OCR Settings
```python
# In ocr_text() method
pytesseract.image_to_string(
    processed, 
    lang="srp+eng",          # Languages: Serbian + English
    config="--oem 1 --psm 6" # OEM 1 = LSTM, PSM 6 = uniform block
)
```

**Language Codes:**
- `srp` = Serbian
- `eng` = English
- `srp+eng` = Both (recommended)

**PSM Modes (Page Segmentation):**
- `3` = Fully automatic
- `6` = Uniform block of text (recommended)
- `11` = Sparse text

#### Fuzzy Matching Threshold
```python
# In match_question() and validate_and_correct()
if score >= 85:  # 85% similarity threshold
```

**Recommended Range:** 80-90%
- 80% = More lenient, catches more variations
- 90% = Stricter, fewer false matches

#### Screen Monitoring Interval
```python
# In monitor_loop()
time.sleep(0.5)  # Check every 0.5 seconds
```

**Recommended Range:** 0.3-1.0 seconds
- Faster = More responsive, higher CPU usage
- Slower = Less CPU, may miss quick changes

#### Answer Change Detection Threshold
```python
# In wait_for_user_answer()
if change > 5:  # Threshold for significant change
```

**Recommended Range:** 3-10
- Lower = More sensitive to small changes
- Higher = Only detects major changes

#### Selection Detection Thresholds
```python
# In is_answer_selected()
blue_ratio > 0.1    # 10% of pixels are blue
dark_ratio > 0.3    # 30% of pixels are dark
```

**Adjust based on test UI appearance.**

---

## 8. Usage Guide

### First-Time Setup

#### Step 1: Launch Program
```bash
python auto_test_corrector.py
```

#### Step 2: Import Data (Optional)
- If you have `qa_data.json` in same folder, it auto-imports
- Or click **"📥 Import Data"** to paste JSON manually

#### Step 3: Setup Regions
1. Click **"⚙️ Setup Regions"**
2. **Screen 1:** Drag around the QUESTION text area
3. **Screen 2:** Drag around ALL ANSWER OPTIONS
4. Click OK when done

#### Step 4: Start Monitoring
1. Click **"🚀 Start Monitoring"**
2. Status changes to **"● MONITORING"** (green)
3. System now watches in background

### During Test

#### Normal Operation
1. Read question
2. Click your answer
3. System automatically:
   - Detects your click
   - Validates against database
   - If wrong: auto-clicks correct answer
   - Logs activity

#### Signals for Next Question
- Screen changes (new question appears)
- Or press **'N'** key to force next

#### Stopping
- Click **"⏹️ Stop"** button
- Or press **ESC** key

### Post-Session

#### View Statistics
- Click **"📊 Database Stats"**
- Shows:
  - Total questions processed
  - Correct first try count
  - Auto-corrections count
  - Success rate

#### Review Activity Log
- Scroll through log panel
- Shows:
  - Timestamps
  - Question detections
  - Corrections made
  - Errors/warnings

---

## 9. Troubleshooting

### Issue: Questions Not Detected

**Possible Causes:**
1. Question region not set correctly
2. OCR not reading text properly
3. Question not in database

**Solutions:**
1. **Re-setup regions:** Click "⚙️ Setup Regions" again
2. **Check OCR quality:**
   - Ensure question text is clear on screen
   - Increase screen resolution if possible
   - Check Tesseract installation
3. **Verify database:**
   - Click "📊 Database Stats"
   - Ensure questions imported
   - Check log for "Question not in database" message

### Issue: Wrong Answer Not Corrected

**Possible Causes:**
1. Correct answer not in database
2. Answer positions not detected properly
3. Selection detection heuristic failing

**Solutions:**
1. **Check database:** Ensure correct answers exist
2. **Re-scan answers:** Stop and restart monitoring
3. **Adjust selection detection:**
   ```python
   # In is_answer_selected(), try different thresholds
   blue_ratio > 0.05  # More sensitive
   dark_ratio > 0.2   # More sensitive
   ```

### Issue: Program Clicks Wrong Position

**Possible Causes:**
1. Answer positions drifted (UI scrolled)
2. Multiple monitors confusing coordinates

**Solutions:**
1. **Keep UI static:** Don't scroll during test
2. **Single monitor:** Run test on primary display
3. **Re-setup regions:** If UI moved, setup again

### Issue: OCR Gibberish

**Possible Causes:**
1. Wrong language pack
2. Text too small/blurry
3. Special characters

**Solutions:**
1. **Verify language:** Check `srp.traineddata` exists
2. **Increase text size:** Zoom browser/test UI
3. **Clean text preprocessing:**
   ```python
   # In ocr_text(), add more preprocessing
   gray = cv2.GaussianBlur(gray, (3, 3), 0)
   gray = cv2.resize(gray, None, fx=3, fy=3)  # More upscaling
   ```

### Issue: High CPU Usage

**Solutions:**
1. **Increase monitoring interval:**
   ```python
   time.sleep(1.0)  # Instead of 0.5
   ```
2. **Reduce screenshot size:** Select smaller regions

### Issue: Database Locked Error

**Cause:** Concurrent access to SQLite.

**Solution:**
```python
# Add retry logic
import sqlite3
import time

def connect_with_retry(db_file, retries=3):
    for i in range(retries):
        try:
            return sqlite3.connect(db_file)
        except sqlite3.OperationalError:
            time.sleep(0.1)
    raise Exception("Could not connect to database")
```

---

## 10. Future Enhancements

### Phase 2 Features

#### 1. Automatic UI Detection
- Auto-find question/answers regions
- Detect "Next Question" button
- No manual setup needed

#### 2. Multi-Monitor Support
- Select which monitor to watch
- Handle different screen resolutions

#### 3. Advanced Statistics
- Per-topic accuracy
- Time per question
- Difficulty analysis
- Export reports

#### 4. Correction Modes
- **Instant:** Auto-correct immediately (current)
- **Confirm:** Ask before correcting
- **Alert-Only:** Just show warning, no click

#### 5. Keyboard Shortcuts
- `SPACE`: Force question detection
- `N`: Next question
- `R`: Rescan answers
- `ESC`: Cancel current operation
- `P`: Pause monitoring

#### 6. Cloud Sync
- Sync database across devices
- Collaborative question building
- Real-time updates

#### 7. Machine Learning
- Learn from corrections
- Improve OCR accuracy
- Predict question types

#### 8. Answer Confidence
- Show confidence scores
- Warn on low-confidence corrections
- Manual override option

### Code Improvements

#### Better Error Handling
```python
try:
    # Risky operation
except SpecificException as e:
    self.log(f"Specific error: {e}", "ERROR")
    # Fallback behavior
except Exception as e:
    self.log(f"Unexpected error: {e}", "ERROR")
    # General fallback
finally:
    # Cleanup
```

#### Logging to File
```python
import logging

logging.basicConfig(
    filename='corrector.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

#### Configuration File
```python
# config.json
{
    "tesseract_path": "C:\\dt\\Tesseract-OCR\\tesseract.exe",
    "fuzzy_threshold": 85,
    "monitor_interval": 0.5,
    "change_threshold": 5,
    "languages": "srp+eng"
}
```

---

## 11. Code Locations

### Important Functions Reference

| Function | Line # (approx) | Purpose |
|----------|----------------|---------|
| `__init__` | 25 | Initialize app |
| `init_database` | 55 | Create DB schema |
| `create_gui` | 95 | Build UI |
| `start_monitoring` | 280 | Start background thread |
| `monitor_loop` | 300 | Main monitoring loop |
| `ocr_text` | 380 | OCR processing |
| `match_question` | 410 | Fuzzy question matching |
| `scan_answer_positions` | 440 | Detect answer locations |
| `wait_for_user_answer` | 480 | Detect user click |
| `validate_and_correct` | 520 | Core correction logic |
| `detect_color_blocks` | 600 | Find colored regions |
| `is_answer_selected` | 640 | Check if selected |
| `import_existing_data` | 680 | Import qa_data.json |

### State Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `monitoring` | bool | Is monitoring active? |
| `question_region` | tuple | (x1,y1,x2,y2) for question |
| `answers_region` | tuple | (x1,y1,x2,y2) for answers |
| `current_question_id` | int | Matched question ID |
| `answer_positions` | list | [{text, x, y, region}, ...] |
| `correction_count` | int | Total corrections made |
| `total_questions` | int | Questions processed |
| `correct_first_try` | int | Correct on first attempt |

### Database Queries

#### Get All Questions
```sql
SELECT id, question_text, question_type, required_answers 
FROM questions 
ORDER BY created_at DESC;
```

#### Get Answers for Question
```sql
-- Correct answers
SELECT answer_text FROM answers 
WHERE question_id = ? AND is_correct = 1;

-- Wrong answers
SELECT answer_text FROM answers 
WHERE question_id = ? AND is_correct = 0;
```

#### Get Correction History
```sql
SELECT timestamp, question_text, wrong_answer, correct_answer 
FROM correction_log 
WHERE correction_successful = 1 
ORDER BY timestamp DESC 
LIMIT 50;
```

#### Statistics Query
```sql
SELECT 
    COUNT(*) as total_corrections,
    SUM(CASE WHEN correction_successful = 1 THEN 1 ELSE 0 END) as successful,
    COUNT(DISTINCT question_text) as unique_questions
FROM correction_log;
```

---

## 12. Common Patterns & Snippets

### Thread-Safe GUI Updates

**Problem:** Background thread cannot directly update GUI.

**Solution:** Use `root.after()`
```python
# In background thread
def background_task():
    result = some_computation()
    
    # Safe GUI update
    self.root.after(0, self.update_label, result)

# In main class
def update_label(self, text):
    self.label.config(text=text)
```

### Safe Screenshot Capture
```python
def safe_screenshot():
    try:
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        self.log(f"Screenshot failed: {e}", "ERROR")
        return None
```

### Database Connection Context Manager
```python
from contextlib import contextmanager

@contextmanager
def db_connection(db_file):
    conn = sqlite3.connect(db_file)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Usage
with db_connection(self.db_file) as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    results = cursor.fetchall()
```

### Robust OCR with Fallback
```python
def ocr_with_fallback(img):
    # Try primary method (Serbian + English)
    try:
        text = pytesseract.image_to_string(
            preprocess(img), 
            lang="srp+eng", 
            config="--oem 1 --psm 6"
        )
        if text.strip():
            return text.strip(), 90
    except:
        pass
    
    # Fallback 1: English only
    try:
        text = pytesseract.image_to_string(
            preprocess(img), 
            lang="eng", 
            config="--psm 6"
        )
        if text.strip():
            return text.strip(), 70
    except:
        pass
    
    # Fallback 2: Serbian only
    try:
        text = pytesseract.image_to_string(
            preprocess(img), 
            lang="srp", 
            config="--psm 3"
        )
        if text.strip():
            return text.strip(), 60
    except:
        pass
    
    return "", 0
```

### Fuzzy Answer Validation
```python
def fuzzy_validate_answer(clicked_text, correct_answers, threshold=85):
    """
    Returns: (is_correct, best_match, confidence)
    """
    best_match = None
    best_score = 0
    
    for correct in correct_answers:
        score = fuzz.ratio(clicked_text.lower(), correct.lower())
        if score > best_score:
            best_score = score
            best_match = correct
    
    is_correct = best_score >= threshold
    
    return is_correct, best_match, best_score
```

---

## 13. Testing Guide

### Unit Testing

#### Test OCR Function
```python
def test_ocr():
    # Create test image with text
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, "Test pitanje", (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    text = ocr_text(img)
    assert "test" in text.lower() or "pitanje" in text.lower()
```

#### Test Fuzzy Matching
```python
def test_fuzzy_matching():
    question_db = "Koji je glavni grad Srbije?"
    
    # Exact match
    assert match_question(question_db) is not None
    
    # With OCR error
    question_ocr = "Koji ie glavni gard Srbije?"
    assert match_question(question_ocr) is not None
    
    # Completely different
    question_wrong = "Sta je Python?"
    # Should not match if not in DB
```

#### Test Color Detection
```python
def test_color_blocks():
    # Create image with green rectangle
    img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 50), (150, 80), (0, 255, 0), -1)
    
    blocks = detect_color_blocks(img, "green")
    assert len(blocks) >= 1
    assert blocks[0]['w'] > 90  # Width check
```

### Integration Testing

#### Test Full Workflow
```python
def test_full_workflow():
    # 1. Import test data
    import_test_data()
    
    # 2. Setup regions (manual)
    print("Please setup regions...")
    
    # 3. Start monitoring
    start_monitoring()
    
    # 4. Simulate test
    # Navigate to test question
    # Click wrong answer
    # Verify correction occurred
    
    # 5. Check logs
    assert correction_count > 0
```

### Manual Testing Checklist

- [ ] Program launches without errors
- [ ] Database created successfully
- [ ] Data imports correctly
- [ ] Region selection works
- [ ] Monitoring starts without crash
- [ ] Questions detected correctly
- [ ] Answers scanned properly
- [ ] Wrong answer detected
- [ ] Auto-correction clicks correct answer
- [ ] Statistics update correctly
- [ ] Log shows all events
- [ ] Stop button works
- [ ] Can restart monitoring
- [ ] Database persists between sessions

---

## 14. Deployment Guide

### Standalone Executable

Using PyInstaller:

```bash
pip install pyinstaller

pyinstaller --onefile \
            --windowed \
            --icon=icon.ico \
            --add-data "C:\dt\Tesseract-OCR;Tesseract-OCR" \
            auto_test_corrector.py
```

**Note:** Tesseract must be bundled or installed separately.

### Requirements.txt
```txt
opencv-python==4.8.0.76
pytesseract==0.3.10
pyautogui==0.9.54
Pillow==10.0.0
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1
```

### Installation Script
```bash
#!/bin/bash
# install.sh

echo "Installing Auto Test Corrector..."

# Install Python packages
pip install -r requirements.txt

# Check Tesseract
if [ ! -f "C:\dt\Tesseract-OCR\tesseract.exe" ]; then
    echo "Please install Tesseract OCR to C:\dt\Tesseract-OCR\"
    exit 1
fi

# Create database
python -c "from auto_test_corrector import AutoTestCorrector; import tkinter as tk; root = tk.Tk(); app = AutoTestCorrector(root)"

echo "Installation complete!"
```

---

## 15. Performance Optimization

### Bottlenecks

1. **OCR Processing** (slowest)
   - Takes 0.5-2 seconds per image
   
2. **Screen Capture**
   - Takes 0.05-0.2 seconds
   
3. **Database Queries**
   - Usually < 0.01 seconds

### Optimization Strategies

#### 1. Cache OCR Results
```python
class OCRCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
    
    def get(self, img_hash):
        return self.cache.get(img_hash)
    
    def set(self, img_hash, text):
        if len(self.cache) >= self.max_size:
            # Remove oldest
            self.cache.pop(next(iter(self.cache)))
        self.cache[img_hash] = text
```

#### 2. Reduce Screenshot Size
```python
# Capture only necessary regions, not full screen
screenshot = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
```

#### 3. Database Indexing
```sql
CREATE INDEX idx_questions_text ON questions(question_text);
CREATE INDEX idx_answers_question ON answers(question_id);
CREATE INDEX idx_answers_correct ON answers(is_correct);
```

#### 4. Parallel Processing
```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

# Process OCR in parallel
future_question = executor.submit(ocr_text, question_img)
future_answers = executor.submit(scan_answers, answers_img)

question_text = future_question.result()
answers = future_answers.result()
```

#### 5. Reduce Image Size
```python
def downscale_for_ocr(img, max_width=800):
    h, w = img.shape[:2]
    if w > max_width:
        scale = max_width / w
        new_h = int(h * scale)
        img = cv2.resize(img, (max_width, new_h))
    return img
```

---

## 16. Security Considerations

### Data Privacy
- All data stored locally (SQLite)
- No external network calls (except if using Supabase)
- Screen captures not saved to disk

### Potential Risks
1. **Screen capture of sensitive info**
2. **Database contains test answers**
3. **Auto-clicking could be detected**

### Mitigation
```python
# Option 1: Encrypt database
import sqlite3
from sqlcipher3 import dbapi2 as sqlcipher

conn = sqlcipher.connect('test_questions.db')
conn.execute("PRAGMA key = 'your-encryption-key'")

# Option 2: Don't save screenshots
# Already implemented - only processed in memory

# Option 3: Add stealth mode
STEALTH_MODE = True
if STEALTH_MODE:
    # Randomize click timing
    delay = random.uniform(0.1, 0.5)
    time.sleep(delay)
    pyautogui.click(x, y)
```

---

## 17. Debugging Guide

### Enable Debug Logging
```python
class AutoTestCorrector:
    def __init__(self, root):
        self.DEBUG = True  # Add this
        # ...
    
    def debug_log(self, message):
        if self.DEBUG:
            print(f"[DEBUG] {message}")
            self.log(f"DEBUG: {message}", "INFO")
```

### Save Debug Images
```python
def debug_save_image(img, name):
    """Save image for debugging"""
    if not os.path.exists('debug'):
        os.makedirs('debug')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debug/{timestamp}_{name}.png"
    cv2.imwrite(filename, img)
    print(f"Saved debug image: {filename}")

# Usage
debug_save_image(question_img, "question")
debug_save_image(answers_img, "answers")
```

### Log OCR Results
```python
def ocr_text_debug(img):
    text = pytesseract.image_to_string(img, lang="srp+eng")
    
    # Log raw OCR output
    print(f"OCR Raw: {repr(text)}")
    
    # Log after cleaning
    cleaned = clean_text(text)
    print(f"OCR Cleaned: {repr(cleaned)}")
    
    return cleaned
```

### Monitor Performance
```python
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.3f}s")
        return result
    return wrapper

@timing_decorator
def ocr_text(img):
    # ... existing code ...
```

### Database Inspection
```python
def inspect_database():
    """Print database contents"""
    conn = sqlite3.connect('test_questions.db')
    cursor = conn.cursor()
    
    print("\n=== QUESTIONS ===")
    cursor.execute("SELECT * FROM questions LIMIT 5")
    for row in cursor.fetchall():
        print(row)
    
    print("\n=== ANSWERS ===")
    cursor.execute("SELECT * FROM answers LIMIT 10")
    for row in cursor.fetchall():
        print(row)
    
    print("\n=== CORRECTIONS ===")
    cursor.execute("SELECT * FROM correction_log ORDER BY timestamp DESC LIMIT 5")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()
```

---

## 18. Known Issues & Limitations

### Current Limitations

1. **Single Monitor Only**
   - Coordinates may be off on multi-monitor setups
   - **Workaround:** Run test on primary monitor

2. **Static UI Required**
   - If test UI scrolls/moves, positions become invalid
   - **Workaround:** Keep test window maximized and static

3. **OCR Accuracy**
   - Serbian OCR ~85-90% accurate
   - Special characters may be misread
   - **Workaround:** Use fuzzy matching with lower threshold

4. **Selection Detection**
   - Heuristic-based, not 100% reliable
   - May fail with unusual UI styles
   - **Workaround:** Adjust thresholds in `is_answer_selected()`

5. **No Multi-Answer Support**
   - Can only click one correct answer at a time
   - **Future:** Will handle multi-select questions

6. **Timing Dependent**
   - Fast users may outpace detection
   - **Workaround:** Increase monitoring frequency

### Known Bugs

**Bug #1:** Program freezes if monitoring thread crashes
- **Cause:** Unhandled exception in background thread
- **Fix:** Add try-except in `monitor_loop()`

**Bug #2:** Database locked during concurrent access
- **Cause:** SQLite doesn't handle concurrent writes well
- **Fix:** Use connection with timeout

**Bug #3:** Wrong answer clicked if answers reordered
- **Cause:** Positions cached from first scan
- **Fix:** Re-scan positions for each new question

---

## 19. FAQ

**Q: Does this work with all test platforms?**
A: Should work with most browser-based tests. May need adjustments for specific UIs.

**Q: Can it detect trick questions?**
A: Only if the correct answer is in the database. It doesn't "understand" questions.

**Q: What if question wording is slightly different?**
A: Fuzzy matching handles variations up to ~15% difference.

**Q: Can I use this in an exam?**
A: This is for practice/study purposes only. Using in real exams may violate academic integrity policies.

**Q: Does it work offline?**
A: Yes! All processing is local. No internet required.

**Q: How accurate is it?**
A: Depends on database quality and OCR accuracy. Typically 85-95% with good data.

**Q: Can multiple people use same database?**
A: Yes! Share the `test_questions.db` file or use Supabase for real-time collaboration.

**Q: What if the test has images in questions?**
A: Currently text-only. Image-based questions not supported.

---

## 20. Support & Resources

### Getting Help

1. **Check this reference document first**
2. **Review troubleshooting section**
3. **Enable debug mode and check logs**
4. **Inspect database contents**

### Useful Links

- **Tesseract OCR:** https://github.com/tesseract-ocr/tesseract
- **OpenCV Docs:** https://docs.opencv.org/
- **PyAutoGUI Guide:** https://pyautogui.readthedocs.io/
- **FuzzyWuzzy:** https://github.com/seatgeek/fuzzywuzzy
- **SQLite Tutorial:** https://www.sqlitetutorial.net/

### Code Comments Convention

```python
# Single-line comment for brief explanation

"""
Multi-line docstring for functions
Explains parameters, return values, and behavior
"""

# TODO: Feature to implement later
# FIXME: Bug that needs fixing
# HACK: Temporary workaround
# NOTE: Important information
```

---

## 21. Version History

### MVP 1.0 (Current)
- ✅ Core monitoring system
- ✅ OCR with Serbian support
- ✅ Fuzzy matching
- ✅ Auto-correction
- ✅ SQLite database
- ✅ Activity logging
- ✅ Basic statistics

### Planned 1.1
- Auto UI detection
- Multi-monitor support
- Improved selection detection
- Keyboard shortcuts
- Configuration file

### Planned 2.0
- Machine learning integration
- Cloud sync
- Advanced statistics
- Answer confidence scoring
- Mobile app support

---

## 22. Contributing

### Code Style

Follow PEP 8 with these specifics:
- **Indentation:** 4 spaces
- **Line length:** 100 characters max
- **Naming:**
  - Classes: `PascalCase`
  - Functions: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_leading_underscore`

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/auto-ui-detection

# Make changes and commit
git add .
git commit -m "Add automatic UI element detection"

# Push and create PR
git push origin feature/auto-ui-detection
```

### Testing Requirements

All new features must include:
1. Unit tests
2. Integration test
3. Manual testing checklist
4. Documentation update

---

## 23. License & Disclaimer

### License
MIT License - Free to use, modify, and distribute.

### Disclaimer
This software is for educational purposes only. Use responsibly and in accordance with your institution's academic integrity policies. The authors are not responsible for misuse.

---

## 24. Quick Reference Card

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| ESC | Cancel current operation |
| N | Force next question (planned) |

### File Locations
| File | Purpose |
|------|---------|
| `auto_test_corrector.py` | Main program |
| `test_questions.db` | SQLite database |
| `qa_data.json` | Import source (optional) |
| `reference.md` | This document |

### Important Thresholds
| Parameter | Value | Location |
|-----------|-------|----------|
| Fuzzy match | 85% | `match_question()` |
| Screen change | 5 | `wait_for_user_answer()` |
| Monitor interval | 0.5s | `monitor_loop()` |
| Blue selection | 10% | `is_answer_selected()` |
| Dark selection | 30% | `is_answer_selected()` |

### Database Tables
- `questions` - Question bank
- `answers` - Answer options
- `correction_log` - Correction history

---

**END OF REFERENCE DOCUMENT**

For questions or issues, please refer to the troubleshooting section or contact support.

Last updated: 2025-10-24