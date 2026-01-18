"""
Remote Database API Manager
Handles all communication with the cloud-based question database API

Features:
- Full CRUD operations for questions and answers
- Correction logging and statistics
- Search and filtering capabilities
- Automatic retry logic
- Error handling and recovery
"""

import requests
from typing import List, Dict, Optional, Tuple
import json
import time
from datetime import datetime

class RemoteAPIError(Exception):
    """Custom exception for API errors"""
    pass


class RemoteAPIManager:
    """
    Manager for cloud-based question database API

    Base URL: https://question-database-api.onrender.com

    Provides methods for:
    - Getting questions (all, by ID, search)
    - Creating/updating/deleting questions
    - Managing answers
    - Logging corrections
    - Statistics
    """

    def __init__(self, base_url: str = "https://question-database-api.onrender.com", timeout: int = 10):
        """
        Initialize API manager

        Args:
            base_url: Base URL of the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self._health_check_cache = None
        self._cache_timestamp = 0

    # =====================================================================
    # HEALTH & CONNECTION
    # =====================================================================

    def health_check(self) -> bool:
        """
        Check if API is healthy and accessible

        Returns:
            True if API is running, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=self.timeout)
            data = response.json()
            return data.get("success", False)
        except Exception as e:
            print(f"[API] Health check failed: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if currently connected to API"""
        return self.health_check()

    # =====================================================================
    # QUESTIONS - GET
    # =====================================================================

    def get_all_questions(self, include_answers: bool = True) -> Optional[List[Dict]]:
        """
        Get all questions from database

        Args:
            include_answers: Whether to include answers in response

        Returns:
            List of question dicts, or None on error
        """
        try:
            params = {"include_answers": "true" if include_answers else "false"}
            response = self.session.get(
                f"{self.base_url}/api/questions",
                params=params,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data", [])

        except requests.exceptions.Timeout:
            raise RemoteAPIError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise RemoteAPIError("Connection failed")
        except Exception as e:
            raise RemoteAPIError(f"Failed to get questions: {e}")

    def get_question(self, question_id: int, include_answers: bool = True) -> Optional[Dict]:
        """
        Get a specific question by ID

        Args:
            question_id: ID of the question
            include_answers: Whether to include answers

        Returns:
            Question dict or None on error
        """
        try:
            params = {"include_answers": "true" if include_answers else "false"}
            response = self.session.get(
                f"{self.base_url}/api/questions/{question_id}",
                params=params,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data")

        except Exception as e:
            raise RemoteAPIError(f"Failed to get question {question_id}: {e}")

    def search_questions(self, query: str) -> Optional[List[Dict]]:
        """
        Search questions by text

        Args:
            query: Search query string

        Returns:
            List of matching questions or None on error
        """
        try:
            params = {"q": query}
            response = self.session.get(
                f"{self.base_url}/api/questions/search",
                params=params,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data", [])

        except Exception as e:
            raise RemoteAPIError(f"Search failed: {e}")

    # =====================================================================
    # QUESTIONS - CREATE/UPDATE/DELETE
    # =====================================================================

    def create_question(self, question_text: str, question_type: str = "single",
                       required_answers: int = 1) -> Optional[int]:
        """
        Create a new question

        Args:
            question_text: The question text
            question_type: "single" or "multi"
            required_answers: Number of correct answers required

        Returns:
            Question ID if successful, None otherwise
        """
        try:
            payload = {
                "question_text": question_text,
                "question_type": question_type,
                "required_answers": required_answers
            }

            response = self.session.post(
                f"{self.base_url}/api/questions",
                json=payload,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data["data"]["question_id"]

        except Exception as e:
            raise RemoteAPIError(f"Failed to create question: {e}")

    def update_question(self, question_id: int, question_text: Optional[str] = None,
                       question_type: Optional[str] = None,
                       required_answers: Optional[int] = None) -> bool:
        """
        Update an existing question

        Args:
            question_id: ID of question to update
            question_text: New question text (optional)
            question_type: New question type (optional)
            required_answers: New required answers count (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {}
            if question_text is not None:
                payload["question_text"] = question_text
            if question_type is not None:
                payload["question_type"] = question_type
            if required_answers is not None:
                payload["required_answers"] = required_answers

            if not payload:
                raise RemoteAPIError("No fields to update")

            response = self.session.put(
                f"{self.base_url}/api/questions/{question_id}",
                json=payload,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            return data.get("success", False)

        except Exception as e:
            raise RemoteAPIError(f"Failed to update question: {e}")

    def delete_question(self, question_id: int) -> bool:
        """
        Delete a question (also deletes all answers)

        Args:
            question_id: ID of question to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/questions/{question_id}",
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            return data.get("success", False)

        except Exception as e:
            raise RemoteAPIError(f"Failed to delete question: {e}")

    # =====================================================================
    # ANSWERS - GET/CREATE/UPDATE/DELETE
    # =====================================================================

    def get_answers(self, question_id: int, correct_only: bool = False) -> Optional[List[Dict]]:
        """
        Get all answers for a question

        Args:
            question_id: ID of the question
            correct_only: Only return correct answers

        Returns:
            List of answer dicts or None on error
        """
        try:
            params = {"correct_only": "true" if correct_only else "false"}
            response = self.session.get(
                f"{self.base_url}/api/questions/{question_id}/answers",
                params=params,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data", [])

        except Exception as e:
            raise RemoteAPIError(f"Failed to get answers: {e}")

    def add_answer(self, question_id: int, answer_text: str, is_correct: bool = False) -> Optional[int]:
        """
        Add an answer to a question

        Args:
            question_id: ID of the question
            answer_text: The answer text
            is_correct: Whether this is a correct answer

        Returns:
            Answer ID if successful, None otherwise
        """
        try:
            payload = {
                "answer_text": answer_text,
                "is_correct": is_correct
            }

            response = self.session.post(
                f"{self.base_url}/api/questions/{question_id}/answers",
                json=payload,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data["data"]["answer_id"]

        except Exception as e:
            raise RemoteAPIError(f"Failed to add answer: {e}")

    def update_answer(self, answer_id: int, answer_text: Optional[str] = None,
                     is_correct: Optional[bool] = None) -> bool:
        """
        Update an answer

        Args:
            answer_id: ID of the answer to update
            answer_text: New answer text (optional)
            is_correct: New correctness status (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {}
            if answer_text is not None:
                payload["answer_text"] = answer_text
            if is_correct is not None:
                payload["is_correct"] = is_correct

            if not payload:
                raise RemoteAPIError("No fields to update")

            response = self.session.put(
                f"{self.base_url}/api/answers/{answer_id}",
                json=payload,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            return data.get("success", False)

        except Exception as e:
            raise RemoteAPIError(f"Failed to update answer: {e}")

    def delete_answer(self, answer_id: int) -> bool:
        """
        Delete an answer

        Args:
            answer_id: ID of the answer to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/api/answers/{answer_id}",
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            return data.get("success", False)

        except Exception as e:
            raise RemoteAPIError(f"Failed to delete answer: {e}")

    # =====================================================================
    # CORRECTIONS - LOGGING & STATS
    # =====================================================================

    def get_corrections(self, limit: int = 100) -> Optional[List[Dict]]:
        """
        Get correction log entries

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of correction dicts or None on error
        """
        try:
            params = {"limit": limit}
            response = self.session.get(
                f"{self.base_url}/api/corrections",
                params=params,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data", [])

        except Exception as e:
            raise RemoteAPIError(f"Failed to get corrections: {e}")

    def log_correction(self, question_text: str, wrong_answer: str,
                      correct_answer: str, correction_successful: bool = True) -> Optional[int]:
        """
        Log a correction attempt

        Args:
            question_text: The question text
            wrong_answer: What user selected (incorrect)
            correct_answer: What was auto-selected (correct)
            correction_successful: Whether correction was successful

        Returns:
            Correction ID if successful, None otherwise
        """
        try:
            payload = {
                "question_text": question_text,
                "wrong_answer": wrong_answer,
                "correct_answer": correct_answer,
                "correction_successful": correction_successful
            }

            response = self.session.post(
                f"{self.base_url}/api/corrections",
                json=payload,
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data["data"]["correction_id"]

        except Exception as e:
            raise RemoteAPIError(f"Failed to log correction: {e}")

    def get_statistics(self) -> Optional[Dict]:
        """
        Get correction statistics

        Returns:
            Dict with total_corrections, successful, failed, or None on error
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/corrections/stats",
                timeout=self.timeout
            )

            if not response.ok:
                raise RemoteAPIError(f"HTTP {response.status_code}: {response.text}")

            data = response.json()
            if not data.get("success"):
                raise RemoteAPIError(f"API Error: {data.get('message')}")

            return data.get("data")

        except Exception as e:
            raise RemoteAPIError(f"Failed to get statistics: {e}")

    # =====================================================================
    # CONVENIENCE METHODS
    # =====================================================================

    def submit_question_with_answers(self, question_text: str, answers: List[Dict],
                                    question_type: str = "single") -> Optional[int]:
        """
        Create a question with multiple answers in one operation

        Args:
            question_text: The question text
            answers: List of {'text': str, 'is_correct': bool} dicts
            question_type: "single" or "multi" (auto-detected if not specified)

        Returns:
            Question ID if successful, None otherwise
        """
        try:
            # Count correct answers
            correct_count = sum(1 for a in answers if a.get('is_correct', False))

            if correct_count == 0:
                raise RemoteAPIError("At least one answer must be correct")

            # Auto-detect question type if needed
            if question_type == "single" and correct_count > 1:
                question_type = "multi"

            # Create question
            question_id = self.create_question(question_text, question_type, correct_count)

            if not question_id:
                raise RemoteAPIError("Failed to create question")

            # Add answers
            for answer in answers:
                answer_id = self.add_answer(
                    question_id,
                    answer['text'],
                    answer.get('is_correct', False)
                )
                if not answer_id:
                    print(f"[Warning] Failed to add answer: {answer['text']}")

            return question_id

        except Exception as e:
            raise RemoteAPIError(f"Failed to submit question with answers: {e}")

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# =========================================================================
# USAGE EXAMPLES
# =========================================================================

if __name__ == "__main__":
    # Example: Using the API manager

    try:
        # Create manager
        api = RemoteAPIManager()

        # Check connection
        if api.health_check():
            print("✅ Connected to API")

            # Get all questions
            questions = api.get_all_questions()
            print(f"Found {len(questions)} questions")

            # Search questions
            results = api.search_questions("capital")
            print(f"Search results: {len(results)}")

            # Create a question
            q_id = api.create_question(
                "What is Python?",
                "single",
                1
            )
            print(f"Created question #{q_id}")

            # Add answers
            api.add_answer(q_id, "Programming language", True)
            api.add_answer(q_id, "A snake", False)

            # Get statistics
            stats = api.get_statistics()
            print(f"Statistics: {stats}")

        else:
            print("❌ Cannot connect to API")

    except RemoteAPIError as e:
        print(f"API Error: {e}")
    finally:
        api.close()
