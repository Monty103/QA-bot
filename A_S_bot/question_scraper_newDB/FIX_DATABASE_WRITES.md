# How to Fix Database Write Operations

## The Problem

Your API returns **HTTP 500 Internal Server Error** when trying to create questions. This prevents the questionnaire scraper from uploading data.

**Evidence**:
```
POST /api/questions
Status: 500 Internal Server Error
Body: <html><h1>Internal Server Error</h1>...
```

---

## Step 1: Check Render.com Logs

### Access Your Service Logs

1. Open: https://dashboard.render.com
2. Login to your account
3. Find your service: `question-database-api`
4. Click on it
5. Look for the **Logs** tab on the right side
6. Click **Logs**

### What to Look For

You'll see logs that look like this:

**✓ Good log** (API working):
```
[2025-12-01 21:20:14] GET /api/health - 200 OK
[2025-12-01 21:20:15] GET /api/questions - 200 OK
```

**✗ Bad log** (Error):
```
[2025-12-01 21:20:16] POST /api/questions - 500 ERROR
Traceback (most recent call last):
  File "app.py", line 45, in create_question
    cursor.execute(...)
OperationalError: database is locked
```

### Common Error Messages

**Error 1: Database is Locked**
```
sqlite3.OperationalError: database is locked
```
**Cause**: Multiple requests at once, or database corruption
**Fix**: Restart the Render.com service

**Error 2: Table Doesn't Exist**
```
sqlite3.OperationalError: no such table: questions
```
**Cause**: Database wasn't initialized
**Fix**: Initialize database (see below)

**Error 3: Import Error**
```
NameError: name 'request' is not defined
ModuleNotFoundError: No module named 'flask'
```
**Cause**: Missing import statements
**Fix**: Add missing imports to API code

**Error 4: SQL Syntax Error**
```
sqlite3.ProgrammingError: near "INSERT": syntax error
```
**Cause**: Malformed SQL in the API
**Fix**: Check SQL syntax in the INSERT statement

**Error 5: Missing Required Field**
```
TypeError: 'NoneType' object is not subscriptable
```
**Cause**: API expecting a field you're not sending
**Fix**: Check the request JSON format

---

## Step 2: Check Your API Code

### Find Your API Code

Where did you host the API? Look for:

- **GitHub repository** → Check your code there
- **Render.com web service** → View code in editor
- **Your local machine** → Check original Flask app

### Examine the Create Question Function

Find the code that handles POST `/api/questions`:

```python
@app.route('/api/questions', methods=['POST'])
def create_question():
    # THIS IS THE FUNCTION THAT'S FAILING
```

### Common Issues to Fix

#### Issue 1: Missing Error Handling

❌ **BAD** (No error handling):
```python
@app.route('/api/questions', methods=['POST'])
def create_question():
    data = request.json
    cursor.execute("""
        INSERT INTO questions (question_text, question_type, required_answers)
        VALUES (?, ?, ?)
    """, (data['question_text'], data['question_type'], data['required_answers']))
    db.commit()
    return {"success": True, "data": {"question_id": cursor.lastrowid}}
```

✓ **GOOD** (With error handling):
```python
@app.route('/api/questions', methods=['POST'])
def create_question():
    try:
        data = request.json
        if not data:
            return {"success": False, "message": "No JSON data"}, 400

        if not data.get('question_text'):
            return {"success": False, "message": "Missing question_text"}, 400

        cursor.execute("""
            INSERT INTO questions (question_text, question_type, required_answers)
            VALUES (?, ?, ?)
        """, (
            data['question_text'],
            data.get('question_type', 'single'),
            data.get('required_answers', 1)
        ))
        db.commit()

        return {
            "success": True,
            "data": {"question_id": cursor.lastrowid}
        }, 201

    except sqlite3.OperationalError as e:
        return {"success": False, "message": f"Database error: {str(e)}"}, 500
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}, 500
```

#### Issue 2: Missing Imports

❌ **BAD** (Missing imports):
```python
from flask import Flask, jsonify
# Missing: request, make_response

@app.route('/api/questions', methods=['POST'])
def create_question():
    data = request.json  # ← NameError: request not defined
```

✓ **GOOD** (All imports):
```python
from flask import Flask, jsonify, request, make_response
import sqlite3
from datetime import datetime

@app.route('/api/questions', methods=['POST'])
def create_question():
    data = request.json  # ✓ Now 'request' is defined
```

#### Issue 3: Database Not Initialized

❌ **BAD** (No database check):
```python
def create_question():
    cursor.execute("INSERT INTO questions ...")  # May fail if table doesn't exist
```

✓ **GOOD** (Database initialized):
```python
# On app startup:
def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'single',
            required_answers INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN,
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    """)
    db.commit()

init_db()  # Call this when app starts
```

#### Issue 4: Wrong Content-Type

