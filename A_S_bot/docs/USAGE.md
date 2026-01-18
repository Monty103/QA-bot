# Automatic Questionnaire Helper - Usage Guide

## Quick Start

1. **Start the helper script:**
   ```bash
   python src/main.py --config docs/config.json
   ```

2. **The script will:**
   - Load questions from the database
   - Monitor the screen for questions
   - Detect clicks in the answer region
   - Auto-correct wrong answers

3. **Stop the script:**
   - Press `Ctrl+C`

## Configuration

The helper reads settings from `docs/config.json`:

### Region Coordinates
These define where questions and answers appear on screen:
- `question_region`: Where the question text is displayed
- `answer_region`: Where the answer options are displayed

**Current coordinates (from screenshot analysis):**
- Question: `x=30, y=150, width=800, height=80`
- Answer: `x=25, y=200, width=750, height=120`

### OCR Settings
- `ocr_language`: "srp+eng" (Serbian + English)
- `fuzzy_match_threshold`: 85 (how closely OCR must match database)

### Detection Settings
- `monitoring_interval_seconds`: 0.5 (how often to re-read question)
- `click_detection_threshold`: 5 (sensitivity for click detection)
- `correction_delay_seconds`: 0.2 (delay between auto-clicks)

### Debug Mode
Set `show_debug_messages: true` to see:
- Raw OCR output vs cleaned text
- Detailed circle detection information

## Troubleshooting

### Issue: "Question not found in database"

**Possible causes:**
1. The question region is capturing headers/titles instead of actual questions
2. The OCR is misreading the text
3. The question isn't in the database

**Solutions:**
1. Enable debug mode to see what OCR is reading:
   ```json
   "show_debug_messages": true
   ```
2. Adjust the question region coordinates if needed
3. Check database contents to ensure question exists

### Issue: "No radio buttons detected"

**Possible causes:**
1. The answer region coordinates are wrong
2. Radio buttons are styled differently than expected
3. The buttons aren't visible on screen

**Solutions:**
1. The script now tries multiple detection parameters automatically
2. Check console output for debug messages showing detection attempts
3. Verify the answer region contains the radio buttons

### Issue: pynput threading errors

**Fixed in current version** - Now using proper `on_click` events instead of `on_move`

### Issue: API timeout errors

**These are normal** - The script works offline using the local SQLite database. API connectivity is optional and provides cloud backup only.

## How It Works

### 1. Question Detection
- Takes screenshot every 0.1 seconds
- Reads question text via OCR every 0.5 seconds
- Cleans text to remove headers ("Pitanja za teorijski ispit", etc.)
- Matches against database using fuzzy matching (85% similarity)

### 2. Radio Button Detection
- Uses Hough Circle Detection with multiple parameter sets
- Tries increasingly relaxed parameters if buttons aren't found
- Extracts answer text using OCR
- Detects filled vs empty state

### 3. Click Monitoring
- Listens for mouse clicks using pynput
- Only triggers for clicks inside answer region
- Identifies which answer was clicked

### 4. Auto-Correction
- Compares clicked answer to correct answers from database
- Only auto-corrects if answer is wrong
- Clicks correct answer automatically
- Tracks statistics (corrections made, questions processed)

## Adjusting Region Coordinates

If the default coordinates don't work for your questionnaire:

1. Take a screenshot of the questionnaire
2. Use an image editor to find pixel coordinates
3. Update `config.json`:
   ```json
   "question_region": {
     "x": <left edge>,
     "y": <top edge>,
     "width": <width in pixels>,
     "height": <height in pixels>
   }
   ```

## Database

The helper uses a **read-only** database connection:
- Does NOT write corrections to the database
- Does NOT log statistics
- Only reads questions and answers

Questions are loaded into memory at startup for fast lookup.

## Statistics

When you stop the script (Ctrl+C), you'll see:
- Total questions processed
- Total corrections made
- Session duration
