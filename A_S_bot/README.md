# Auto Test Corrector - Enhanced v2.0

🤖 **Fully Automatic Web-Based Questionnaire Correction System**

This system monitors your screen in real-time, detects when you select answers in a web-based questionnaire, validates your selections against a local database, and **automatically corrects wrong answers** by clicking the correct ones.

---

## ✨ Key Features

- ✅ **Fully Automatic Operation** - Just select answers, the system handles the rest
- ✅ **Smart Question Type Detection** - Automatically detects single-answer (radio ○) vs multi-answer (checkbox □) questions
- ✅ **OCR with Serbian Support** - Reads both Serbian (latinica) and English text
- ✅ **Fuzzy Matching** - Handles OCR errors with 85%+ similarity matching
- ✅ **Only Corrects Wrong Answers** - If you select correctly, no action is taken
- ✅ **Comprehensive Statistics** - Tracks corrections, accuracy, and session data
- ✅ **Database Integration** - SQLite database with JSON import support

---

## 📋 Requirements

### Software Dependencies

```bash
# Python 3.8 or higher
python --version

# Install Python packages
pip install opencv-python
pip install pytesseract
pip install pyautogui
pip install pillow
pip install fuzzywuzzy
pip install python-Levenshtein
```

### Tesseract OCR Setup

1. **Download Tesseract OCR:**
   - Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - Install to: `C:\dt\Tesseract-OCR\` (or update `config.json`)

2. **Download Serbian Language Pack:**
   - Download `srp.traineddata` from: https://github.com/tesseract-ocr/tessdata
   - Place in: `C:\dt\Tesseract-OCR\tessdata\`

3. **Verify Installation:**
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r"C:\dt\Tesseract-OCR\tesseract.exe"
   print(pytesseract.get_languages())  # Should include 'srp' and 'eng'
   ```

---

## 🚀 Quick Start Guide

### Step 1: Prepare Your Database

You can import questions from a JSON file. The JSON format should be:

```json
{
  "questions": [
    {
      "question": "Koji je glavni grad Srbije?",
      "question_type": "single",
      "required_correct_answers": 1,
      "correct_answers": ["Beograd"],
      "wrong_answers": ["Niš", "Novi Sad", "Kragujevac"]
    },
    {
      "question": "Izaberite sve primarne boje",
      "question_type": "multi",
      "required_correct_answers": 3,
      "correct_answers": ["Crvena", "Plava", "Žuta"],
      "wrong_answers": ["Zelena", "Narandžasta", "Ljubičasta"]
    }
  ]
}
```

Save this as `qa_data.json` in the same folder as `main.py`.

### Step 2: Launch the Application

```bash
python main.py
```

### Step 3: Setup Regions (One-Time)

1. Click **"⚙️ Setup Regions"**
2. **Step 1:** Drag to select the **question area** on your screen
3. **Step 2:** Drag to select the **answers area** on your screen
4. Regions are now configured!

### Step 4: Start Monitoring

1. Click **"🚀 Start Monitoring"**
2. Navigate to your web questionnaire
3. Take the test normally by clicking answers
4. The system will:
   - ✅ **Do nothing** if you select the correct answer
   - 🔧 **Auto-correct** if you select a wrong answer

---

