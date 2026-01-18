# Automatic Helper Script - Detailed Plan

## Overview

Based on the reference screenshots, this document outlines how the automatic helper script should work.

---

## Questionnaire Analysis

### Layout Structure

From the reference images, the questionnaire has:

```
┌─────────────────────────────────────────────────────────┐
│  Header: "Pitanja za teorijski ispit -vežbanje"        │
├─────────────────────────────────────────────────────────┤
│  [Question Counter] "Pitanje: 6/8"                      │ ← IGNORE
│  "Broj pitanja: 1"                                      │ ← IGNORE
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ Question Text:                                  │  │
│  │ "Svako fizičko lice vlastnik, odnosno..."      │  │ ← READ THIS
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ○ Answer 1: "nije dužan da obezbedi..."        │  │ ← DETECT & CLICK
│  │ ○ Answer 2: "dužan je da obezbedi..."          │  │
│  │ ○ Answer 3: "dužan je da obezbedi..."          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Previous] [Next]    [Submit] [More Buttons] [Exit]  │ ← IGNORE
└─────────────────────────────────────────────────────────┘
```

### Screen Regions to Monitor

#### 1. Question Region
- **Location**: Upper-middle area
- **Content**: Question text in Serbian/English
- **Detection**: Look for text field after "Broj pitanja: X"
- **Action**: Extract via OCR

#### 2. Answer Region
- **Location**: Below question, middle area
- **Content**: Radio buttons with answer options
- **Detection**: Multiple radio button options (○ symbol)
- **Action**: Detect clicks, identify position, click correct

#### 3. Regions to IGNORE
- ❌ Question counter "Pitanje: 6/8" (top-left)
- ❌ "Broj pitanja: 1" counter
- ❌ "Obeležite pitanje" checkbox (top-right)
- ❌ "Prikaži odgovor" button (center)
- ❌ "Izveštaj" button (right)
- ❌ "Izlax" button (right)
- ❌ Navigation buttons (Previous/Next/etc)

---

## Automatic Detection Strategy

### 1. Question Region Auto-Detection

**Method**: Template matching + OCR confidence

```python
# Step 1: Look for question area
# - Search for "Broj pitanja:" text
# - Question text should be nearby
# - Use OCR on that region

# Step 2: Define question region dynamically
# - Find the text block after "Broj pitanja:"
# - Region should be ~850px wide, ~80px tall
# - Positioned around middle-top of screen

# Step 3: Monitor for changes
# - Re-read question text every 0.5 seconds
# - Detect when question changes (new question number)
```

**Coordinates (Approximate from screenshot)**:
- **X**: ~30 (left edge)
- **Y**: ~150 (below counter)
- **Width**: ~800px
- **Height**: ~80px

### 2. Answer Region Auto-Detection

**Method**: Radio button detection

```python
# Step 1: Find radio buttons (○ symbols)
# - Look for circular shapes below question
# - Radio buttons appear as empty circles

# Step 2: Extract answer positions
# - For each radio button found:
#   - Record center position (for clicking)
#   - Extract text to the right of button
#   - Check if button is selected (filled vs empty)

# Step 3: Monitor for clicks
# - Track mouse position changes
# - Detect when user clicks in answer region
# - Identify which answer was clicked
```

**Coordinates (Approximate from screenshot)**:
- **X**: ~25 (left edge)
- **Y**: ~200 (below question)
- **Width**: ~750px
- **Height**: ~120px (varies by number of answers)

---

## Operational Flow

### Phase 1: Initialization

```
1. Script starts
2. Wait for user to open questionnaire
3. Auto-detect answer region (look for radio buttons)
4. Load all questions from database into memory
5. Begin monitoring loop
```

### Phase 2: Per-Question Monitoring Loop (Every 0.5 seconds)

