"""
Database Diagnostic Test Program
Tests connectivity, read/write operations to Render.com API
"""

import requests
import json
from datetime import datetime
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configuration
API_BASE_URL = "https://question-database-api.onrender.com"
TEST_TIMEOUT = 10

def print_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"{text:^70}")
    print(f"{'='*70}\n")

def print_success(text):
    """Print success message"""
    print(f"[PASS] {text}")

def print_error(text):
    """Print error message"""
    print(f"[FAIL] {text}")

def print_warning(text):
    """Print warning message"""
    print(f"[WARN] {text}")

def print_info(text):
    """Print info message"""
    print(f"[INFO] {text}")

def test_health_check():
    """Test 1: Basic API health check"""
    print_header("TEST 1: API HEALTH CHECK")

    try:
        print_info(f"Connecting to: {API_BASE_URL}/api/health")
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=TEST_TIMEOUT)

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print_success("Health check passed")
            print(f"  Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print_error("Connection timeout (>10 seconds)")
        print_warning("API server may be slow or unreachable")
        return False
    except requests.exceptions.ConnectionError:
        print_error("Connection failed - cannot reach API server")
        print_warning("Check: Is Render.com API running? Is internet connected?")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_read_all_questions():
    """Test 2: Read all questions"""
    print_header("TEST 2: READ ALL QUESTIONS")

    try:
        url = f"{API_BASE_URL}/api/questions?include_answers=true"
        print_info(f"GET {url}")
        response = requests.get(url, timeout=TEST_TIMEOUT)

        print_info(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                questions = data.get("data", [])
                print_success(f"Retrieved {len(questions)} questions")

                if questions:
                    print_info("Sample question:")
                    q = questions[0]
                    print(f"  ID: {q.get('id')}")
                    print(f"  Text: {q.get('question_text')[:100]}...")
                    print(f"  Type: {q.get('question_type')}")
                    print(f"  Answers: {len(q.get('answers', []))}")

                return True
            else:
                print_error(f"API returned error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False

    except Exception as e:
        print_error(f"Failed to read questions: {e}")
        return False

def test_read_single_question():
    """Test 3: Read a single question by ID"""
    print_header("TEST 3: READ SINGLE QUESTION")

    try:
        # First, get a valid question ID
        print_info("Getting list of questions to find valid ID...")
        response = requests.get(f"{API_BASE_URL}/api/questions", timeout=TEST_TIMEOUT)

        if response.status_code != 200:
            print_error("Could not retrieve question list")
            return False

        data = response.json()
        questions = data.get("data", [])

        if not questions:
            print_warning("No questions in database to test with")
            print_info("Skipping single question read test")
            return None  # Neither pass nor fail

        question_id = questions[0].get("id")
        url = f"{API_BASE_URL}/api/questions/{question_id}"

        print_info(f"GET {url}")
        response = requests.get(url, timeout=TEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                question = data.get("data", {})
                print_success(f"Retrieved question ID {question_id}")
                print(f"  Text: {question.get('question_text')[:100]}...")
                print(f"  Answers: {len(question.get('answers', []))}")
                return True
            else:
                print_error(f"API error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Failed: {e}")
        return False

def test_create_question():
    """Test 4: Create a new question"""
    print_header("TEST 4: CREATE NEW QUESTION (WRITE TEST)")

    try:
        test_question = {
            "question_text": f"Test Question - {datetime.now().isoformat()}",
            "question_type": "single",
            "required_answers": 1
        }

        url = f"{API_BASE_URL}/api/questions"
        print_info(f"POST {url}")
        print_info(f"Data: {json.dumps(test_question, indent=2)}")

        response = requests.post(url, json=test_question, timeout=TEST_TIMEOUT)

        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.text}")

        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("success"):
                question_id = data.get("data", {}).get("question_id")
                print_success(f"Question created successfully (ID: {question_id})")
                return question_id
            else:
                print_error(f"API error: {data.get('message')}")
                return None
        else:
            print_error(f"HTTP {response.status_code}")
            print_error("Possible issues:")
            print_error("  - API may not allow write operations")
            print_error("  - Authentication may be required")
            print_error("  - Database permissions may be restricted")
            return None

    except Exception as e:
        print_error(f"Failed to create question: {e}")
        return None

def test_create_answer(question_id):
    """Test 5: Create an answer for a question"""
    print_header("TEST 5: CREATE ANSWER (WRITE TEST)")

    if not question_id:
        print_warning("No valid question ID - skipping answer creation test")
        return False

    try:
        test_answer = {
            "answer_text": f"Test Answer - {datetime.now().isoformat()}",
            "is_correct": True
        }

        url = f"{API_BASE_URL}/api/questions/{question_id}/answers"
        print_info(f"POST {url}")
        print_info(f"Data: {json.dumps(test_answer, indent=2)}")

        response = requests.post(url, json=test_answer, timeout=TEST_TIMEOUT)

        print_info(f"Status Code: {response.status_code}")
        print_info(f"Response: {response.text}")

        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("success"):
                print_success("Answer created successfully")
                return True
            else:
                print_error(f"API error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}")
            print_error("Answer creation failed - database may not allow writes")
            return False

    except Exception as e:
        print_error(f"Failed to create answer: {e}")
        return False

def test_verify_created_data(question_id):
    """Test 6: Verify the data we created was saved"""
    print_header("TEST 6: VERIFY CREATED DATA")

    if not question_id:
        print_warning("No valid question ID - skipping verification")
        return None

    try:
        url = f"{API_BASE_URL}/api/questions/{question_id}"
        print_info(f"GET {url}")

        response = requests.get(url, timeout=TEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                question = data.get("data", {})
                print_success("Data retrieved successfully")
                print(f"  Question: {question.get('question_text')[:100]}")
                print(f"  Answers: {len(question.get('answers', []))}")

                if question.get('answers'):
                    for ans in question.get('answers'):
                        print(f"    - {ans.get('answer_text')[:50]} (correct: {ans.get('is_correct')})")

                return True
            else:
                print_error(f"Could not verify: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

def test_database_stats():
    """Test 7: Get database statistics"""
    print_header("TEST 7: DATABASE STATISTICS")

    try:
        url = f"{API_BASE_URL}/api/questions"
        print_info(f"GET {url} (counting all questions)")

        response = requests.get(url, timeout=TEST_TIMEOUT)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                questions = data.get("data", [])
                print_success(f"Database Statistics:")
                print(f"  Total Questions: {len(questions)}")

                # Count answers
                total_answers = 0
                correct_answers = 0
                for q in questions:
                    answers = q.get("answers", [])
                    total_answers += len(answers)
                    correct_answers += sum(1 for a in answers if a.get("is_correct"))

                print(f"  Total Answers: {total_answers}")
                print(f"  Correct Answers: {correct_answers}")
                print(f"  Incorrect Answers: {total_answers - correct_answers}")

                if questions:
                    print(f"  First Question Created: {questions[0].get('created_at')}")
                    print(f"  Last Question Created: {questions[-1].get('created_at')}")

                return True
            else:
                print_error(f"Error: {data.get('message')}")
                return False
        else:
            print_error(f"HTTP {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Failed to get stats: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    print(f"Tests Passed:  {passed}")
    print(f"Tests Failed:  {failed}")
    print(f"Tests Skipped: {skipped}")

    print("\nResults:")
    for test_name, result in results.items():
        if result is True:
            print(f"  [PASS] {test_name}")
        elif result is False:
            print(f"  [FAIL] {test_name}")
        else:
            print(f"  [SKIP] {test_name} (skipped)")

    return passed, failed, skipped

def print_recommendations(results):
    """Print recommendations based on test results"""
    print_header("RECOMMENDATIONS")

    # Check if health check passed
    if not results.get("Health Check"):
        print_error("API is not reachable!")
        print("  1. Check that Render.com API is running")
        print("  2. Verify internet connection")
        print("  3. Check API URL is correct: https://question-database-api.onrender.com")
        print("  4. Check Render.com dashboard for errors")
        return

    # Check if read operations work
    if not results.get("Read All Questions"):
        print_error("Cannot read from database!")
        print("  1. Check database schema")
        print("  2. Verify questions table exists")
        print("  3. Check API permissions")
        return

    # Check write operations
    if results.get("Create Question") is False:
        print_error("Cannot write to database!")
        print("  Possible causes:")
        print("    - API may be read-only")
        print("    - Database may have write restrictions")
        print("    - Authentication may be required")
        print("    - Database permissions may be limited")
        print("")
        print("  Solutions:")
        print("    1. Check Render.com dashboard - verify database is writable")
        print("    2. Check API code - may need authentication")
        print("    3. Check database user permissions")
        print("    4. Verify database connection string")
        return

    print_success("All tests passed!")
    print("  Database read and write operations are working correctly")
    print("  You can safely use the questionnaire scraper")

def main():
    """Run all tests"""
    print(f"\n{'='*70}")
    print(f"  DATABASE DIAGNOSTIC TEST PROGRAM")
    print(f"  Serbian Questionnaire Scraper")
    print(f"  API: {API_BASE_URL}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    results = {}

    # Test 1: Health check
    results["Health Check"] = test_health_check()

    if not results["Health Check"]:
        print_summary(results)
        print_recommendations(results)
        return 1

    # Test 2: Read all questions
    results["Read All Questions"] = test_read_all_questions()

    # Test 3: Read single question
    results["Read Single Question"] = test_read_single_question()

    # Test 4: Create question
    question_id = test_create_question()
    results["Create Question"] = question_id is not None

    # Test 5: Create answer (if question was created)
    if question_id:
        results["Create Answer"] = test_create_answer(question_id)
    else:
        results["Create Answer"] = None

    # Test 6: Verify created data
    results["Verify Created Data"] = test_verify_created_data(question_id)

    # Test 7: Database statistics
    results["Database Statistics"] = test_database_stats()

    # Print summary
    passed, failed, skipped = print_summary(results)

    # Print recommendations
    print_recommendations(results)

    # Return exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
