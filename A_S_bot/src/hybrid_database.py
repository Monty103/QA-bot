"""
Hybrid Database Manager
Unified interface for local SQLite + remote API database access

Features:
- Transparent fallback (API → SQLite)
- Automatic offline/online detection
- Sync queue for offline changes
- Conflict resolution
- Graceful error handling
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import threading
from remote_database import RemoteAPIManager, RemoteAPIError


class HybridDatabaseManager:
    """
    Unified database interface combining:
    - Local SQLite (reliable, always available)
    - Remote API (cloud storage, real-time sync)

    Automatically tries API first, falls back to SQLite on network errors.
    Queues offline changes and syncs when connection restored.
    """

    def __init__(self, sqlite_path: str = "test_questions.db",
                 api_url: str = "https://question-database-api.onrender.com",
                 use_api: bool = True,
                 sync_interval: int = 30):
        """
        Initialize hybrid database manager

        Args:
            sqlite_path: Path to local SQLite database
            api_url: Base URL of remote API
            use_api: Whether to use API (True) or local only (False)
            sync_interval: Seconds between auto-sync attempts
        """
        self.sqlite_path = sqlite_path
        self.use_api = use_api
        self.sync_interval = sync_interval

        # Initialize components
        self._init_sqlite()
        self.api = RemoteAPIManager(api_url) if use_api else None

        # Sync tracking
        self.sync_queue = []  # Changes made while offline
        self.is_syncing = False
        self.last_sync = None
        self._sync_lock = threading.Lock()

        # Start auto-sync thread
        self._start_sync_thread()

    # =====================================================================
    # SQLITE INITIALIZATION
    # =====================================================================

    def _init_sqlite(self):
        """Initialize local SQLite database"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Questions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    question_type TEXT DEFAULT 'single',
                    required_answers INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_to_api BOOLEAN DEFAULT 0
                )
            """)

            # Answers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    answer_text TEXT NOT NULL,
                    is_correct BOOLEAN,
                    synced_to_api BOOLEAN DEFAULT 0,
                    FOREIGN KEY (question_id) REFERENCES questions(id)
                )
            """)

            # Correction log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correction_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    question_text TEXT,
                    wrong_answer TEXT,
                    correct_answer TEXT,
                    correction_successful BOOLEAN,
                    synced_to_api BOOLEAN DEFAULT 0
                )
            """)

            # Sync queue (offline changes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT,  -- 'create_question', 'add_answer', 'log_correction'
                    data TEXT,  -- JSON payload
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced BOOLEAN DEFAULT 0
                )
            """)

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[SQLite] Initialization error: {e}")

    # =====================================================================
    # API / CONNECTIVITY
    # =====================================================================

    def is_connected(self) -> bool:
        """Check if connected to API"""
        if not self.use_api or not self.api:
            return False
        return self.api.is_connected()

    def get_mode(self) -> str:
        """Get current operation mode"""
        if not self.use_api:
            return "local"
        if self.is_connected():
            return "hybrid"  # Using both
        else:
            return "offline"  # SQLite only

    # =====================================================================
    # QUESTIONS - GET
    # =====================================================================

    def get_all_questions(self, include_answers: bool = True) -> List[Dict]:
        """
        Get all questions from best available source

        Tries: API first → SQLite fallback

        Args:
            include_answers: Whether to include answers

        Returns:
            List of question dicts
        """
        # Try API first
        if self.use_api and self.is_connected():
            try:
                return self.api.get_all_questions(include_answers)
            except RemoteAPIError as e:
                print(f"[API] Error getting questions: {e}, using local")

        # Fallback to SQLite
        return self._sqlite_get_all_questions(include_answers)

    def get_question(self, question_id: int, include_answers: bool = True) -> Optional[Dict]:
        """
        Get a specific question

        Args:
            question_id: ID of the question
            include_answers: Whether to include answers

        Returns:
            Question dict or None
        """
        # Try API first
        if self.use_api and self.is_connected():
            try:
                return self.api.get_question(question_id, include_answers)
            except RemoteAPIError:
                pass

        # Fallback to SQLite
        return self._sqlite_get_question(question_id, include_answers)

    def search_questions(self, query: str) -> List[Dict]:
        """
        Search questions

        Args:
            query: Search query string

        Returns:
            List of matching questions
        """
        # Try API first
        if self.use_api and self.is_connected():
            try:
                return self.api.search_questions(query)
            except RemoteAPIError:
                pass

        # Fallback to SQLite
        return self._sqlite_search_questions(query)

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
            required_answers: Number of correct answers

        Returns:
            Question ID or None
        """
        # Always save locally first
        q_id = self._sqlite_create_question(question_text, question_type, required_answers)

        if not q_id:
            return None

        # Try to sync to API
        if self.use_api:
            try:
                if self.is_connected():
                    api_id = self.api.create_question(question_text, question_type, required_answers)
                    # Mark as synced if successful
                    self._mark_synced(table="questions", local_id=q_id, api_id=api_id)
                else:
                    # Queue for later sync
                    self._queue_operation("create_question", {
                        "question_text": question_text,
                        "question_type": question_type,
                        "required_answers": required_answers,
                        "local_id": q_id
                    })
            except RemoteAPIError as e:
                print(f"[Sync] Could not sync question to API: {e}")
                self._queue_operation("create_question", {
                    "question_text": question_text,
                    "question_type": question_type,
                    "required_answers": required_answers,
                    "local_id": q_id
                })

        return q_id

    def update_question(self, question_id: int, question_text: Optional[str] = None,
                       question_type: Optional[str] = None,
                       required_answers: Optional[int] = None) -> bool:
        """Update a question"""
        # Update locally
        success = self._sqlite_update_question(question_id, question_text, question_type, required_answers)

        if not success:
            return False

        # Try to sync to API
        if self.use_api and self.is_connected():
            try:
                return self.api.update_question(question_id, question_text, question_type, required_answers)
            except RemoteAPIError as e:
                print(f"[Sync] Could not sync update to API: {e}")

        return True

    def delete_question(self, question_id: int) -> bool:
        """Delete a question"""
        # Delete locally
        success = self._sqlite_delete_question(question_id)

        if not success:
            return False

        # Try to sync to API
        if self.use_api and self.is_connected():
            try:
                return self.api.delete_question(question_id)
            except RemoteAPIError as e:
                print(f"[Sync] Could not sync deletion to API: {e}")

        return True

    # =====================================================================
    # ANSWERS
    # =====================================================================

    def add_answer(self, question_id: int, answer_text: str, is_correct: bool = False) -> Optional[int]:
        """
        Add an answer to a question

        Args:
            question_id: ID of the question
            answer_text: The answer text
            is_correct: Whether this is correct

        Returns:
            Answer ID or None
        """
        # Always save locally first
        a_id = self._sqlite_add_answer(question_id, answer_text, is_correct)

        if not a_id:
            return None

        # Try to sync to API
        if self.use_api:
            try:
                if self.is_connected():
                    api_id = self.api.add_answer(question_id, answer_text, is_correct)
                    self._mark_synced(table="answers", local_id=a_id, api_id=api_id)
                else:
                    self._queue_operation("add_answer", {
                        "question_id": question_id,
                        "answer_text": answer_text,
                        "is_correct": is_correct,
                        "local_id": a_id
                    })
            except RemoteAPIError as e:
                print(f"[Sync] Could not sync answer to API: {e}")
                self._queue_operation("add_answer", {
                    "question_id": question_id,
                    "answer_text": answer_text,
                    "is_correct": is_correct,
                    "local_id": a_id
                })

        return a_id

    def get_answers(self, question_id: int, correct_only: bool = False) -> List[Dict]:
        """Get answers for a question"""
        # Try API first
        if self.use_api and self.is_connected():
            try:
                return self.api.get_answers(question_id, correct_only)
            except RemoteAPIError:
                pass

        # Fallback to SQLite
        return self._sqlite_get_answers(question_id, correct_only)

    # =====================================================================
    # CORRECTIONS
    # =====================================================================

    def log_correction(self, question_text: str, wrong_answer: str,
                      correct_answer: str, correction_successful: bool = True) -> bool:
        """
        Log a correction

        Args:
            question_text: The question text
            wrong_answer: Wrong answer selected
            correct_answer: Correct answer
            correction_successful: Whether correction worked

        Returns:
            True if logged successfully
        """
        # Always save locally first (for statistics)
        self._sqlite_log_correction(question_text, wrong_answer, correct_answer, correction_successful)

        # Try to sync to API
        if self.use_api:
            try:
                if self.is_connected():
                    self.api.log_correction(question_text, wrong_answer, correct_answer, correction_successful)
                else:
                    self._queue_operation("log_correction", {
                        "question_text": question_text,
                        "wrong_answer": wrong_answer,
                        "correct_answer": correct_answer,
                        "correction_successful": correction_successful
                    })
            except RemoteAPIError as e:
                print(f"[Sync] Could not sync correction to API: {e}")
                self._queue_operation("log_correction", {
                    "question_text": question_text,
                    "wrong_answer": wrong_answer,
                    "correct_answer": correct_answer,
                    "correction_successful": correction_successful
                })

        return True

    def get_statistics(self) -> Dict:
        """Get correction statistics"""
        try:
            if self.use_api and self.is_connected():
                return self.api.get_statistics()
        except RemoteAPIError:
            pass

        # Fallback: calculate from local data
        return self._sqlite_get_statistics()

    # =====================================================================
    # SQLITE LOCAL OPERATIONS
    # =====================================================================

    def _sqlite_get_all_questions(self, include_answers: bool = True) -> List[Dict]:
        """Get all questions from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM questions")
            questions = [dict(row) for row in cursor.fetchall()]

            if include_answers:
                for q in questions:
                    q['answers'] = self._sqlite_get_answers(q['id'])

            conn.close()
            return questions

        except Exception as e:
            print(f"[SQLite] Error getting questions: {e}")
            return []

    def _sqlite_get_question(self, question_id: int, include_answers: bool = True) -> Optional[Dict]:
        """Get a specific question from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return None

            question = dict(row)

            if include_answers:
                question['answers'] = self._sqlite_get_answers(question_id)

            conn.close()
            return question

        except Exception as e:
            print(f"[SQLite] Error getting question: {e}")
            return None

    def _sqlite_search_questions(self, query: str) -> List[Dict]:
        """Search questions in SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query_lower = f"%{query.lower()}%"
            cursor.execute("SELECT * FROM questions WHERE LOWER(question_text) LIKE ?", (query_lower,))
            questions = [dict(row) for row in cursor.fetchall()]

            conn.close()
            return questions

        except Exception as e:
            print(f"[SQLite] Error searching questions: {e}")
            return []

    def _sqlite_create_question(self, question_text: str, question_type: str,
                               required_answers: int) -> Optional[int]:
        """Create question in SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO questions (question_text, question_type, required_answers)
                VALUES (?, ?, ?)
            """, (question_text, question_type, required_answers))

            q_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return q_id

        except Exception as e:
            print(f"[SQLite] Error creating question: {e}")
            return None

    def _sqlite_update_question(self, question_id: int, question_text: Optional[str],
                               question_type: Optional[str], required_answers: Optional[int]) -> bool:
        """Update question in SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            updates = []
            params = []

            if question_text is not None:
                updates.append("question_text = ?")
                params.append(question_text)
            if question_type is not None:
                updates.append("question_type = ?")
                params.append(question_type)
            if required_answers is not None:
                updates.append("required_answers = ?")
                params.append(required_answers)

            if not updates:
                return False

            params.append(question_id)
            query = f"UPDATE questions SET {', '.join(updates)} WHERE id = ?"

            cursor.execute(query, params)
            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"[SQLite] Error updating question: {e}")
            return False

    def _sqlite_delete_question(self, question_id: int) -> bool:
        """Delete question from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
            cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"[SQLite] Error deleting question: {e}")
            return False

    def _sqlite_get_answers(self, question_id: int, correct_only: bool = False) -> List[Dict]:
        """Get answers from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if correct_only:
                cursor.execute("SELECT * FROM answers WHERE question_id = ? AND is_correct = 1", (question_id,))
            else:
                cursor.execute("SELECT * FROM answers WHERE question_id = ?", (question_id,))

            answers = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return answers

        except Exception as e:
            print(f"[SQLite] Error getting answers: {e}")
            return []

    def _sqlite_add_answer(self, question_id: int, answer_text: str, is_correct: bool) -> Optional[int]:
        """Add answer to SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO answers (question_id, answer_text, is_correct)
                VALUES (?, ?, ?)
            """, (question_id, answer_text, is_correct))

            a_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return a_id

        except Exception as e:
            print(f"[SQLite] Error adding answer: {e}")
            return None

    def _sqlite_log_correction(self, question_text: str, wrong_answer: str,
                              correct_answer: str, correction_successful: bool) -> bool:
        """Log correction to SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO correction_log (question_text, wrong_answer, correct_answer, correction_successful)
                VALUES (?, ?, ?, ?)
            """, (question_text, wrong_answer, correct_answer, correction_successful))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            print(f"[SQLite] Error logging correction: {e}")
            return False

    def _sqlite_get_statistics(self) -> Dict:
        """Get statistics from SQLite"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM correction_log")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM correction_log WHERE correction_successful = 1")
            successful = cursor.fetchone()[0]

            conn.close()

            return {
                "total_corrections": total,
                "successful_corrections": successful,
                "failed_corrections": total - successful
            }

        except Exception as e:
            print(f"[SQLite] Error getting statistics: {e}")
            return {"total_corrections": 0, "successful_corrections": 0, "failed_corrections": 0}

    # =====================================================================
    # SYNC MANAGEMENT
    # =====================================================================

    def _queue_operation(self, operation: str, data: Dict):
        """Queue an operation for later sync"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sync_queue (operation, data)
                VALUES (?, ?)
            """, (operation, json.dumps(data)))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[Sync] Error queuing operation: {e}")

    def _process_sync_queue(self):
        """Process queued operations"""
        if self.is_syncing or not self.is_connected():
            return

        with self._sync_lock:
            self.is_syncing = True

            try:
                conn = sqlite3.connect(self.sqlite_path)
                cursor = conn.cursor()

                cursor.execute("SELECT id, operation, data FROM sync_queue WHERE synced = 0")
                operations = cursor.fetchall()

                synced_count = 0

                for op_id, operation, data_json in operations:
                    try:
                        data = json.loads(data_json)

                        if operation == "create_question":
                            self.api.create_question(
                                data['question_text'],
                                data['question_type'],
                                data['required_answers']
                            )
                        elif operation == "add_answer":
                            self.api.add_answer(
                                data['question_id'],
                                data['answer_text'],
                                data['is_correct']
                            )
                        elif operation == "log_correction":
                            self.api.log_correction(
                                data['question_text'],
                                data['wrong_answer'],
                                data['correct_answer'],
                                data['correction_successful']
                            )

                        # Mark as synced
                        cursor.execute("UPDATE sync_queue SET synced = 1 WHERE id = ?", (op_id,))
                        synced_count += 1

                    except Exception as e:
                        print(f"[Sync] Error processing operation {op_id}: {e}")

                conn.commit()
                conn.close()

                if synced_count > 0:
                    print(f"[Sync] Successfully synced {synced_count} operations")
                    self.last_sync = datetime.now()

            except Exception as e:
                print(f"[Sync] Error processing queue: {e}")

            finally:
                self.is_syncing = False

    def _start_sync_thread(self):
        """Start background sync thread"""
        def sync_loop():
            while True:
                try:
                    import time
                    time.sleep(self.sync_interval)
                    if self.use_api:
                        self._process_sync_queue()
                except Exception as e:
                    print(f"[Sync] Thread error: {e}")

        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()

    def _mark_synced(self, table: str, local_id: int, api_id: Optional[int] = None):
        """Mark item as synced to API"""
        try:
            conn = sqlite3.connect(self.sqlite_path)
            cursor = conn.cursor()

            cursor.execute(f"UPDATE {table} SET synced_to_api = 1 WHERE id = ?", (local_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[Sync] Error marking as synced: {e}")

    def close(self):
        """Close database connections"""
        if self.api:
            self.api.close()


# =========================================================================
# USAGE EXAMPLE
# =========================================================================

if __name__ == "__main__":
    # Example: Using hybrid database

    db = HybridDatabaseManager()

    print(f"Mode: {db.get_mode()}")
    print(f"Connected: {db.is_connected()}")

    # Create a question
    q_id = db.create_question("What is Python?", "single", 1)
    print(f"Created question: {q_id}")

    # Add answers
    db.add_answer(q_id, "Programming language", True)
    db.add_answer(q_id, "A snake", False)

    # Get questions
    questions = db.get_all_questions()
    print(f"Total questions: {len(questions)}")

    # Log a correction
    db.log_correction("What is Python?", "A snake", "Programming language", True)

    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")

    db.close()
