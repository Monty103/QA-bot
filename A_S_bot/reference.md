📋 PROJECT OVERVIEW
Goal: Build a real-time test monitoring system that:

Watches the screen continuously in the background
Detects when a user clicks an answer
Validates against a database of Serbian Q&A pairs
Auto-corrects wrong answers by clicking the right one
Handles "next question" navigation automatically


🎯 PHASE 1: CORE ARCHITECTURE DESIGN
1.1 Technology Stack Selection

GUI Framework: Tkinter (lightweight, proven in your code)
Screen Monitoring: PyAutoGUI + OpenCV
OCR: Tesseract with Serbian language pack
Database: SQLite (local) or Supabase (if collaboration needed)
Mouse/Keyboard Control: PyAutoGUI
Event Detection: Custom click detection + screen region monitoring

1.2 System Components
┌─────────────────────────────────────────┐
│         Control GUI (Tkinter)           │
│  [Start/Stop] [Status] [Stats] [Config] │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼────────┐   ┌──────▼───────┐
│  Screen    │   │   Database   │
│  Monitor   │   │   Manager    │
│  Thread    │   │              │
└───┬────────┘   └──────┬───────┘
    │                   │
    │    ┌──────────────┘
    │    │
┌───▼────▼─────────────────┐
│  Intelligence Engine     │
│  - OCR Processing        │
│  - Answer Validation     │
│  - Click Correction      │
└──────────────────────────┘

🔧 PHASE 2: DATABASE SETUP
2.1 Database Schema
sqlCREATE TABLE questions (
    id INTEGER PRIMARY KEY,
    question_text TEXT NOT NULL,
    question_type TEXT, -- 'single' or 'multi'
    required_answers INTEGER DEFAULT 1,
    created_at TIMESTAMP,
    confidence_score REAL
);

CREATE TABLE answers (
    id INTEGER PRIMARY KEY,
    question_id INTEGER,
    answer_text TEXT NOT NULL,
    is_correct BOOLEAN,
    confidence_score REAL,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

CREATE TABLE correction_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP,
    question_text TEXT,
    wrong_answer TEXT,
    correct_answer TEXT,
    correction_successful BOOLEAN
);
2.2 Data Import Strategy

Reuse your existing qa_data.json or Supabase data
Create import script to populate SQLite database
Add fuzzy matching support for OCR variations


🖥️ PHASE 3: SCREEN MONITORING SYSTEM
3.1 Continuous Background Monitoring
pythonclass ScreenMonitor:
    def __init__(self):
        self.monitoring = False
        self.current_question_region = None
        self.answers_region = None
        self.last_screenshot = None
        
    def start_monitoring(self):
        """Continuous background thread"""
        # Take screenshots every 0.5 seconds
        # Compare with previous to detect changes
        # Trigger OCR when changes detected
3.2 Region Detection Strategy
Two approaches:
A) User-defined regions (like your reference code):

User selects question region once at start
User selects answers region once at start
Monitor only these regions for efficiency

B) Automatic detection:

Detect UI elements automatically
Find answer buttons by color/shape
Identify "Next Question" button

Recommendation: Start with A (user-defined), add B later

🎯 PHASE 4: CLICK DETECTION & INTERCEPTION
4.1 Click Detection Methods
Method 1: Mouse Position Monitoring
pythonimport pyautogui
import time

def monitor_clicks():
    last_pos = pyautogui.position()
    while monitoring:
        current_pos = pyautogui.position()
        if current_pos != last_pos:
            # Check if click occurred in answers region
            if is_in_answers_region(current_pos):
                detect_clicked_answer(current_pos)
        time.sleep(0.05)
Method 2: Screen Change Detection
pythondef detect_answer_selection():
    before = capture_answers_region()
    time.sleep(0.1)
    after = capture_answers_region()
    
    if images_differ(before, after):
        # Answer was clicked
        return extract_clicked_answer(after)
```

### 4.2 Answer Validation Flow
```
User clicks answer
    ↓
Detect click/change
    ↓
Extract clicked answer text (OCR)
    ↓
Compare with database
    ↓
If WRONG → Auto-correct
    ↓
