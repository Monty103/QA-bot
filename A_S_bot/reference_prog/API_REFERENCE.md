# Question Database API Reference
## For AI Assistant Development Reference

---

## 📋 API Overview

**Base URL**: `https://question-database-api.onrender.com`


**Content-Type**: `application/json`
**Authentication**: None (add if needed for production)

This API provides a complete interface for managing quiz questions, answers, and correction logging.

---

## 🗄️ Database Schema

### Tables Structure

#### `questions` Table
```sql
id                  INTEGER PRIMARY KEY AUTOINCREMENT
question_text       TEXT NOT NULL              -- The question text
question_type       TEXT DEFAULT 'single'      -- 'single' or 'multi'
required_answers    INTEGER DEFAULT 1          -- How many correct answers needed
created_at          TIMESTAMP                  -- Auto-generated timestamp
```

#### `answers` Table
```sql
id                  INTEGER PRIMARY KEY AUTOINCREMENT
question_id         INTEGER                    -- Foreign key to questions.id
answer_text         TEXT NOT NULL              -- The answer text
is_correct          BOOLEAN                    -- 1 = correct, 0 = wrong
```

#### `correction_log` Table
```sql
id                      INTEGER PRIMARY KEY AUTOINCREMENT
timestamp               TIMESTAMP                  -- Auto-generated
question_text           TEXT                       -- Question that was corrected
wrong_answer            TEXT                       -- What user selected (wrong)
correct_answer          TEXT                       -- What was auto-selected (correct)
correction_successful   BOOLEAN                    -- Did the correction work
```

---

## 🔌 API Endpoints Reference

### 📌 Health Check

#### `GET /api/health`
Check if API is running.

**Response**:
```json
{
  "success": true,
  "message": "API is running",
  "data": {
    "status": "healthy"
  }
}
```

---

## 📝 Question Endpoints

### Get All Questions

#### `GET /api/questions`
Retrieve all questions from database.

**Query Parameters**:
- `include_answers` (optional): `true` or `false` - Include answers in response

**Example Request**:
```http
GET /api/questions?include_answers=true
```

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "question_text": "What is the capital of France?",
      "question_type": "single",
      "required_answers": 1,
      "created_at": "2024-11-24 10:30:00",
      "answers": [
        {
          "id": 1,
          "question_id": 1,
          "answer_text": "Paris",
          "is_correct": 1
        },
        {
          "id": 2,
          "question_id": 1,
          "answer_text": "London",
          "is_correct": 0
        }
      ]
    }
  ]
}
```

---

### Get Specific Question

#### `GET /api/questions/{question_id}`
Retrieve a single question by ID.

**Path Parameters**:
- `question_id` (required): Integer - The question ID

**Query Parameters**:
- `include_answers` (optional): `true` or `false`

**Example Request**:
```http
GET /api/questions/1?include_answers=true
```

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "id": 1,
    "question_text": "What is the capital of France?",
    "question_type": "single",
    "required_answers": 1,
    "created_at": "2024-11-24 10:30:00",
    "answers": [
      {
        "id": 1,
        "question_id": 1,
        "answer_text": "Paris",
        "is_correct": 1
      }
    ]
  }
}
```

---

### Create New Question

#### `POST /api/questions`
Create a new question.

**Request Body**:
```json
{
  "question_text": "What is Python?",
  "question_type": "single",
  "required_answers": 1
}
```

**Field Descriptions**:
- `question_text` (required): String - The question text
- `question_type` (optional): String - Either "single" or "multi" (default: "single")
- `required_answers` (optional): Integer - Number of correct answers (default: 1)

**Example Response**:
```json
{
  "success": true,
  "message": "Question created successfully",
  "data": {
    "question_id": 5
  }
}
```

---

### Update Question

#### `PUT /api/questions/{question_id}`
Update an existing question.

**Path Parameters**:
- `question_id` (required): Integer - The question ID to update

**Request Body** (all fields optional):
```json
{
  "question_text": "What is Python programming?",
  "question_type": "single",
  "required_answers": 1
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Question updated successfully",
  "data": null
}
```

---

### Delete Question

#### `DELETE /api/questions/{question_id}`
Delete a question (also deletes all associated answers).

**Path Parameters**:
- `question_id` (required): Integer - The question ID to delete