## 🎯 How It Works

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│  1. Screen Monitoring (Background Thread)          │
│     - Captures question region every 0.5s           │
│     - Detects when new question appears             │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  2. OCR Processing                                  │
│     - Extracts question text (Serbian + English)    │
│     - Cleans bubble characters (○, □, M, etc.)      │
│     - Fuzzy matches against database (85%+)         │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  3. Answer Detection                                │
│     - Finds green blocks (correct answers)          │
│     - Finds red blocks (wrong answers)              │
│     - Detects box shape (○ = single, □ = multi)     │
│     - Extracts and cleans answer text               │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  4. User Selection Monitoring                       │
│     - Waits for screen change in answers region     │
│     - Detects which answer(s) user clicked          │
│     - Analyzes color changes (blue/dark = selected) │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│  5. Validation & Auto-Correction                    │
│     - Compares user selection with database         │
│     - If CORRECT: ✅ Log success, do nothing        │
│     - If WRONG: 🔧 Auto-click correct answer(s)     │
│     - Updates statistics                            │
└─────────────────────────────────────────────────────┘
```

### Question Type Detection

The system automatically detects question type in **two ways**:

1. **Visual Shape Analysis:**
   - Analyzes selection boxes using edge detection
   - **Circular shapes (○)** → Single-answer (radio button)
   - **Square shapes (□)** → Multi-answer (checkbox)

2. **Database Information:**
   - Uses `question_type` field from database
   - Uses `required_correct_answers` count

### Auto-Correction Logic

**For Single-Answer Questions (Radio):**
- User clicks wrong answer
- System immediately clicks the correct answer
- Radio button auto-unselects the wrong one

**For Multi-Answer Questions (Checkbox):**
- User clicks wrong answer(s)
- System unclicks all wrong selections
- System clicks all correct answers
- All required answers are now selected

---

## ⚙️ Configuration

Edit [config.json](config.json) to customize:

| Setting | Description | Default |
|---------|-------------|---------|
| `tesseract_path` | Path to Tesseract executable | `C:\dt\Tesseract-OCR\tesseract.exe` |
| `fuzzy_match_threshold` | Minimum similarity % for matching | `85` |
| `monitoring_interval_seconds` | Screenshot capture interval | `0.5` |
| `correction_delay_seconds` | Delay between auto-clicks | `0.2` |
| `circle_min_circularity` | Threshold for detecting radio buttons | `0.7` |
| `square_max_circularity` | Threshold for detecting checkboxes | `0.5` |
| `enable_auto_correction` | Enable/disable auto-correction | `true` |

---

## 📊 Database Schema

The system uses SQLite with three tables:

### `questions` Table
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    question_type TEXT DEFAULT 'single',  -- 'single' or 'multi'
    required_answers INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `answers` Table
```sql
CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN,  -- 1 = correct, 0 = wrong
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
```

### `correction_log` Table
```sql
CREATE TABLE correction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    question_text TEXT,
    wrong_answer TEXT,
    correct_answer TEXT,
    correction_successful BOOLEAN
);
```

---

## 🔧 Troubleshooting

### OCR Not Working
- Verify Tesseract installation: `pytesseract.get_languages()`
- Check Serbian language pack is installed in `tessdata/`
- Try increasing image contrast in question region
- Ensure question text is clearly visible

### Wrong Question Matching
- Lower `fuzzy_match_threshold` in [config.json](config.json) (e.g., to 80)
- Check question text in database matches OCR output
- Review cleaned text in activity log

### Answers Not Detected
- Ensure answer blocks are clearly green/red colored
- Adjust color detection ranges in `AnswerBlockDetector` class
- Try selecting a larger answers region
- Check if blocks meet minimum size requirements (40x10 pixels)

### Auto-Correction Not Triggering
- Verify `enable_auto_correction` is `true` in config
- Check that database has correct answers marked (`is_correct = 1`)
- Ensure fuzzy matching finds the correct answer (>85% similarity)
- Look for error messages in activity log

### Selection Not Detected
- System looks for color changes (blue/dark tones)
- Ensure selected answers visually change color
- May need to adjust `is_answer_selected()` thresholds
- Try increasing `click_detection_threshold` in config

---

## 📈 Statistics & Logging

The GUI displays real-time statistics:
- **Total Questions:** Questions encountered in current session
- **Correct First Try:** Questions you answered correctly
- **Auto-Corrected:** Wrong answers that were automatically fixed
- **Success Rate:** Percentage of correct first-try answers

All corrections are logged to the database for later analysis.

---

## 🛡️ Safety Features

- **Auto-Correction Flag:** Prevents correction loops
- **Fuzzy Matching:** Handles OCR errors gracefully
- **Database Logging:** All corrections are tracked
- **Emergency Stop:** Click "⏹️ Stop" to halt monitoring instantly
- **Thread Safety:** GUI updates use thread-safe methods

---

## 🔄 Workflow Example

1. **Question Appears:**
   ```
   Question: "Koji je glavni grad Srbije?"
   Answers:
   ○ Niš
   ○ Beograd  ← Correct
   ○ Novi Sad
   ```

2. **You Click:** "Niš" (wrong answer)

3. **System Detects:**
   ```
   ❌ Wrong answer: Niš
   🔧 Auto-correcting to: Beograd
   ```

4. **System Auto-Clicks:** "Beograd"

5. **Result:**
   ```
   ✅ Correction successful!
   Statistics: +1 Auto-Corrected
   ```

---

## 📁 File Structure

```
A_S_bot/
├── main.py                      # Main application
├── config.json                  # Configuration file
├── test_questions.db            # SQLite database (auto-created)
├── qa_data.json                 # Optional: Import source
├── README.md                    # This file
├── reference.md                 # Technical reference
├── reference_MVP.md             # MVP documentation
└── reference_prog/              # Reference implementations
    ├── semi-manual.py           # Semi-automatic version
    └── ultimate_database_qa_gui.py  # Database builder
```

---

## 🚧 Known Limitations

- Requires visible answer blocks with green/red colors
- OCR accuracy depends on text clarity and font
- Screen must remain visible (no minimizing during test)
- Mouse must not be moved manually during auto-correction
- Best results with consistent questionnaire UI

---

## 🔮 Future Enhancements

- [ ] Automatic UI element detection (no manual region setup)
- [ ] Machine learning for better question matching
- [ ] Support for typed answers (not just selection)
- [ ] Multi-monitor support
- [ ] Cloud database sync (Supabase integration)
- [ ] Browser extension version
- [ ] Mobile app support

---

## 📝 Tips for Best Results

1. **Database Preparation:**
   - Ensure questions in database match actual test text
   - Include all possible answer variations
   - Mark correct answers accurately

2. **Region Selection:**
   - Select tight regions around question/answers
   - Avoid including unnecessary UI elements
   - Ensure text is fully visible

3. **During Test:**
   - Don't move mouse during auto-correction
   - Wait for correction to complete before next question
   - Monitor activity log for issues

4. **Performance:**
   - Close unnecessary applications
   - Ensure good screen visibility
   - Use stable internet connection

---

## 📄 License

This project is for educational purposes. Use responsibly and in accordance with your institution's policies.

---

## 🆘 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review activity log for error messages
3. Verify configuration settings
4. Check database statistics for data completeness

---

**Version:** 2.0
**Last Updated:** 2025
**Language Support:** Serbian (Latinica) + English
