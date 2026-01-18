#!/usr/bin/env python3
"""
Automatic Questionnaire Helper - Background Script
Monitors questionnaires and auto-corrects wrong answers
Runs invisibly in background
"""

import sys
import json
import time
import argparse
import pyautogui
from pathlib import Path

from question_reader import QuestionReader
from radio_detector import RadioButtonDetector
from click_monitor import ClickMonitor, find_closest_answer, find_answer_by_text
from question_database import QuestionDatabase
from region_detector import RegionDetector


class QuestionnaireHelper:
    """Main helper script for automatic questionnaire correction"""

    def __init__(self, config_path):
        """
        Initialize the helper

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)

        # Initialize components
        tesseract_path = self.config['tesseract_path']
        self.reader = QuestionReader(tesseract_path)
        self.detector = RadioButtonDetector(tesseract_path)
        self.db = QuestionDatabase(
            self.config['database_file'],
            self.config.get('api_url'),
            self.config.get('use_api', True)
        )

        # Dynamic region detection
        self.use_dynamic_regions = self.config.get('use_dynamic_regions', True)
        self.region_detector = RegionDetector() if self.use_dynamic_regions else None

        # Fallback/manual configuration regions
        self.question_region = self.config.get('question_region', {
            'x': 30, 'y': 125, 'width': 900, 'height': 50
        })
        self.answer_region = self.config.get('answer_region', {
            'x': 25, 'y': 160, 'width': 900, 'height': 200
        })

        # Region detection state
        self.regions_detected = False
        self.region_detection_interval = 2.0  # Re-detect regions every 2 seconds
        self.last_region_detection = 0

        # Initialize click monitor (will be updated when regions are detected)
        self.monitor = ClickMonitor(self.answer_region)

        # Load all questions into memory
        self.all_questions = self.db.load_all_questions()

        # State tracking
        self.current_question_text = None
        self.current_question_id = None
        self.current_correct_answers = []
        self.last_ocr_time = 0
        self.ocr_interval = 0.5  # Re-read question every 0.5 seconds

        # Statistics
        self.corrections_made = 0
        self.questions_processed = 0

    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"[*] Configuration loaded from {config_path}")
            return config
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            sys.exit(1)

    def _update_regions(self, screenshot):
        """
        Update regions using dynamic detection

        Args:
            screenshot: Current screenshot
        """
        if not self.use_dynamic_regions or not self.region_detector:
            return

        current_time = time.time()
        if current_time - self.last_region_detection < self.region_detection_interval:
            return

        try:
            regions = self.region_detector.detect_regions(screenshot)

            if regions:
                new_q_region = regions.get('question_region')
                new_a_region = regions.get('answer_region')

                if new_q_region and new_a_region:
                    # Check if regions changed significantly
                    q_changed = (abs(self.question_region.get('y', 0) - new_q_region['y']) > 20 or
                                not self.regions_detected)
                    a_changed = (abs(self.answer_region.get('y', 0) - new_a_region['y']) > 20 or
                                not self.regions_detected)

                    if q_changed or a_changed:
                        self.question_region = new_q_region
                        self.answer_region = new_a_region
                        self.regions_detected = True

                        if self.config.get('show_debug_messages', False):
                            print(f"[*] Updated regions dynamically:")
                            print(f"    Question: y={new_q_region['y']}, h={new_q_region['height']}")
                            print(f"    Answers: y={new_a_region['y']}, h={new_a_region['height']}")

        except Exception as e:
            if self.config.get('show_debug_messages', False):
                print(f"[WARN] Dynamic region detection failed: {e}")

        self.last_region_detection = current_time

    def run(self):
        """Main monitoring loop"""
        print("[*] Questionnaire Helper Started")
        if self.use_dynamic_regions:
            print("[*] Using DYNAMIC region detection (anchor-based)")
        else:
            print(f"[*] Using FIXED regions from config")
            print(f"[*] Question region: x={self.question_region['x']}, y={self.question_region['y']}")
            print(f"[*] Answer region: x={self.answer_region['x']}, y={self.answer_region['y']}")
        print("[*] Monitoring active... Press Ctrl+C to stop\n")

        # Start click monitor
        self.monitor.start()

        try:
            while True:
                # STEP 1: Capture screenshot
                screenshot = pyautogui.screenshot()

                # STEP 1.5: Update regions dynamically if enabled
                self._update_regions(screenshot)

                # STEP 2: Read question text
                current_time = time.time()
                if current_time - self.last_ocr_time >= self.ocr_interval:
                    raw_text = self.reader.extract_question(screenshot, self.question_region)
                    question_text = self.reader.clean_text(raw_text) if raw_text else ""

                    # STEP 3: Check if question changed
                    if question_text and question_text != self.current_question_text:
                        # Show debug info if enabled
                        if self.config.get('show_debug_messages', False) and raw_text != question_text:
                            print(f"[DEBUG] Raw OCR: {raw_text[:80]}")
                            print(f"[DEBUG] Cleaned: {question_text[:80]}")
                        self._on_new_question(question_text)

                    self.last_ocr_time = current_time

                # STEP 4: Detect radio buttons in current screenshot
                answers = self.detector.find_radio_buttons(screenshot, self.answer_region)

                # STEP 5: Monitor for clicks
                if self.monitor.check_click():
                    clicked_position = self.monitor.get_click_position()
                    self._on_user_click(clicked_position, answers)
                    self.monitor.reset_click()

                # STEP 6: Sleep for monitoring interval
                time.sleep(0.1)  # Check frequently, but don't consume CPU

        except KeyboardInterrupt:
            print("\n[*] Helper stopped by user")
            self._print_summary()
            self.cleanup()

    def _on_new_question(self, question_text):
        """Handle new question detected"""
        print(f"\n[?] New Question: {question_text[:60]}...")

        self.current_question_text = question_text
        self.questions_processed += 1

        # Search for question in database
        results = self.db.find_question(question_text)

        if results:
            self.current_question_id = results[0]['id']
            self.current_correct_answers = self.db.get_correct_answers(self.current_question_id)
            print(f"[✓] Correct Answer(s): {', '.join(self.current_correct_answers)}")
        else:
            print(f"[!] Question not found in database")
            self.current_question_id = None
            self.current_correct_answers = []

    def _on_user_click(self, clicked_position, answers):
        """Handle user click in answer region"""
        print(f"[!] User clicked at position {clicked_position}")

        # Find which answer was clicked
        clicked_answer = find_closest_answer(clicked_position, answers)

        if not clicked_answer:
            print("[WARN] Could not identify clicked answer")
            return

        clicked_text = clicked_answer['text']
        print(f"[!] Clicked Answer: {clicked_text}")

        # Check if it's correct
        if self.current_correct_answers:
            is_correct = any(
                self._fuzzy_match(clicked_text, correct, threshold=80)
                for correct in self.current_correct_answers
            )

            if is_correct:
                print(f"[✓] Correct! (no action needed)")
            else:
                # WRONG - AUTO-CORRECT
                print(f"[!] Wrong answer! Auto-correcting...")
                self._auto_correct(answers)
                self.corrections_made += 1
        else:
            print("[WARN] No correct answers in database")

    def _auto_correct(self, answers):
        """Auto-correct by clicking the correct answer"""
        if not self.current_correct_answers:
            print("[WARN] No correct answers to click")
            return

        # Find the correct answer button
        correct_answer = find_answer_by_text(self.current_correct_answers[0], answers)

        if correct_answer:
            # Click the correct answer
            position = correct_answer['position']
            print(f"[>] Clicking correct answer at {position}")

            try:
                pyautogui.click(position[0], position[1])
                time.sleep(0.3)  # Wait for button effect
                print(f"[>] Auto-correction complete")
            except Exception as e:
                print(f"[ERROR] Failed to click: {e}")
        else:
            print("[WARN] Could not locate correct answer button")

    def _fuzzy_match(self, text1, text2, threshold=80):
        """Check if two texts match using fuzzy matching"""
        from fuzzywuzzy import fuzz
        score = fuzz.ratio(text1.lower(), text2.lower())
        return score >= threshold

    def _print_summary(self):
        """Print session summary"""
        print("\n" + "="*50)
        print("Session Summary:")
        print(f"  Questions processed: {self.questions_processed}")
        print(f"  Auto-corrections made: {self.corrections_made}")
        if self.questions_processed > 0:
            success_rate = (1 - self.corrections_made / self.questions_processed) * 100
            print(f"  Initial success rate: {success_rate:.1f}%")
        print("="*50)

    def cleanup(self):
        """Cleanup resources"""
        print("[*] Cleaning up...")
        try:
            self.monitor.stop()
            self.db.close()
            print("[*] Cleanup complete")
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Automatic Questionnaire Helper',
        epilog='Example: python helper.py --config ../docs/config.json'
    )
    parser.add_argument(
        '--config',
        default='../docs/config.json',
        help='Path to configuration file (default: ../docs/config.json)'
    )

    args = parser.parse_args()

    # Verify config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Configuration file not found: {config_path}")
        sys.exit(1)

    # Create and run helper
    helper = QuestionnaireHelper(str(config_path))
    helper.run()


if __name__ == '__main__':
    main()