**Example Response**:
```json
{
  "success": true,
  "message": "Question deleted successfully",
  "data": null
}
```

---

### Search Questions

#### `GET /api/questions/search`
Search questions by text.

**Query Parameters**:
- `q` (required): String - Search query

**Example Request**:
```http
GET /api/questions/search?q=capital
```

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "question_text": "What is the capital of France?",
      "question_type": "single",
      "required_answers": 1,
      "created_at": "2024-11-24 10:30:00"
    }
  ]
}
```

---

## 🎯 Answer Endpoints

### Get Answers for Question

#### `GET /api/questions/{question_id}/answers`
Get all answers for a specific question.

**Path Parameters**:
- `question_id` (required): Integer - The question ID

**Query Parameters**:
- `correct_only` (optional): `true` or `false` - Only return correct answers

**Example Request**:
```http
GET /api/questions/1/answers?correct_only=false
```

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "question_id": 1,
      "answer_text": "Paris",
      "is_correct": 1
    },
    {
      "id": 2,
      "question_id": 1,
      "answer_text": "London",
      "is_correct": 0
    }
  ]
}
```

---

### Add Answer to Question

#### `POST /api/questions/{question_id}/answers`
Add a new answer to a question.

**Path Parameters**:
- `question_id` (required): Integer - The question ID

**Request Body**:
```json
{
  "answer_text": "Paris",
  "is_correct": true
}
```

**Field Descriptions**:
- `answer_text` (required): String - The answer text
- `is_correct` (optional): Boolean - Whether this is a correct answer (default: false)

**Example Response**:
```json
{
  "success": true,
  "message": "Answer created successfully",
  "data": {
    "answer_id": 10
  }
}
```

---

### Update Answer

#### `PUT /api/answers/{answer_id}`
Update an existing answer.

**Path Parameters**:
- `answer_id` (required): Integer - The answer ID

**Request Body** (all fields optional):
```json
{
  "answer_text": "Paris, France",
  "is_correct": true
}
```

**Example Response**:
```json
{
  "success": true,
  "message": "Answer updated successfully",
  "data": null
}
```

---

### Delete Answer

#### `DELETE /api/answers/{answer_id}`
Delete a specific answer.

**Path Parameters**:
- `answer_id` (required): Integer - The answer ID

**Example Response**:
```json
{
  "success": true,
  "message": "Answer deleted successfully",
  "data": null
}
```

---

## 📊 Correction Log Endpoints

### Get Correction Log

#### `GET /api/corrections`
Retrieve correction log entries.

**Query Parameters**:
- `limit` (optional): Integer - Limit number of results

**Example Request**:
```http
GET /api/corrections?limit=10
```

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "timestamp": "2024-11-24 15:30:00",
      "question_text": "What is the capital of France?",
      "wrong_answer": "London",
      "correct_answer": "Paris",
      "correction_successful": 1
    }
  ]
}
```

---

### Log Correction

#### `POST /api/corrections`
Log a correction attempt.

**Request Body**:
```json
{
  "question_text": "What is the capital of France?",
  "wrong_answer": "London",
  "correct_answer": "Paris",
  "correction_successful": true
}
```

**Field Descriptions**:
- `question_text` (required): String - The question text
- `wrong_answer` (required): String - The answer the user selected (wrong)
- `correct_answer` (required): String - The correct answer that was auto-selected
- `correction_successful` (required): Boolean - Whether the correction worked

**Example Response**:
```json
{
  "success": true,
  "message": "Correction logged successfully",
  "data": {
    "correction_id": 15
  }
}
```

---

### Get Correction Statistics

#### `GET /api/corrections/stats`
Get statistics about corrections.

**Example Response**:
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "total_corrections": 50,
    "successful_corrections": 45,
    "failed_corrections": 5
  }
}
```

---

## 🔄 Common Workflows

### Workflow 1: Create a Complete Question with Answers

```python
import requests

BASE_URL = "https://your-service.onrender.com"

# Step 1: Create question
question_data = {
    "question_text": "What is 2 + 2?",
    "question_type": "single",
    "required_answers": 1
}
response = requests.post(f"{BASE_URL}/api/questions", json=question_data)
question_id = response.json()["data"]["question_id"]

# Step 2: Add answers
answers = [
    {"answer_text": "3", "is_correct": False},
    {"answer_text": "4", "is_correct": True},
    {"answer_text": "5", "is_correct": False},
    {"answer_text": "22", "is_correct": False}
]

for answer in answers:
    requests.post(
        f"{BASE_URL}/api/questions/{question_id}/answers",
        json=answer
    )

print(f"Question created with ID: {question_id}")
```

