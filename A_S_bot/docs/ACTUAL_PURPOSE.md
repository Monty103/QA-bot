# Actual Purpose - Auto Test Helper Script

## What This Script Actually Is

**Not a program.** This is a **background helper script** for questionnaires.

### Core Function
The script runs invisibly in the background while the user has a questionnaire open. It:
1. **Reads** questions from the screen (via OCR)
2. **Looks up** correct answers in the database/server
3. **Monitors** user clicks in real-time
4. **Auto-corrects** ONLY if user clicks the wrong answer
5. **Never writes** to the database

---

## How It Works

### User's Perspective
1. User opens an online questionnaire
2. User clicks on answers (some may be wrong)
3. Script detects wrong clicks
4. Script automatically clicks the correct answer instead
5. User never knows the script was working (unless they look wrong!)

### Technical Flow
```
┌─────────────────────────────────────────────────┐
│ Questionnaire Open in Browser/App               │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ Script Running in Background  │
        │ (No GUI, no window)          │
        └──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    ┌────────┐  ┌──────────┐  ┌────────────┐
    │ Monitor│  │ Read OCR │  │ Read DB    │
    │ Clicks │  │ Questions│  │ Answers    │
    └────────┘  └──────────┘  └────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │ User Clicked Wrong?│
            └────────────────────┘
                   │        │
              YES  │        │  NO
                   ▼        ▼
            ┌─────────┐  ┌────────┐
            │Click    │  │Do Nothing
            │Correct  │  │
            │Answer   │  │
            └─────────┘  └────────┘
```

---

## Key Requirements

### ✅ What the Script MUST Do
1. **Run in background** - No GUI window visible
2. **Read only** - Never write to database
3. **Monitor screen** - Use OCR to read questions
4. **Detect clicks** - Monitor user mouse clicks
5. **Auto-correct** - Click correct answer if user was wrong
6. **Be invisible** - User doesn't notice it running (ideally)

### ❌ What the Script MUST NOT Do
1. **Write to database** - READ ONLY
2. **Show windows/GUI** - Background service only
3. **Write to database** - (stated twice for emphasis)
4. **Require user interaction** - Fully automatic
5. **Modify questionnaire data** - Only click selections

---

## Database Access

### Read Operations (✅ Allowed)
```python
# Get all questions
questions = db.get_all_questions()

# Search for a question
results = db.search_questions("What is...")

# Get answers for a question
answers = db.get_question(question_id)

# Get statistics (optional)
stats = db.get_statistics()
```

### Write Operations (❌ NOT ALLOWED)
```python
# DO NOT DO THIS
db.create_question(...)        # ❌ NO
db.update_question(...)        # ❌ NO
db.delete_question(...)        # ❌ NO
db.log_correction(...)         # ❌ NO (don't write logs)
db.add_answer(...)             # ❌ NO
db.update_answer(...)          # ❌ NO
```

---

## Architecture

### Current Issues (WRONG)
- ✗ Has GUI window (wrong - should be background)
- ✗ Tries to write corrections to database (wrong - read only)
- ✗ Has buttons like "Start Monitoring" (wrong - should auto-start)
- ✗ Tries to create/import questions (wrong - read only)

### Correct Implementation (RIGHT)
- ✓ Background service (no visible window)
- ✓ Reads from database/API only
- ✓ Auto-starts monitoring
- ✓ Detects user clicks
- ✓ Auto-corrects wrong answers
- ✓ Stops only when questionnaire closes

---

## Configuration

The script needs minimal configuration:
```json
{
  "tesseract_path": "C:\\dt\\Tesseract-OCR\\tesseract.exe",
  "database_file": "data/test_questions.db",      // or API URL
  "monitoring_interval_seconds": 0.5,
  "question_region": null,                         // defined at startup
  "answers_region": null,                          // defined at startup
  "fuzzy_match_threshold": 85
}
```

---

## Monitoring Process

### Step 1: Identify Regions (One-time Setup)
User must specify:
- Question text region (where question appears on screen)
- Answers region (where answer options appear on screen)

This can be:
- Command-line arguments
- Config file
- Window title matching
- Static coordinates

### Step 2: Continuous Monitoring Loop
```python
while questionnaire_open():
    # Every 0.5 seconds:
    1. Screenshot screen
    2. Extract question text (OCR)
    3. Look up correct answers in database
    4. Check if user clicked
    5. If wrong click → click correct answer
    6. Sleep 0.5 seconds
```

