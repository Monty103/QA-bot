# Quick Start Guide

## Installation (One Time)

### 1. Install Python Packages
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract-OCR
Download from: https://github.com/UB-Mannheim/tesseract/wiki

Install to default location: `C:\Program Files\Tesseract-OCR`

### 3. Run the Application
```bash
python questionnaire_scraper.py
```

## Workflow (Fast & Optimized)

### Start Capturing
1. **Click START** button (green) - Status shows "Listening for SPACEBAR..."
2. **Press SPACEBAR** - Start capture for a question
3. **Draw rectangle around question** (click & drag) - OCR extracts automatically
4. **Draw rectangle around answers** (click & drag) - Colors detected automatically
5. **Status shows** "✓ Captured Q#1 | Ready for next" - Done!
6. **Press SPACEBAR again** - Repeat for next question

### After Capturing
- **Click PREVIEW** - Review all captured questions
- **Click SYNC** - Upload all to database
- **Click STOP** - End capture session

## Key Points

✓ **No dialog boxes** - Status bar shows everything
✓ **No manual confirmations** - Workflow is automatic
✓ **Fast** - ~5 seconds per question
✓ **Smart colors** - Green boxes = correct, Red boxes = incorrect

## Status Messages

| Status | Meaning |
|--------|---------|
| "Listening for SPACEBAR..." | Ready - press SPACEBAR |
| "Select question area..." | Draw rectangle for question |
| "Extracting question..." | Processing text |
| "Select answer area..." | Draw rectangle for answers |
| "Analyzing answers..." | Detecting colors |
| "✓ Captured Q#N \| Ready for next" | Success - press SPACEBAR for next |

## Tips

1. **Quick selections** - Draw rectangles quickly, don't be precise
2. **Keep questionnaire visible** - Have it open while capturing
3. **Use PREVIEW before SYNC** - Review data quality
4. **Batch capture** - Do multiple questions before uploading
5. **Clear colors** - Make sure green and red boxes are visible

## Performance

- **Per question**: ~5 seconds
- **10 questions**: ~50 seconds
- **100 questions**: ~8 minutes

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API Disconnected" | Check internet connection |
| OCR not extracting text | Install Tesseract at `C:\Program Files\Tesseract-OCR` |
| Color detection wrong | Ensure green/red boxes are clear and distinct |
| Text not readable | Increase selected area size, ensure clear font |

## That's It!

You're ready to start capturing Serbian questionnaires!

Simply:
1. Click START
2. Press SPACEBAR
3. Draw rectangles
4. Done!

For detailed information, see README.md or API_REFERENCE.md