❌ **BAD** (Doesn't check content type):
```python
def create_question():
    data = request.json  # May be None if Content-Type not JSON
    question_text = data['question_text']  # TypeError!
```

✓ **GOOD** (Checks content type):
```python
def create_question():
    if not request.is_json:
        return {"success": False, "message": "Request must be JSON"}, 400

    data = request.json
    if not data:
        return {"success": False, "message": "No data provided"}, 400

    question_text = data.get('question_text')
    if not question_text:
        return {"success": False, "message": "Missing question_text"}, 400
```

---

## Step 3: Test the Fix

### After You Fix the Code

1. Deploy the updated code to Render.com
2. Run the diagnostic test:

```bash
python test_database.py
```

### Expected Output

**Before Fix** (Current):
```
[PASS] Health Check
[PASS] Read All Questions
[PASS] Read Single Question
[FAIL] Create Question           <- This should now be PASS
[SKIP] Create Answer
[SKIP] Verify Created Data
[PASS] Database Statistics
```

**After Fix** (Expected):
```
[PASS] Health Check
[PASS] Read All Questions
[PASS] Read Single Question
[PASS] Create Question           <- Now PASSING!
[PASS] Create Answer             <- Now PASSING!
[PASS] Verify Created Data       <- Now PASSING!
[PASS] Database Statistics
```

---

## Step 4: Test with Questionnaire Scraper

Once all tests pass:

1. Run the questionnaire scraper:
```bash
python questionnaire_scraper.py
```

2. Capture 1-2 test questions:
   - Click START
   - Press SPACEBAR
   - Draw rectangles as usual

3. Click SYNC button

4. Should now successfully upload!

---

## Common Flask API Template

Here's a working Flask API template you can use:

```python
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
DATABASE = 'questions.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with required tables"""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'single',
            required_answers INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            answer_text TEXT NOT NULL,
            is_correct BOOLEAN DEFAULT 0,
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    """)

    db.commit()
    db.close()

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "success": True,
        "message": "API is running",
        "data": {"status": "healthy"}
    })

@app.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        include_answers = request.args.get('include_answers', 'false').lower() == 'true'
        db = get_db()
        cursor = db.cursor()

        cursor.execute('SELECT * FROM questions ORDER BY id DESC')
        questions = cursor.fetchall()

        result = []
        for q in questions:
            question = dict(q)
            if include_answers:
                cursor.execute('SELECT * FROM answers WHERE question_id = ?', (q['id'],))
                question['answers'] = [dict(a) for a in cursor.fetchall()]
            result.append(question)

        return jsonify({
            "success": True,
            "message": "Success",
            "data": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/questions', methods=['POST'])
def create_question():
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Request must be JSON"
            }), 400

        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400

        question_text = data.get('question_text')
        if not question_text:
            return jsonify({
                "success": False,
                "message": "Missing question_text"
            }), 400

        question_type = data.get('question_type', 'single')
        required_answers = data.get('required_answers', 1)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO questions (question_text, question_type, required_answers)
            VALUES (?, ?, ?)
        """, (question_text, question_type, required_answers))

        db.commit()
        question_id = cursor.lastrowid
        db.close()

        return jsonify({
            "success": True,
            "message": "Question created",
            "data": {"question_id": question_id}
        }), 201

    except sqlite3.Error as e:
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/questions/<int:question_id>/answers', methods=['POST'])
def create_answer(question_id):
    try:
        if not request.is_json:
            return jsonify({
                "success": False,
                "message": "Request must be JSON"
            }), 400

        data = request.json
        answer_text = data.get('answer_text')
        is_correct = data.get('is_correct', 0)

        if not answer_text:
            return jsonify({
                "success": False,
                "message": "Missing answer_text"
            }), 400

        db = get_db()
        cursor = db.cursor()

        # Verify question exists
        cursor.execute('SELECT id FROM questions WHERE id = ?', (question_id,))
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Question not found"
            }), 404

        cursor.execute("""
            INSERT INTO answers (question_id, answer_text, is_correct)
            VALUES (?, ?, ?)
        """, (question_id, answer_text, is_correct))

        db.commit()
        db.close()

        return jsonify({
            "success": True,
            "message": "Answer created"
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    init_db()
    app.run()
```

---

## Quick Checklist

- [ ] Check Render.com logs for error message
- [ ] Found the exact error? Document it
- [ ] Fixed the Flask code?
- [ ] Added error handling?
- [ ] Added necessary imports?
- [ ] Redeployed to Render.com?
- [ ] Ran `python test_database.py`?
- [ ] All 7 tests now pass?
- [ ] Tested questionnaire scraper SYNC?
- [ ] Successfully uploaded a test question?

---

## Getting Help

If you get stuck:

1. **Share the exact error from logs**
2. **Share the POST request data** (from test_database.py output)
3. **Share your Flask code** (the create_question function)

With those three things, it's usually fixable in 5 minutes.

---

## Summary

**Your Issue**: Write operations (POST) return HTTP 500
**Root Cause**: Bug in Flask API code
**Time to Fix**: 15-30 minutes
**Steps**:
1. Check Render.com logs
2. Identify the error
3. Fix the Flask code
4. Redeploy
5. Test with `python test_database.py`

Good luck! This is very fixable.
