"""
Question Database - Read-only database access wrapper
Provides read-only access to questions and answers
"""

from fuzzywuzzy import fuzz
import sys
import os

# Add parent directory to path to import hybrid_database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class QuestionDatabase:
    """Read-only wrapper for question database access"""

    def __init__(self, db_path, api_url=None, use_api=True):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database
            api_url: URL to API server (optional)
            use_api: Whether to use API (default: True)
        """
        try:
            from hybrid_database import HybridDatabaseManager
            self.db = HybridDatabaseManager(
                sqlite_path=db_path,
                api_url=api_url,
                use_api=use_api,
                sync_interval=30
            )
            print("[*] Database initialized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize database: {e}")
            self.db = None

    def load_all_questions(self):
        """
        Load all questions from database into memory

        Returns:
            List of question dicts with answers
        """
        if not self.db:
            return []

        try:
            questions = self.db.get_all_questions(include_answers=True)
            print(f"[*] Loaded {len(questions)} questions from database")
            return questions
        except Exception as e:
            print(f"[ERROR] Failed to load questions: {e}")
            return []

    def find_question(self, question_text, threshold=85):
        """
        Find question by fuzzy matching

        Args:
            question_text: Text to search for
            threshold: Minimum similarity (0-100)

        Returns:
            List of matching questions or empty list
        """
        if not self.db:
            return []

        try:
            results = self.db.search_questions(question_text)

            # Filter by threshold
            matches = [q for q in results
                      if fuzz.ratio(question_text.lower(), q['question_text'].lower()) >= threshold]

            return matches
        except Exception as e:
            print(f"[WARN] Search failed: {e}")
            return []

    def get_question(self, question_id):
        """
        Get specific question by ID

        Args:
            question_id: Question ID to retrieve

        Returns:
            Question dict or None
        """
        if not self.db:
            return None

        try:
            question = self.db.get_question(question_id)
            return question
        except Exception as e:
            print(f"[WARN] Failed to get question {question_id}: {e}")
            return None

    def get_correct_answers(self, question_id):
        """
        Get correct answers for a question

        Args:
            question_id: Question ID

        Returns:
            List of correct answer texts
        """
        question = self.get_question(question_id)

        if not question:
            return []

        try:
            answers = question.get('answers', [])
            correct = [a['answer_text'] for a in answers if a.get('is_correct', False)]
            return correct
        except Exception as e:
            print(f"[WARN] Failed to get correct answers: {e}")
            return []

    def get_answers(self, question_id):
        """
        Get all answers for a question

        Args:
            question_id: Question ID

        Returns:
            List of answer dicts
        """
        question = self.get_question(question_id)

        if not question:
            return []

        try:
            return question.get('answers', [])
        except Exception as e:
            print(f"[WARN] Failed to get answers: {e}")
            return []

    def close(self):
        """Close database connection"""
        try:
            if self.db:
                self.db.close()
                print("[*] Database closed")
        except Exception as e:
            print(f"[WARN] Error closing database: {e}")

    # READ-ONLY - NO WRITE OPERATIONS
    # The following operations are NOT implemented:
    # - create_question()
    # - update_question()
    # - delete_question()
    # - add_answer()
    # - update_answer()
    # - delete_answer()
    # - log_correction()
    # - import_existing_data()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