If CORRECT → Wait for next question

🔄 PHASE 5: INTELLIGENT CORRECTION ENGINE
5.1 Answer Matching Algorithm
pythonclass AnswerValidator:
    def __init__(self, database):
        self.db = database
        self.fuzzy_threshold = 85  # % similarity
    
    def find_question_match(self, ocr_question):
        """Find best matching question in database"""
        # Use fuzzy string matching
        # Account for OCR errors
        # Return matched question with confidence
        
    def validate_answer(self, question_id, clicked_answer):
        """Check if clicked answer is correct"""
        correct_answers = self.db.get_correct_answers(question_id)
        
        # Fuzzy match clicked answer against correct ones
        for correct in correct_answers:
            if fuzzy_match(clicked_answer, correct) > threshold:
                return True, None
        
        # Find which wrong answer was clicked
        wrong_answers = self.db.get_wrong_answers(question_id)
        clicked_match = best_fuzzy_match(clicked_answer, wrong_answers)
        
        return False, correct_answers[0]  # Return first correct answer
5.2 Auto-Correction System
pythondef auto_correct_answer(wrong_answer_coords, correct_answer_text):
    """Click the correct answer automatically"""
    
    # 1. Find correct answer on screen
    correct_coords = locate_answer_on_screen(correct_answer_text)
    
    # 2. Unclick wrong answer (if needed)
    if answer_can_be_unclicked():
        pyautogui.click(wrong_answer_coords)
        time.sleep(0.1)
    
    # 3. Click correct answer
    pyautogui.click(correct_coords)
    
    # 4. Log correction
    log_correction(wrong_answer_text, correct_answer_text)
```

---

## 🖼️ PHASE 6: UI DESIGN

### 6.1 Main Control Panel
```
╔══════════════════════════════════════════════════╗
║  🤖 Automated Test Correction System            ║
╠══════════════════════════════════════════════════╣
║                                                  ║
║  Status: ● MONITORING                           ║
║  Current Question: Q15/100                      ║
║  Corrections Made: 3                            ║
║                                                  ║
║  ┌────────────────────────────────────────┐    ║
║  │ [🚀 Start Monitoring]  [⏸️ Pause]      │    ║
║  │ [⏹️ Stop]  [⚙️ Settings]  [📊 Stats]    │    ║
║  └────────────────────────────────────────┘    ║
║                                                  ║
║  ┌─ Current Question ──────────────────────┐   ║
║  │ Koji je glavni grad Srbije?             │   ║
║  │ Type: SINGLE                             │   ║
║  └──────────────────────────────────────────┘   ║
║                                                  ║
║  ┌─ Last Action ───────────────────────────┐   ║
║  │ ❌ Wrong: Niš                            │   ║
║  │ ✅ Corrected to: Beograd                 │   ║
║  │ ⏱️ Time: 14:32:15                        │   ║
║  └──────────────────────────────────────────┘   ║
║                                                  ║
║  ┌─ Statistics ────────────────────────────┐   ║
║  │ Total Questions: 15                      │   ║
║  │ Correct First Try: 12                    │   ║
║  │ Auto-Corrected: 3                        │   ║
║  │ Success Rate: 80%                        │   ║
║  └──────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════╝
```

### 6.2 Setup Wizard
```
Step 1: Define question region (drag to select)
Step 2: Define answers region (drag to select)  
Step 3: Test detection on current question
Step 4: Start monitoring

🚀 PHASE 7: IMPLEMENTATION ROADMAP
Week 1: Foundation

 Set up project structure
 Create database schema
 Import existing Q&A data
 Build basic GUI shell
 Implement region selection (from your reference code)

Week 2: Core Features

 Screen monitoring thread
 OCR integration for Serbian
 Question matching algorithm
 Answer validation logic
 Database query optimization

Week 3: Automation

 Click detection system
 Answer location on screen
 Auto-click mechanism
 Correction logic
 Error handling

Week 4: Polish & Testing

 Real test environment testing
 Edge case handling
 Performance optimization
 User documentation
 Settings/configuration panel


🔍 PHASE 8: CRITICAL CHALLENGES & SOLUTIONS
Challenge 1: Reliable OCR in Serbian
Solution:

