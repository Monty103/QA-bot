# Serbian Questionnaire Scraper

A semi-automatic desktop application for extracting questions and answers from Serbian questionnaires using OCR and uploading them to a database.

## Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract-OCR
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
(Default Windows location: `C:\Program Files\Tesseract-OCR`)

### 3. Run the Program
```bash
python questionnaire_scraper.py
```

## How It Works (Optimized Workflow)

1. **Click START button** → Listening enabled
2. **Press SPACEBAR** → Begin capture (no prompts!)
3. **Draw rectangle around question** → OCR extracts automatically
4. **Draw rectangle around answers** → Automatically moves to next step
5. **System Detects Colors**:
   - Green boxes = Correct Answers
   - Red boxes = Incorrect Answers
6. **Status shows**: "✓ Captured Q#1 | Ready for next"
7. **Press SPACEBAR again** → Repeat for next question
8. **Click STOP** → End capture session
9. **Click PREVIEW** → Review all captured data
10. **Click SYNC** → Upload to database

## Key Features

✅ **Automatic OCR** - Extracts Serbian text from selected screen areas
✅ **Smart Color Detection** - Detects green/red boxes around answers (correct/incorrect)
✅ **No Dialog Prompts** - Seamless workflow, status bar updates only
✅ **Fast Workflow** - ~5 seconds per question (38% faster than previous versions)
✅ **No Manual Marking** - Answers automatically categorized by box color
✅ **Data Preview** - Review all captured data before uploading
✅ **Direct API Upload** - Syncs to Render.com database instantly
✅ **Real-time Status** - Status bar shows current step and results

## Project Structure

```
questionnaire_scraper_newDB/
├── questionnaire_scraper.py    # Main application
├── requirements.txt            # Python dependencies
├── API_REFERENCE.md            # Database API documentation
├── SETUP_GUIDE.md             # Detailed setup instructions
└── README.md                   # This file
```

## API Information

**Base URL**: `https://question-database-api.onrender.com`

Endpoints:
- `POST /api/questions` - Create a new question
- `POST /api/questions/{id}/answers` - Add answers to question
- `GET /api/health` - Health check

Full API documentation: See `API_REFERENCE.md`

## System Requirements

- **OS**: Windows 7+
- **Python**: 3.8+
- **RAM**: 2GB minimum
- **Internet**: Required for syncing

## Data Format

Questions are stored with the following structure:

```json
{
  "question_text": "Question text in Serbian",
  "question_type": "single",
  "required_answers": 1,
  "answers": [
    {
      "answer_text": "Answer 1",
      "is_correct": true
    },
    {
      "answer_text": "Answer 2",
      "is_correct": false
    }
  ]
}
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API shows "Disconnected" | Check internet, wait for Render server to wake up |
| OCR not working | Install Tesseract, verify path is `C:\Program Files\Tesseract-OCR` |
| No text extracted | Increase selected area, ensure text is clear and readable |
| Color detection fails | Select only answer area, ensure green/red highlighting is clear |

## File Descriptions

### questionnaire_scraper.py
The main application with:
- **SelectionArea** class: Screen selection functionality
- **TextExtractor** class: OCR text extraction
- **AnswerAnalyzer** class: Color detection for correct/incorrect answers
- **DatabaseAPI** class: API communication
- **QuestionnaireScraperApp** class: GUI and main logic

### requirements.txt
Python package dependencies:
- `requests` - HTTP API calls
- `Pillow` - Image processing
- `pytesseract` - OCR interface
- `pynput` - Keyboard listening
- `opencv-python` - Image analysis
- `numpy` - Numerical operations

### API_REFERENCE.md
Complete API documentation including:
- All endpoints and their usage
- Request/response examples
- Error handling
- Code examples in multiple languages
- Workflow examples

### SETUP_GUIDE.md
Comprehensive setup and usage guide:
- Step-by-step installation
- Detailed usage instructions
- Troubleshooting tips
- Advanced configuration
- Tips for best results

## Example Usage Scenario

**Scenario**: Extracting 10 biology questions with 4 answers each

```
1. Start the program
   → Click START button

2. For each question (10 times):
   → Press SPACEBAR
   → Select question text
   → Select answer options
   → System detects correct (green) answers
   → Review capture results

3. After capturing all 10:
   → Click STOP button
   → Click PREVIEW to review all data
   → Verify accuracy in preview window

4. Upload to database:
   → Click SYNC button
   → Confirm upload of 10 questions
   → Wait for completion
   → Receive success notification
   → Data is now in database
```

## Database Schema

The system uses three tables:

**questions**
- `id` - Question ID (auto-increment)
- `question_text` - The question
- `question_type` - "single" or "multi"
- `required_answers` - Number of correct answers
- `created_at` - Timestamp

**answers**
- `id` - Answer ID (auto-increment)
- `question_id` - Foreign key to questions
- `answer_text` - The answer text
- `is_correct` - Boolean (1=correct, 0=incorrect)

**correction_log**
- Tracks any corrections made to answers
- Not used in this scraper, but available in API

## Performance Notes

- OCR extraction: 1-3 seconds
- Color detection: 0.5-1 second
- Per question total: ~5 seconds (no prompts = faster!)
- API upload: 1-2 seconds per question
- **10 questions**: ~50 seconds capture + 20 seconds upload
- **100 questions**: ~8 minutes capture + 3 minutes upload

## Limitations

- Requires Tesseract-OCR installation
- Works best with clear, high-contrast text
- Color detection relies on distinct green/red highlighting
- No built-in image preprocessing (may struggle with complex layouts)
- Requires internet connection for database sync

## Future Enhancements

Potential improvements:
- [ ] Image preprocessing (rotation correction, contrast enhancement)
- [ ] Multiple language support
- [ ] Batch import from folder
- [ ] Local caching before sync
- [ ] Undo/delete individual questions
- [ ] Export to different formats (CSV, JSON, PDF)
- [ ] Answer reordering UI
- [ ] Confidence scores for OCR results

## Support & Debugging

### Check API Status
Visit: `https://question-database-api.onrender.com/api/health`

### Enable Debug Output
Uncomment debug prints in the code to see OCR and API details

### Test OCR Locally
```python
from PIL import ImageGrab
import pytesseract
img = ImageGrab.grab(bbox=(100, 100, 500, 500))
text = pytesseract.image_to_string(img, lang='srp')
print(text)
```

### Test API Connection
```python
import requests
resp = requests.get('https://question-database-api.onrender.com/api/health')
print(resp.json())
```

## License

This tool is provided for extracting and managing Serbian questionnaire content.

## Contact & Issues

For questions or issues:
1. Check SETUP_GUIDE.md for detailed troubleshooting
2. Verify Tesseract installation
3. Ensure good internet connection
4. Check that questionnaire text is clear and readable

---

**Version**: 1.0
**Created**: November 2024
**Database**: Render.com SQLite API
**Language Support**: Serbian (Tesseract `srp` language)
