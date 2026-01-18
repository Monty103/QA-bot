# IMPORTANT CLARIFICATION

## The Actual Purpose

This script is **NOT a program with a GUI**.

It is a **background helper script** for online questionnaires.

### How It Works

1. **User opens an online questionnaire** in their browser
2. **Script runs in background** (invisible, no window)
3. **User takes the test** normally
4. **If user clicks WRONG answer** → Script auto-clicks the correct one
5. **If user clicks RIGHT answer** → Script does nothing
6. **User never sees** the script working (it's invisible)

### Key Characteristics

✅ **Background operation** - No visible GUI window
✅ **Automatic** - Starts and runs without user interaction
✅ **Read-only database** - NEVER writes to database
✅ **Invisible helper** - User doesn't notice it working
✅ **Hands-off** - No buttons to click, no setup required

## What's Wrong Currently

The current code is implemented as a **GUI Application**, which is **WRONG**:

❌ Shows a GUI window
❌ Requires clicking buttons ("Setup", "Start")
❌ Displays status and statistics
❌ Writes corrections to database
❌ Imports data into database
❌ Shows visible updates

## What Needs to Change

### 1. Remove GUI Entirely
- Delete all Tkinter code
- Delete all window/button/display code
- No visible interface at all

### 2. Make Database Read-Only
- Remove `log_correction()` calls
- Remove `create_question()` calls
- Remove `add_answer()` calls
- Remove `import_existing_data()` calls
- Keep ONLY: `get_all_questions()`, `search_questions()`, `get_answers()`

### 3. Create Background Helper
- Auto-start monitoring loop
- Silent operation (no output unless error)
- Continuously check for wrong clicks
- Auto-correct when detected
- Stop with Ctrl+C

### 4. Accept Configuration
- Command-line arguments, or
- Configuration file, or
- Auto-detection of questionnaire window

## Example Usage (Correct)

```bash
# Start the helper
python src/helper.py --config docs/config.json

# Or with inline arguments
python src/helper.py --question-region "100:50:800:100" \
                     --answers-region "100:200:800:300"

# [Script runs silently]
# [User opens questionnaire and takes test]
# [Script auto-corrects wrong answers invisibly]

# Stop the helper
Ctrl+C
```

## Documentation

Read these to understand:

- **[docs/ACTUAL_PURPOSE.md](docs/ACTUAL_PURPOSE.md)** - Detailed explanation
- **[docs/REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md)** - Step-by-step plan
- **[docs/INDEX.md](docs/INDEX.md)** - Documentation index

## Database Access Rules

### Allowed (Read-Only) ✅
```python
db.get_all_questions()      # Load questions
db.search_questions(text)   # Find question
db.get_question(id)         # Get by ID
db.get_answers(id)          # Get correct answers
```

### NOT Allowed (Write Operations) ❌
```python
db.log_correction(...)      # NO - read-only
db.create_question(...)     # NO - read-only
db.add_answer(...)          # NO - read-only
db.import_existing_data()   # NO - read-only
```

## Current vs Correct

| Aspect | Current (WRONG) | Correct (RIGHT) |
|--------|---|---|
| What it is | GUI Application | Background Script |
| Visible | GUI window pops up | Completely invisible |
| Startup | Click buttons | Automatic |
| Database | Read + Write | Read-only |
| User interaction | Required | None |
| Configuration | GUI buttons | CLI args / config file |

## Summary

- **Type**: Background helper script
- **Operation**: Invisible and automatic
- **Database**: Read-only, never writes
- **Purpose**: Auto-correct wrong answers on questionnaires
- **User view**: Script runs silently in background

This requires **major refactoring** (10-15 hours) to convert from a GUI application to a background helper script.

---

**See docs/ACTUAL_PURPOSE.md and docs/REFACTORING_PLAN.md for details.**
