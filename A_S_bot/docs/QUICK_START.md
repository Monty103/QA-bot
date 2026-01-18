# 🚀 Quick Start Guide - Auto Test Corrector

Get up and running in 5 minutes!

---

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Tesseract OCR installed at `C:\dt\Tesseract-OCR\`
- [ ] Serbian language pack (`srp.traineddata`) in Tesseract's `tessdata` folder
- [ ] Required Python packages installed (see below)

---

## Step 1: Install Dependencies (One Time)

Open terminal in the `A_S_bot` folder and run:

```bash
pip install opencv-python pytesseract pyautogui pillow fuzzywuzzy python-Levenshtein
```

---

## Step 2: Prepare Your Question Database

### Option A: Import from JSON (Recommended)

Create a file named `qa_data.json` in the `A_S_bot` folder with your questions:

```json
{
  "questions": [
    {
      "question": "Your question text here?",
      "question_type": "single",
      "required_correct_answers": 1,
      "correct_answers": ["Correct answer 1"],
      "wrong_answers": ["Wrong 1", "Wrong 2", "Wrong 3"]
    }
  ]
}
```

**Question Types:**
- `"single"` = Radio buttons (○) - Select ONE answer
- `"multi"` = Checkboxes (□) - Select MULTIPLE answers

### Option B: Use Reference Program

Run `reference_prog/ultimate_database_qa_gui.py` to build your database interactively.

---

## Step 3: Launch the Application

```bash
python main.py
```

---

## Step 4: One-Time Setup

### 4.1 Import Database (First Launch)

If `qa_data.json` exists, it will be auto-imported. Otherwise:

1. Click **"📥 Import Data"**
2. Paste your JSON or select file
3. Click **"Import"**

### 4.2 Define Screen Regions

1. Click **"⚙️ Setup Regions"**

2. **STEP 1 - Question Region:**
   - A fullscreen window appears
   - Drag a rectangle around the **QUESTION TEXT ONLY**
   - Release mouse to confirm

   Example:
   ```
   ┌─────────────────────────────────┐
   │ Koji je glavni grad Srbije?     │  ← Select this area
   └─────────────────────────────────┘
   ```

3. **STEP 2 - Answers Region:**
   - Another fullscreen window appears
   - Drag a rectangle around **ALL ANSWER OPTIONS**
   - Release mouse to confirm

   Example:
   ```
   ┌─────────────────────────────────┐
   │ ○ Niš                           │
   │ ○ Beograd                       │  ← Select entire area
   │ ○ Novi Sad                      │
   │ ○ Kragujevac                    │
   └─────────────────────────────────┘
   ```

4. Click **OK** when setup is complete

---

## Step 5: Start Monitoring

1. Navigate to your web-based questionnaire in your browser
2. Click **"🚀 Start Monitoring"** in the Auto Test Corrector window
3. Status changes to **"● MONITORING"** (green)

---

## Step 6: Take Your Test!

Now just take your test normally:

### What Happens:

1. **New Question Appears** → System OCRs it and finds match in database
2. **You Click an Answer** → System detects your selection
3. **System Validates:**
   - ✅ **If CORRECT:** Nothing happens, continue to next question
   - ❌ **If WRONG:** System auto-clicks the correct answer for you!

### Activity Log Shows:

```
[14:32:15] ℹ️ New question detected, processing...
[14:32:16] ✅ Question matched (ID: 42)
[14:32:16] ℹ️ Question type detected: SINGLE
[14:32:16] ℹ️ Found 4 answers (✅1 ❌3)
[14:32:18] ℹ️ Answer click detected!
[14:32:18] ❌ Wrong answer: Niš
[14:32:18] 🔧 Auto-correcting to: Beograd
[14:32:19] ✅ Correction successful!
```

---

## Step 7: Navigate to Next Question

After each question:

1. Press **'N'** key OR
2. Wait for screen to change (system auto-detects)
3. System processes next question automatically

---

## Step 8: View Statistics

The GUI shows real-time stats:

```
┌────────────────────────────────────┐
│ Current Question: Q15/100          │
│ Total Questions: 15                │
│ Correct First Try: 12              │
│ Auto-Corrected: 3                  │
│ Success Rate: 80%                  │
└────────────────────────────────────┘
```

---

## Step 9: Stop Monitoring

When done:
- Click **"⏹️ Stop"** to end monitoring
- View **"📊 Database Stats"** for session summary

---

## 🎯 Tips for Success

### ✅ DO:
- Select tight regions (just question, just answers)
- Ensure text is clearly visible
- Keep questionnaire window visible during test
- Let auto-correction complete before next action

### ❌ DON'T:
- Don't minimize the questionnaire window
- Don't move mouse during auto-correction
- Don't select regions with overlapping elements
- Don't click too fast (wait for system to process)

---

## 🐛 Quick Troubleshooting

### "Question not in database"
→ Add the question to `qa_data.json` and re-import

### "Could not detect clicked answer"
→ Reselect answers region to include all options

### OCR reads wrong text
→ Ensure text is clear, try re-selecting question region

### Auto-correction doesn't work
→ Check that correct answers are marked in database (`is_correct = 1`)

---

## 📋 Example Workflow

**Scenario:** Taking a 100-question test

1. **Preparation (5 min):**
   - Import 100 questions from JSON
   - Setup question/answer regions

2. **During Test (60 min):**
   - Start monitoring
   - Answer questions normally
   - System auto-corrects mistakes
   - View real-time stats

3. **After Test:**
   - Stop monitoring
   - Check statistics: 95% correct first try, 5 auto-corrected
   - Review correction log in database

---

## 🎓 Next Steps

- Read full [README.md](README.md) for detailed documentation
- Check [reference.md](reference.md) for technical details
- Customize [config.json](config.json) for your needs
- Review [reference_MVP.md](reference_MVP.md) for architecture info

---

**Happy testing! 🚀**