---

### Workflow 2: Get Random Question for Quiz

```python
import requests
import random

BASE_URL = "https://your-service.onrender.com"

# Get all questions with answers
response = requests.get(f"{BASE_URL}/api/questions?include_answers=true")
questions = response.json()["data"]

# Pick random question
random_question = random.choice(questions)

print(f"Question: {random_question['question_text']}")

# Shuffle answers
answers = random_question['answers']
random.shuffle(answers)

for i, answer in enumerate(answers, 1):
    print(f"{i}. {answer['answer_text']}")
```

---

### Workflow 3: Check Answer and Log if Wrong

```python
import requests

BASE_URL = "https://your-service.onrender.com"

def check_answer(question_id, selected_answer_id):
    # Get question with answers
    response = requests.get(
        f"{BASE_URL}/api/questions/{question_id}?include_answers=true"
    )
    question = response.json()["data"]
    
    # Find selected answer
    selected_answer = next(
        (a for a in question['answers'] if a['id'] == selected_answer_id),
        None
    )
    
    # Check if correct
    if selected_answer and selected_answer['is_correct']:
        return True, "Correct!"
    
    # Find correct answer
    correct_answer = next(
        (a for a in question['answers'] if a['is_correct']),
        None
    )
    
    # Log correction
    if selected_answer and correct_answer:
        correction_data = {
            "question_text": question['question_text'],
            "wrong_answer": selected_answer['answer_text'],
            "correct_answer": correct_answer['answer_text'],
            "correction_successful": True
        }
        requests.post(f"{BASE_URL}/api/corrections", json=correction_data)
    
    return False, f"Wrong! Correct answer: {correct_answer['answer_text']}"

# Usage
is_correct, message = check_answer(question_id=1, selected_answer_id=2)
print(message)
```

---

### Workflow 4: Import Questions from List

```python
import requests

BASE_URL = "https://your-service.onrender.com"

# List of questions to import
questions_to_import = [
    {
        "question": "What is the capital of Spain?",
        "type": "single",
        "answers": [
            ("Madrid", True),
            ("Barcelona", False),
            ("Valencia", False),
            ("Seville", False)
        ]
    },
    {
        "question": "Which are primary colors?",
        "type": "multi",
        "required": 3,
        "answers": [
            ("Red", True),
            ("Blue", True),
            ("Yellow", True),
            ("Green", False),
            ("Purple", False)
        ]
    }
]

for q_data in questions_to_import:
    # Create question
    question_payload = {
        "question_text": q_data["question"],
        "question_type": q_data["type"],
        "required_answers": q_data.get("required", 1)
    }
    response = requests.post(f"{BASE_URL}/api/questions", json=question_payload)
    question_id = response.json()["data"]["question_id"]
    
    # Add answers
    for answer_text, is_correct in q_data["answers"]:
        answer_payload = {
            "answer_text": answer_text,
            "is_correct": is_correct
        }
        requests.post(
            f"{BASE_URL}/api/questions/{question_id}/answers",
            json=answer_payload
        )
    
    print(f"✓ Imported: {q_data['question']}")
```

---

### Workflow 5: Export All Data to JSON File

```python
import requests
import json

BASE_URL = "https://your-service.onrender.com"

# Get all questions with answers
response = requests.get(f"{BASE_URL}/api/questions?include_answers=true")
questions = response.json()["data"]

# Get correction log
response = requests.get(f"{BASE_URL}/api/corrections")
corrections = response.json()["data"]

# Get stats
response = requests.get(f"{BASE_URL}/api/corrections/stats")
stats = response.json()["data"]

# Create export data
export_data = {
    "export_date": "2024-11-24",
    "total_questions": len(questions),
    "questions": questions,
    "corrections": corrections,
    "statistics": stats
}

# Save to file
with open("database_backup.json", "w") as f:
    json.dump(export_data, f, indent=2)

print("✓ Database exported to database_backup.json")
```

---

## 🛠️ Code Examples for Different Languages