```python
while questionnaire_open():
    # STEP 1: Screenshot
    screenshot = capture_screen()

    # STEP 2: Read Question
    question_text = ocr_extract_question(screenshot)

    # STEP 3: Lookup Question
    if question_text != previous_question:
        db_question = database.search_questions(question_text)
        correct_answers = [a for a in db_question.answers if a.is_correct]
        previous_question = question_text

    # STEP 4: Monitor for Clicks
    current_mouse_pos = get_mouse_position()
    if mouse_moved_in_answer_region(current_mouse_pos):
        user_clicked = True
        clicked_answer = extract_clicked_answer_text(screenshot)

    # STEP 5: Check if Wrong
    if user_clicked:
        if clicked_answer not in correct_answers:
            # WRONG CLICK - AUTO-CORRECT
            correct_answer_position = find_radio_position(correct_answers[0])
            click(correct_answer_position)
            user_clicked = False
        else:
            # RIGHT CLICK - DO NOTHING
            user_clicked = False

    # STEP 6: Sleep
    sleep(0.5)
```

---

## Key Components to Implement

### 1. OCR Question Extraction

**File**: `src/question_reader.py`

```python
class QuestionReader:
    def extract_question(self, screenshot, region):
        """Extract question text from screenshot"""
        # Crop to question region
        question_area = crop_image(screenshot, region)

        # Preprocess image
        preprocessed = preprocess_for_ocr(question_area)

        # Extract text with Tesseract
        text = pytesseract.image_to_string(
            preprocessed,
            lang='srp+eng',
            config='--oem 1 --psm 6'
        )

        return text.strip()
```

### 2. Radio Button Detection

**File**: `src/radio_detector.py`

```python
class RadioButtonDetector:
    def find_radio_buttons(self, screenshot, region):
        """Find all radio button positions and states"""
        answers_area = crop_image(screenshot, region)

        # Detect circles (radio buttons)
        circles = detect_circles(answers_area)

        # For each circle, extract:
        answers = []
        for circle in circles:
            x, y = circle.center

            # Is it selected? (filled vs empty)
            is_selected = check_circle_filled(circle)

            # Extract text to the right
            text_region = crop_text_area(answers_area, x, y)
            text = ocr_extract_text(text_region)

            answers.append({
                'position': (x, y),
                'text': text,
                'selected': is_selected
            })

        return answers
```

### 3. Click Detection

**File**: `src/click_monitor.py`

```python
class ClickMonitor:
    def __init__(self, answer_region):
        self.answer_region = answer_region
        self.last_mouse_pos = None
        self.click_detected = False
        self.clicked_position = None

    def check_click(self):
        """Check if user clicked in answer region"""
        current_pos = get_mouse_position()

        # Check if mouse is in answer region
        if in_region(current_pos, self.answer_region):
            # Check if position changed (click movement)
            if self.last_mouse_pos and distance(current_pos, self.last_mouse_pos) > 5:
                self.click_detected = True
                self.clicked_position = current_pos

        self.last_mouse_pos = current_pos
        return self.click_detected
```

### 4. Database Read-Only Wrapper

**File**: `src/question_database.py`

```python
class QuestionDatabase:
    def __init__(self, db_path):
        self.db = HybridDatabaseManager(sqlite_path=db_path, use_api=True)

    def load_all_questions(self):
        """Load all questions into memory (one-time)"""
        return self.db.get_all_questions(include_answers=True)

    def find_question(self, question_text):
        """Find question by fuzzy matching"""
        return self.db.search_questions(question_text, threshold=85)

    def get_correct_answers(self, question_id):
        """Get correct answers for question"""
        q = self.db.get_question(question_id)
        return [a for a in q['answers'] if a['is_correct']]

    # NO WRITE METHODS - READ ONLY!
```

### 5. Main Helper Script

**File**: `src/helper.py`