Use Serbian language pack: srp+eng
Pre-process images (contrast, denoise)
Use multiple OCR passes with different configs
Implement fuzzy matching (85%+ similarity)

Challenge 2: Fast Answer Location
Solution:

Cache answer positions after first detection
Use color markers to find answer blocks quickly
Maintain coordinate map of answer regions

Challenge 3: Detecting User Clicks vs Auto-Clicks
Solution:

Set flag before auto-clicking
Ignore screen changes during auto-click window
Use timing patterns (user clicks are slower)

Challenge 4: "Next Question" Detection
Solution:

Monitor for screen region changes
Detect when question text changes
User can press hotkey (e.g., N) to signal next question

Challenge 5: Multi-Answer Questions
Solution:

Track multiple correct answers from database
Allow multiple clicks before validation
Detect "Submit" button click to trigger validation


🎮 PHASE 9: OPERATION MODES
Mode 1: Full Auto (Recommended)

User just clicks answers
System auto-corrects immediately
No user confirmation needed

Mode 2: Confirm Before Correct

System detects wrong answer
Shows popup: "Wrong! Click OK to auto-correct"
User confirms, system corrects

Mode 3: Alert Only

System detects wrong answer
Shows alert but doesn't auto-click
User manually corrects


📝 PHASE 10: PSEUDO-CODE STRUCTURE
pythonclass AutoTestCorrector:
    def __init__(self):
        self.db = Database("questions.db")
        self.monitor = ScreenMonitor()
        self.validator = AnswerValidator(self.db)
        self.current_question = None
        
    def main_loop(self):
        while self.monitoring:
            # 1. Capture current question
            question_img = self.monitor.get_question_region()
            question_text = ocr_text(question_img)
            
            # 2. Match with database
            self.current_question = self.db.find_match(question_text)
            
            if not self.current_question:
                log("Question not in database")
                continue
            
            # 3. Wait for user click
            clicked_answer = self.wait_for_answer_click()
            
            # 4. Validate
            is_correct, correct_answer = self.validator.validate(
                self.current_question.id,
                clicked_answer
            )
            
            # 5. Auto-correct if wrong
            if not is_correct:
                self.show_alert(f"Wrong! Correcting to: {correct_answer}")
                self.auto_click_correct_answer(correct_answer)
                self.log_correction()
            else:
                self.show_success("Correct!")
            
            # 6. Wait for next question
            self.wait_for_next_question_signal()
    
    def wait_for_answer_click(self):
        """Monitor answers region for click"""
        while True:
            if self.detect_click_in_answers_region():
                return self.extract_clicked_answer()
            time.sleep(0.05)
    
    def auto_click_correct_answer(self, answer_text):
        """Find and click correct answer"""
        coords = self.locate_answer_on_screen(answer_text)
        pyautogui.click(coords)

🛠️ PHASE 11: TOOLS & LIBRARIES NEEDED
bashpip install opencv-python
pip install pytesseract
pip install pyautogui
pip install pillow
pip install keyboard
pip install fuzzywuzzy
pip install python-Levenshtein
pip install sqlite3  # Built-in
Tesseract Setup:

Download Serbian language pack
Install Tesseract OCR
Configure path in code


📊 PHASE 12: SUCCESS METRICS

Detection Accuracy: >95% question matching
OCR Accuracy: >90% text recognition
Correction Speed: <500ms from wrong click to correct click
False Positives: <5% (incorrect corrections)
System Stability: 2+ hours continuous operation


🎯 PHASE 13: MVP (Minimum Viable Product)
Start with these core features:

✅ User defines question + answers regions (manual setup)
✅ System monitors for screen changes
✅ OCR extracts question text
✅ Matches against database (exact or 85%+ fuzzy)
✅ Detects when answer is clicked (screen change detection)
✅ Validates clicked answer
✅ If wrong: auto-clicks correct answer
✅ Simple GUI with start/stop and status
✅ Basic logging

Then add enhancements:

Statistics tracking
Multiple test session support
Auto-detection of UI elements
Settings panel
Correction confirmation mode