### Step 3: Exit When Done
- Questionnaire closes → Script stops
- Ctrl+C pressed → Script stops
- User command → Script stops

---

## Data Flow

### Reading Process
```
User Screen
    ↓
OCR Preprocessing
    ↓
Tesseract OCR
    ↓
Question Text
    ↓
Fuzzy Match Against DB
    ↓
Correct Answers Found
    ↓
Store in Memory
```

### Correction Process
```
Monitor User Clicks
    ↓
User Clicked Option
    ↓
Compare with Correct Answers
    ↓
Is it Correct?
    ├─ YES: Do nothing
    └─ NO: Auto-click correct answer
```

---

## Integration Points

### Database/API
- **Purpose**: Read questions and correct answers
- **Operation**: Read-only
- **Frequency**: Once per new question
- **Fallback**: Local SQLite if API down

### OCR Engine
- **Purpose**: Extract text from screen
- **Tool**: Tesseract
- **Target**: Question and answer regions

### Screen Monitoring
- **Purpose**: Detect user clicks
- **Method**: Monitor mouse position changes
- **Target**: Answers region

### Click Automation
- **Purpose**: Click correct answer if user wrong
- **Tool**: PyAutoGUI
- **Action**: Only after wrong click detected

---

## File Structure for Script

```
src/
├── helper.py                    ← Main background script
├── ocr_reader.py               ← OCR functionality (read-only)
├── answer_detector.py          ← Detect clicked answer
├── database_reader.py          ← Database read-only interface
├── screen_monitor.py           ← Monitor screen and clicks
├── config.json                 ← Configuration (in docs/)
└── run_helper.py               ← Entry point script
```

---

## Execution Model

### Current (WRONG)
```
python main.py
  ↓
GUI window opens
  ↓
User clicks buttons
  ↓
Monitoring starts
  ↓
GUI stays open
```

### Correct (RIGHT)
```
python helper.py --question-region="x:y:w:h" --answers-region="x:y:w:h"
  ↓
Script starts silently
  ↓
Monitoring begins immediately
  ↓
No window visible
  ↓
Background monitoring loop
  ↓
Ctrl+C to stop (or auto-detect questionnaire close)
```

---

## Database vs Memory

### What to Store in Memory
```python
# After reading from DB once:
correct_answers = {
    "What is 2+2?": ["4"],
    "Capital of France?": ["Paris"],
    # ... etc
}

# Keep in RAM for fast lookup
# Don't re-query database for every click
```

### What NOT to Write
```python
# Never write these:
- Corrections made
- User answers
- Session logs
- Statistics
# Read-only interface only!
```

---

## Success Criteria

The script is working correctly when:

✅ No GUI window appears
✅ Script runs silently in background
✅ User can take questionnaire normally
✅ If user clicks wrong answer → Script auto-corrects
✅ If user clicks right answer → Script does nothing
✅ Database is never modified
✅ User experience is seamless

---

## Comparison: Current vs Correct

| Aspect | Current (WRONG) | Correct (RIGHT) |
|--------|-----------------|-----------------|
| Startup | GUI pops up | Runs silently |
| Operation | Manual buttons | Auto-monitoring |
| Database | Writes logs | Read-only |
| User View | Visible script | Invisible helper |
| Config | GUI setup | Command-line/config |
| Stop | Click button | Auto or Ctrl+C |

---

## Example Usage (Correct)

```bash
# Method 1: Static coordinates
python helper.py --question-x 100 --question-y 50 --question-w 800 --question-h 100 \
                 --answers-x 100 --answers-y 200 --answers-w 800 --answers-h 300

# Method 2: Config file
python helper.py --config config.json

# Method 3: Window title matching
python helper.py --window-title "Online Questionnaire"
```

---

## Next Steps

The current codebase needs significant changes:

1. **Remove GUI entirely** - main.py GUI is wrong
2. **Create background script** - helper.py for monitoring
3. **Read-only database** - Remove write operations
4. **Auto-detection** - Detect questionnaire automatically
5. **Command-line interface** - No GUI, only CLI args
6. **Silent operation** - No visible windows

This is fundamentally different from the current GUI-based implementation.

---

## Summary

**This is a helper script, not an application.**

It runs invisibly, reads questions from the screen, checks the database for correct answers, and automatically clicks the right answer if the user clicks wrong.

**Read-only. Background. Automatic. Invisible.**

---

**Status**: Purpose Clarified ✓
**Next Action**: Rewrite codebase to match this specification