```python
#!/usr/bin/env python3
"""Automatic questionnaire helper - background script"""

import time
import argparse
from question_reader import QuestionReader
from radio_detector import RadioButtonDetector
from click_monitor import ClickMonitor
from question_database import QuestionDatabase

def main(config_path):
    # Load config
    config = load_config(config_path)

    # Initialize components
    db = QuestionDatabase(config['database_file'])
    reader = QuestionReader()
    detector = RadioButtonDetector()
    monitor = ClickMonitor(config['answer_region'])

    # Load questions once
    print("[*] Loading questions from database...")
    all_questions = db.load_all_questions()

    # Define regions
    question_region = config['question_region']
    answer_region = config['answer_region']

    current_question = None
    correct_answers = []
    user_clicked = False

    print("[*] Starting questionnaire helper...")
    print("[*] Question region:", question_region)
    print("[*] Answer region:", answer_region)

    try:
        while True:
            # Capture screen
            screenshot = pyautogui.screenshot()

            # Read question
            question_text = reader.extract_question(screenshot, question_region)

            # If question changed, lookup answers
            if question_text and question_text != current_question:
                result = db.find_question(question_text)
                if result:
                    current_question = question_text
                    correct_answers = db.get_correct_answers(result[0]['id'])
                    print(f"[*] Question: {question_text[:50]}...")
                    print(f"[*] Correct answers: {correct_answers}")

            # Find radio buttons
            answers = detector.find_radio_buttons(screenshot, answer_region)

            # Check for clicks
            if monitor.check_click() and not user_clicked:
                user_clicked = True
                clicked_pos = monitor.clicked_position

                # Find which answer was clicked
                clicked_answer = find_closest_answer(clicked_pos, answers)
                print(f"[!] User clicked: {clicked_answer['text']}")

                # Check if it's wrong
                if clicked_answer['text'] not in correct_answers:
                    # WRONG - AUTO-CORRECT
                    correct_btn = find_answer_by_text(correct_answers[0], answers)
                    click_position = correct_btn['position']

                    print(f"[!] Wrong! Auto-correcting to: {correct_answers[0]}")
                    pyautogui.click(click_position[0], click_position[1])
                    time.sleep(0.2)  # Delay for button effect
                else:
                    print(f"[✓] Correct! (no action needed)")

                user_clicked = False

            # Sleep for monitoring interval
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("[*] Helper stopped")
```

---

## Configuration Structure

**docs/config.json** (for automatic operation):

```json
{
  "tesseract_path": "C:\\dt\\Tesseract-OCR\\tesseract.exe",
  "database_file": "data/test_questions.db",
  "api_url": "https://question-database-api.onrender.com",
  "use_api": true,

  "monitoring_interval_seconds": 0.5,

  "question_region": {
    "x": 30,
    "y": 150,
    "width": 800,
    "height": 80
  },

  "answer_region": {
    "x": 25,
    "y": 200,
    "width": 750,
    "height": 120
  },

  "ocr_language": "srp+eng",
  "fuzzy_match_threshold": 85
}
```

---

## Answer Type Handling

### Single-Select (Radio Buttons - Current)

```
○ Answer 1
○ Answer 2  ← User clicks here (wrong)
○ Answer 3

Script detects:
- Circle shape at position (x,y)
- Text: "Answer 2"
- Looks up in database
- Finds correct answer is "Answer 3"
- Clicks radio button for "Answer 3"
```

### Multi-Select (Checkboxes - Future)

```
☐ Answer 1
☑ Answer 2  ← User clicks here (partial)
☐ Answer 3

Script detects:
- Checkbox shape
- Multiple correct answers possible
- Clicks all correct checkboxes
```

---

## Detection Algorithm Details

### Question Change Detection

```python
def detect_question_change(new_text, old_text, threshold=85):
    """Detect if question actually changed"""
    similarity = fuzz.ratio(new_text.lower(), old_text.lower())

    if similarity < threshold:
        return True  # Different question
    return False     # Same question
```

### Click Position Analysis