### Python (using requests)
```python
import requests

BASE_URL = "https://your-service.onrender.com"

# Get all questions
response = requests.get(f"{BASE_URL}/api/questions?include_answers=true")
data = response.json()

if data["success"]:
    questions = data["data"]
    for q in questions:
        print(f"Q: {q['question_text']}")
```

### JavaScript (using fetch)
```javascript
const BASE_URL = "https://your-service.onrender.com";

// Get all questions
async function getQuestions() {
  const response = await fetch(`${BASE_URL}/api/questions?include_answers=true`);
  const data = await response.json();
  
  if (data.success) {
    return data.data;
  }
}

// Create question
async function createQuestion(questionText, questionType = "single") {
  const response = await fetch(`${BASE_URL}/api/questions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question_text: questionText,
      question_type: questionType,
      required_answers: 1
    })
  });
  
  const data = await response.json();
  return data.data.question_id;
}
```

### C++ (using libcurl)
```cpp
#include <curl/curl.h>
#include <string>

std::string makeRequest(const std::string& url) {
    CURL* curl = curl_easy_init();
    std::string response;
    
    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_perform(curl);
        curl_easy_cleanup(curl);
    }
    return response;
}

// Usage
std::string questions = makeRequest(
    "https://your-service.onrender.com/api/questions?include_answers=true"
);
```

### cURL (Command Line)
```bash
# Get all questions
curl "https://your-service.onrender.com/api/questions?include_answers=true"

# Create question
curl -X POST "https://your-service.onrender.com/api/questions" \
  -H "Content-Type: application/json" \
  -d '{"question_text":"What is AI?","question_type":"single","required_answers":1}'

# Add answer
curl -X POST "https://your-service.onrender.com/api/questions/1/answers" \
  -H "Content-Type: application/json" \
  -d '{"answer_text":"Artificial Intelligence","is_correct":true}'
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "success": false,
  "message": "Error description here",
  "data": null
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad Request (missing required fields)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

### Error Handling Example
```python
import requests

BASE_URL = "https://your-service.onrender.com"

try:
    response = requests.get(f"{BASE_URL}/api/questions/999")
    data = response.json()
    
    if not data["success"]:
        print(f"Error: {data['message']}")
    else:
        print(f"Success: {data['data']}")
        
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

---

## 📌 Important Notes for AI Development

### Data Types
- **Boolean values**: In database stored as `1` (true) or `0` (false)
- **Timestamps**: Format is `YYYY-MM-DD HH:MM:SS`
- **IDs**: All IDs are integers and auto-increment

### Question Types
- `"single"` - Single choice (only one correct answer)
- `"multi"` - Multiple choice (multiple correct answers possible)

### Best Practices
1. Always check `success` field in response before using data
2. Use `include_answers=true` when you need complete question data
3. Log corrections for tracking wrong answers
4. Use search endpoint for finding questions by keyword
5. Handle network errors gracefully

### Limitations
- No built-in pagination (returns all results)
- No built-in authentication (add if needed)
- Case-sensitive search
- No rate limiting (add if needed for production)

---

## 🎯 Quick Reference: All Endpoints

```
HEALTH
GET    /api/health                           # Check API status

QUESTIONS
GET    /api/questions                        # Get all questions
GET    /api/questions/{id}                   # Get specific question
POST   /api/questions                        # Create question
PUT    /api/questions/{id}                   # Update question
DELETE /api/questions/{id}                   # Delete question
GET    /api/questions/search?q={text}        # Search questions

ANSWERS
GET    /api/questions/{id}/answers           # Get answers for question
POST   /api/questions/{id}/answers           # Add answer to question
PUT    /api/answers/{id}                     # Update answer
DELETE /api/answers/{id}                     # Delete answer

CORRECTIONS
GET    /api/corrections                      # Get correction log
POST   /api/corrections                      # Log correction
GET    /api/corrections/stats                # Get correction statistics
```

---

## 📞 Testing Your Deployment

Once deployed on Render.com, test with:

```bash
# Replace YOUR-SERVICE-NAME with your actual Render service name
curl https://YOUR-SERVICE-NAME.onrender.com/api/health
```

Expected response:
```json
{
  "success": true,
  "message": "API is running",
  "data": {"status": "healthy"}
}
```

---

**Last Updated**: November 2024
**API Version**: 1.0
**Database Type**: SQLite
**Framework**: Flask (Python)
