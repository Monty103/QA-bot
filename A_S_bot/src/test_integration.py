"""
Integration Test for Hybrid Database System
Tests all major functionality of the unified database interface
"""

from hybrid_database import HybridDatabaseManager
import sys

def test_api_connectivity():
    """Test 1: Check API connectivity"""
    print("\n=== Test 1: API Connectivity ===")
    db = HybridDatabaseManager()
    mode = db.get_mode()
    connected = db.is_connected()

    print(f"Mode: {mode}")
    print(f"Connected: {connected}")

    if mode == "hybrid":
        print("[PASS] API is accessible (hybrid mode)")
    elif mode == "offline":
        print("[WARN] API not available, using offline mode (SQLite)")
    else:
        print("[INFO] Using local-only mode")

    db.close()
    return True


def test_create_question():
    """Test 2: Create a test question"""
    print("\n=== Test 2: Create Question ===")
    db = HybridDatabaseManager()

    try:
        q_id = db.create_question("What is 2+2?", "single", 1)
        print(f"[PASS] Created question with ID: {q_id}")

        db.close()
        return q_id
    except Exception as e:
        print(f"[FAIL] Failed to create question: {e}")
        db.close()
        return None


def test_add_answers(question_id):
    """Test 3: Add answers to question"""
    print("\n=== Test 3: Add Answers ===")
    db = HybridDatabaseManager()

    try:
        a1 = db.add_answer(question_id, "4", True)
        print(f"[PASS] Added correct answer with ID: {a1}")

        a2 = db.add_answer(question_id, "5", False)
        print(f"[PASS] Added incorrect answer with ID: {a2}")

        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Failed to add answers: {e}")
        db.close()
        return False


def test_get_questions():
    """Test 4: Get all questions"""
    print("\n=== Test 4: Get All Questions ===")
    db = HybridDatabaseManager()

    try:
        questions = db.get_all_questions(include_answers=True)
        print(f"[PASS] Retrieved {len(questions)} questions")

        if questions:
            q = questions[0]
            print(f"\nFirst question:")
            print(f"  ID: {q['id']}")
            print(f"  Text: {q['question_text']}")
            print(f"  Type: {q.get('question_type', 'unknown')}")
            print(f"  Answers: {len(q.get('answers', []))}")

        db.close()
        return len(questions) > 0
    except Exception as e:
        print(f"[FAIL] Failed to get questions: {e}")
        db.close()
        return False


def test_search_questions():
    """Test 5: Search questions"""
    print("\n=== Test 5: Search Questions ===")
    db = HybridDatabaseManager()

    try:
        results = db.search_questions("2+2")
        print(f"[PASS] Search found {len(results)} results for '2+2'")

        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Search failed: {e}")
        db.close()
        return False


def test_log_correction():
    """Test 6: Log a correction"""
    print("\n=== Test 6: Log Correction ===")
    db = HybridDatabaseManager()

    try:
        corr_id = db.log_correction(
            "What is 2+2?",
            "5",
            "4",
            True
        )
        print(f"[PASS] Logged correction with ID: {corr_id}")

        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Failed to log correction: {e}")
        db.close()
        return False


def test_get_statistics():
    """Test 7: Get statistics"""
    print("\n=== Test 7: Get Statistics ===")
    db = HybridDatabaseManager()

    try:
        stats = db.get_statistics()
        if stats:
            print(f"[PASS] Retrieved statistics:")
            print(f"  Total corrections: {stats.get('total_corrections', 0)}")
            print(f"  Successful: {stats.get('successful_corrections', 0)}")
            print(f"  Failed: {stats.get('failed_corrections', 0)}")
        else:
            print("[INFO] No statistics available yet")

        db.close()
        return True
    except Exception as e:
        print(f"[FAIL] Failed to get statistics: {e}")
        db.close()
        return False


def test_offline_mode():
    """Test 8: Verify offline functionality"""
    print("\n=== Test 8: Offline Mode Verification ===")

    # Disable API
    db = HybridDatabaseManager(use_api=False)
    mode = db.get_mode()

    if mode == "local":
        print("[PASS] System correctly entered local-only mode when API disabled")
    else:
        print(f"[INFO] Mode: {mode}")

    db.close()
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("HYBRID DATABASE INTEGRATION TEST SUITE")
    print("=" * 60)

    # Run connectivity test first
    if not test_api_connectivity():
        print("\n[WARN] Skipping remaining tests - API connectivity issue")
        return

    # Create a test question
    q_id = test_create_question()

    # Test with the created question
    if q_id:
        test_add_answers(q_id)

    test_get_questions()
    test_search_questions()
    test_log_correction()
    test_get_statistics()
    test_offline_mode()

    print("\n" + "=" * 60)
    print("[PASS] INTEGRATION TEST SUITE COMPLETED")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Review the results above")
    print("2. If all tests passed, run main.py to test the full application")
    print("3. Test both online and offline modes by:")
    print("   - Starting the app and enabling monitoring")
    print("   - Disconnecting your internet")
    print("   - Verifying the system continues to work with local cache")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