```python
def identify_clicked_answer(mouse_pos, answers):
    """Find which answer was clicked"""
    closest = None
    min_distance = float('inf')

    for answer in answers:
        dist = distance(mouse_pos, answer['position'])
        if dist < min_distance:
            min_distance = dist
            closest = answer

    return closest if min_distance < 50 else None
```

### Correct Answer Clicking

```python
def click_correct_answer(correct_text, answers):
    """Find and click correct answer"""
    for answer in answers:
        if fuzzy_match(answer['text'], correct_text, threshold=80):
            # Found it - click the radio button position
            x, y = answer['position']
            pyautogui.click(x, y)
            time.sleep(0.2)  # Wait for UI response
            return True

    return False  # Couldn't find answer
```

---

## Region Calibration

### Automatic Region Detection (Future Enhancement)

```python
def auto_detect_regions(screenshot):
    """Auto-detect question and answer regions"""

    # Find "Broj pitanja:" text
    pitanja_pos = find_text(screenshot, "Broj pitanja:")

    if pitanja_pos:
        # Question region is below this
        question_region = {
            'x': 30,
            'y': pitanja_pos.y + 50,
            'width': 800,
            'height': 80
        }

        # Find radio buttons below question
        radio_buttons = find_circles(screenshot)

        if radio_buttons:
            # Answer region contains all buttons
            answer_region = {
                'x': 25,
                'y': min(b.y for b in radio_buttons) - 10,
                'width': 750,
                'height': max(b.y for b in radio_buttons) - min(b.y for b in radio_buttons) + 50
            }

            return question_region, answer_region

    return None, None
```

### Manual Region Configuration

```bash
# Run with explicit regions
python src/helper.py --question-region "30:150:800:80" \
                     --answer-region "25:200:750:120"

# Or use config file
python src/helper.py --config docs/config.json
```

---

## File Structure

```
src/
├── helper.py                    ← Main background script
├── question_reader.py           ← OCR question extraction
├── radio_detector.py            ← Radio button detection & clicking
├── click_monitor.py             ← Click monitoring
├── question_database.py         ← Read-only database wrapper
├── answer_detector.py           ← Answer text extraction (existing)
├── shape_detector.py            ← Shape detection (existing)
├── ocr_processor.py             ← OCR preprocessing (simplified)
├── remote_database.py           ← API client (unchanged)
├── hybrid_database.py           ← DB manager (read-only usage)
└── cpp_extensions/              ← Performance optimization (optional)

docs/
├── config.json                  ← Configuration with regions
├── AUTOMATIC_HELPER_PLAN.md     ← This file
└── (other documentation)
```

---

## Success Criteria

The script is working correctly when:

✅ No GUI window appears
✅ Script runs silently in background
✅ Questions are read correctly via OCR
✅ Correct answers are found in database
✅ User clicks are detected within 0.5 seconds
✅ Wrong answers are auto-corrected instantly
✅ Right answers are left alone
✅ Database is never modified
✅ Works with single-select (radio buttons)

---

## Implementation Phases

### Phase 1: Core Components
- ✓ Question reader (OCR)
- ✓ Radio button detector
- ✓ Click monitor
- ✓ Database wrapper (read-only)

### Phase 2: Main Script
- ✓ Background helper script
- ✓ Monitoring loop
- ✓ Auto-correction logic

### Phase 3: Configuration
- ✓ Region configuration file
- ✓ CLI argument support
- ✓ Auto-detection (optional)

### Phase 4: Testing & Deployment
- ✓ Unit tests for components
- ✓ Integration testing
- ✓ Real questionnaire testing

---

## Estimated Timeline

- Phase 1: 4-5 hours
- Phase 2: 3-4 hours
- Phase 3: 2-3 hours
- Phase 4: 2-3 hours

**Total: 11-15 hours**

---

**Status**: Plan Created ✓
**Based on**: Reference screenshots analysis
**Ready for**: Implementation
