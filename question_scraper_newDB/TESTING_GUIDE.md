# Testing Guide - Serbian Questionnaire Scraper

## Pre-Testing Checklist

Before testing the application with real questionnaires, ensure:

- [ ] Python 3.13+ installed
- [ ] All requirements installed: `pip install -r requirements.txt`
- [ ] Tesseract-OCR installed at `C:\Program Files\Tesseract-OCR` (v5.5.0+)
- [ ] Internet connection available (for API sync)
- [ ] Serbian questionnaire ready for capture
- [ ] Integration tests pass: `python test_integration.py`

---

## Phase 1: Automated Integration Tests

### Run the Test Suite
```bash
python test_integration.py
```

### Expected Results
All 8 tests should show status **OK** or **PASSED**:
1. ✓ Imports check
2. ✓ SelectionArea initialization
3. ✓ TextExtractor initialization
4. ✓ AnswerAnalyzer initialization
5. ✓ DatabaseAPI initialization
6. ✓ Color detection test
7. ✓ API connectivity
8. ✓ Tesseract availability

### Troubleshooting
| Issue | Solution |
|-------|----------|
| Import failed | Check `pip install -r requirements.txt` completed |
| Color detection failed | Check OpenCV installation |
| API connectivity failed | Check internet connection and Render.com API status |
| Tesseract not found | Install from https://github.com/UB-Mannheim/tesseract |

---

## Phase 2: Manual Functional Testing

### Test 1: Application Startup

```bash
python questionnaire_scraper.py
```

**Expected Behavior**:
- Tkinter window opens
- Size: 900x700
- Title: "Serbian Questionnaire Scraper"
- Status shows: "API Connected ✓" (green text) or "API Disconnected ✗" (red text)
- START button is green and enabled
- STOP button is red and disabled
- SYNC and PREVIEW buttons are blue and enabled

**Pass Criteria**: ✓ Window appears with all controls

---

### Test 2: Spacebar Listener

**Steps**:
1. Click the green **START** button
2. Observe status message

**Expected Behavior**:
- Status changes to "Listening for SPACEBAR... Press SPACEBAR to capture" (blue)
- START button becomes disabled (grayed out)
- STOP button becomes enabled

**Pass Criteria**: ✓ Status updates and buttons change state

---

### Test 3: Question Text Extraction

**Setup**:
- Have a Serbian questionnaire visible on screen
- Click START and wait for listening status

**Steps**:
1. Press SPACEBAR
2. Status shows "Select question area (draw rectangle)..." (blue)
3. Draw a rectangle around the question text
4. Release mouse

**Expected Behavior**:
- Status changes to "Extracting question..." (blue)
- After 1-2 seconds, status changes to "Select answer area (draw rectangle)..."
- No dialog boxes appear
- Automatic transition to answer selection

**Pass Criteria**: ✓ Question area selected and text extracted (check in last captured section)

---

### Test 4: Answer Color Detection

**Steps** (continuing from Test 3):
1. Draw a rectangle around the answer options
2. Release mouse

**Expected Behavior**:
- Status shows "Analyzing answers..." (blue)
- After 1-2 seconds, status shows "✓ Captured Q#1 | Ready for next" (green)
- Last captured section updates with question and answers
- Answers show [✓ CORRECT] or [✗ INCORRECT] tags
- Green boxes detected as correct, red as incorrect

**Example Output**:
```
QUESTION:
Koji je najveći grad u Srbiji?

ANSWERS:
1. [✓ CORRECT] Beograd
2. [✗ INCORRECT] Novi Sad
3. [✗ INCORRECT] Nis
```

**Pass Criteria**: ✓ Colors correctly identified as correct/incorrect

---

### Test 5: Multiple Questions Capture

**Steps**:
1. Continue from Test 4 status "Ready for next"
2. Press SPACEBAR again
3. Capture 3-5 more questions following the same process

**Expected Behavior**:
- Counter updates: "Captured: 1 questions", "Captured: 2 questions", etc.
- Each capture follows the ~5 second workflow
- No errors or crashes
- Data displays in the last captured section

**Pass Criteria**: ✓ Multiple questions captured without errors

---

### Test 6: Stop and Preview

**Steps**:
1. Click the red **STOP** button
2. Click the orange **PREVIEW** button

**Expected Behavior**:
- Status shows "Stopped. Captured X questions" (orange)
- STOP button becomes disabled
- START button becomes enabled
- PREVIEW window opens
- Preview shows all captured questions in formatted list

**Expected Format**:
```
================================================================================
QUESTIONNAIRE DATA PREVIEW
================================================================================

QUESTION #1
----------------------------------------
Koji je najveći grad u Srbiji?

ANSWERS:
  1. [✓ CORRECT] Beograd
  2. [✗ INCORRECT] Novi Sad
  3. [✗ INCORRECT] Nis

QUESTION #2
...
```

**Pass Criteria**: ✓ Preview window shows all questions properly formatted

---

### Test 7: Database Sync

**Prerequisites**: Must have X questions captured

**Steps**:
1. Click the blue **SYNC** button
2. Confirmation dialog: "Upload X questions to the database?"
3. Click "Yes"

**Expected Behavior**:
- Status shows "Syncing to database..." (blue)
- Status updates: "Syncing... 1/X (1 OK)", "Syncing... 2/X (2 OK)", etc.
- After 5-10 seconds, sync completes
- Success dialog appears:
  ```
  Sync Complete!

  Successful: X
  Failed: 0
  ```
- Status shows "✓ All X questions uploaded!" (green)
- Counter resets to "Captured: 0 questions"
- Last captured section clears

**Pass Criteria**: ✓ All questions uploaded successfully to database

---

### Test 8: Error Handling - Cancel Sync

**Steps**:
1. Capture 2-3 questions
2. Click SYNC
3. Click "No" in confirmation dialog

**Expected Behavior**:
- Dialog closes without syncing
- Status remains unchanged
- Data remains in counter and preview
- No errors or crashes

**Pass Criteria**: ✓ Cancel operation works correctly

---

## Phase 3: Edge Case Testing

### Test 9: OCR Failure Handling

**Setup**: Try to capture from an area with no text or unclear text

**Expected Behavior**:
- Status shows "OCR failed - could not extract question text" (red)
- Does not advance to answer selection
- User can press SPACEBAR again to retry
- No crash

**Pass Criteria**: ✓ Graceful error handling without crash

---

### Test 10: Color Confusion

**Setup**: Area with boxes that are partly colored or unclear colors

**Expected Behavior**:
- Detection may not find blocks if colors are outside ranges
- Status shows "OCR failed - could not extract answers" (red)
- User can retry with different area selection
- No crash

**Pass Criteria**: ✓ Handles ambiguous colors gracefully

---

### Test 11: Small Selection Area

**Setup**: Select a very small area (< 50x50 pixels)

**Expected Behavior**:
- OCR processes but may fail
- Color detection may not find valid blocks
- Appropriate error messages shown
- No crash

**Pass Criteria**: ✓ Handles edge cases without crashing

---

## Phase 4: Performance Testing

### Test 12: Capture Speed

**Setup**: Measure time for complete question/answer capture cycle

**Steps**:
1. Start with status "Ready"
2. Press SPACEBAR (time starts)
3. Draw question rectangle (1 sec)
4. Draw answer rectangle (1 sec)
5. Status shows "✓ Captured Q#X" (time ends)

**Expected Performance**:
- Total time: ~5 seconds (±1 sec)
- Processing time: ~3 seconds (OCR + color detection)
- Selection time: ~2 seconds (user interaction)

**Pass Criteria**: ✓ Consistent 5-second cycle

---

### Test 13: Batch Performance

**Setup**: Capture 10 questions in succession

**Steps**:
1. Start capture
2. Repeat spacebar → select question → select answers 10 times
3. Time total duration

**Expected Performance**:
- Total time: ~50 seconds (10 × 5 sec)
- Consistent speed throughout
- No slowdown or memory leaks

**Pass Criteria**: ✓ Performance remains consistent with batch

---

## Phase 5: Data Quality Testing

### Test 14: Text Recognition Accuracy

**Setup**: Questionnaire with clear Serbian text

**Expected Behavior**:
- ✓ Extracts 90%+ of question text correctly
- ✓ Identifies all answer options
- ✓ Properly classifies green as correct, red as incorrect
- ✓ Detects multiple correct answers when present

**Pass Criteria**: ✓ High accuracy in real questionnaire

---

### Test 15: Multiple Correct Answers

**Setup**: Questionnaire with multiple correct answers (multi-select)

**Expected Behavior**:
- All green boxes marked [✓ CORRECT]
- When synced, question_type auto-set to "multi"
- required_answers count reflects actual count

**Pass Criteria**: ✓ Multi-select questions handled correctly

---

## Acceptance Criteria

### All tests pass when:

1. **Automation**: test_integration.py passes 8/8 tests
2. **Core Workflow**: Can capture → preview → sync in <2 minutes
3. **Accuracy**: 90%+ correct extraction on real questionnaires
4. **Performance**: 5 seconds per question average
5. **Reliability**: No crashes on 50+ captures
6. **Data Quality**: All captured questions upload successfully
7. **Error Handling**: Graceful failures with user feedback
8. **Multi-select**: Properly handles multiple correct answers

---

## Reporting Issues

If any test fails, note:
1. Which test failed (number and name)
2. What you were doing
3. What happened (vs. expected)
4. OCR output (copy from preview/last captured)
5. Error messages (if any)

Create a bug report with this information.

---

## Performance Baseline

Once you've completed testing, record:
- [ ] Average time per question: ___ seconds
- [ ] Total questions captured: ___
- [ ] Successful syncs: ___
- [ ] Failed captures: ___
- [ ] Failed syncs: ___

This helps track improvements over time.

---

## Next Steps After Testing

1. **Passed all tests**: Application is ready for production use
2. **Some test failures**: Identify root cause and adjust:
   - OCR quality issues → Improve image selection/contrast
   - Color detection issues → Adjust HSV ranges (see IMPROVEMENTS_SUMMARY.md)
   - API issues → Check Render.com dashboard and connection
3. **Performance issues**: Profile and optimize based on bottleneck
4. **Data quality issues**: Iterate on questionnaire image quality

---

## Support

For detailed information on:
- **Installation**: See [QUICK_START.md](QUICK_START.md)
- **API Integration**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Technical Details**: See [IMPROVEMENTS_SUMMARY.md](IMPROVEMENTS_SUMMARY.md)
- **Code Review**: See [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)
