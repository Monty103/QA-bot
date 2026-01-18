#!/usr/bin/env python3
"""
Region Calibration Tool
Click on the screen to define question and answer regions manually.

Instructions:
1. Run this script
2. Position your questionnaire on screen
3. Follow the prompts to click on corners of each region
4. The script will update your config.json automatically
"""

import sys
import json
import time
import pyautogui
from pathlib import Path
from pynput import mouse

# Disable pyautogui fail-safe for this tool
pyautogui.FAILSAFE = False


class RegionCalibrator:
    """Interactive tool to calibrate screen regions by clicking"""

    def __init__(self, config_path):
        self.config_path = Path(config_path)
        self.clicks = []
        self.waiting_for_click = False
        self.listener = None

    def load_config(self):
        """Load existing config"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_config(self, config):
        """Save config back to file"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def wait_for_click(self):
        """Wait for a single mouse click and return position"""
        self.waiting_for_click = True
        self.clicks = []

        def on_click(x, y, button, pressed):
            if pressed and self.waiting_for_click:
                self.clicks.append((x, y))
                self.waiting_for_click = False
                return False  # Stop listener

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

        return self.clicks[0] if self.clicks else None

    def calibrate(self):
        """Run interactive calibration"""
        print("=" * 60)
        print("REGION CALIBRATION TOOL")
        print("=" * 60)
        print()
        print("This tool will help you define the exact screen regions")
        print("for question text and answer bubbles.")
        print()
        print("INSTRUCTIONS:")
        print("  1. Position your questionnaire window on screen")
        print("  2. Follow the prompts below")
        print("  3. Click on the indicated corners when prompted")
        print()
        input("Press ENTER when ready to start...")

        # ==========================================
        # QUESTION REGION
        # ==========================================
        print()
        print("-" * 40)
        print("STEP 1: Define QUESTION region")
        print("-" * 40)
        print()
        print("The question region is where the question TEXT appears.")
        print("(NOT the answers, just the question itself)")
        print()

        # Top-left corner
        print(">>> Click on the TOP-LEFT corner of the question text area...")
        q_top_left = self.wait_for_click()
        if not q_top_left:
            print("[ERROR] No click detected")
            return
        print(f"    Got: ({q_top_left[0]}, {q_top_left[1]})")

        # Bottom-right corner
        print()
        print(">>> Click on the BOTTOM-RIGHT corner of the question text area...")
        q_bottom_right = self.wait_for_click()
        if not q_bottom_right:
            print("[ERROR] No click detected")
            return
        print(f"    Got: ({q_bottom_right[0]}, {q_bottom_right[1]})")

        # Calculate question region
        question_region = {
            'x': min(q_top_left[0], q_bottom_right[0]),
            'y': min(q_top_left[1], q_bottom_right[1]),
            'width': abs(q_bottom_right[0] - q_top_left[0]),
            'height': abs(q_bottom_right[1] - q_top_left[1])
        }

        print()
        print(f"[*] Question region: {question_region}")

        # ==========================================
        # ANSWER REGION
        # ==========================================
        print()
        print("-" * 40)
        print("STEP 2: Define ANSWER region")
        print("-" * 40)
        print()
        print("The answer region contains ALL the answer options")
        print("(including the bubbles/checkboxes and their text)")
        print()

        # Top-left corner
        print(">>> Click on the TOP-LEFT corner of the answers area...")
        print("    (Click just above and to the left of the FIRST answer bubble)")
        a_top_left = self.wait_for_click()
        if not a_top_left:
            print("[ERROR] No click detected")
            return
        print(f"    Got: ({a_top_left[0]}, {a_top_left[1]})")

        # Bottom-right corner
        print()
        print(">>> Click on the BOTTOM-RIGHT corner of the answers area...")
        print("    (Click below and to the right of the LAST answer text)")
        a_bottom_right = self.wait_for_click()
        if not a_bottom_right:
            print("[ERROR] No click detected")
            return
        print(f"    Got: ({a_bottom_right[0]}, {a_bottom_right[1]})")

        # Calculate answer region
        answer_region = {
            'x': min(a_top_left[0], a_bottom_right[0]),
            'y': min(a_top_left[1], a_bottom_right[1]),
            'width': abs(a_bottom_right[0] - a_top_left[0]),
            'height': abs(a_bottom_right[1] - a_top_left[1])
        }

        print()
        print(f"[*] Answer region: {answer_region}")

        # ==========================================
        # SUMMARY AND SAVE
        # ==========================================
        print()
        print("=" * 60)
        print("CALIBRATION COMPLETE")
        print("=" * 60)
        print()
        print("New regions:")
        print(f"  Question: x={question_region['x']}, y={question_region['y']}, "
              f"w={question_region['width']}, h={question_region['height']}")
        print(f"  Answers:  x={answer_region['x']}, y={answer_region['y']}, "
              f"w={answer_region['width']}, h={answer_region['height']}")
        print()

        # Ask to save
        save = input("Save these regions to config.json? (y/n): ").strip().lower()

        if save == 'y':
            try:
                config = self.load_config()
                config['question_region'] = question_region
                config['answer_region'] = answer_region
                # Disable dynamic regions since we're using manual calibration
                config['use_dynamic_regions'] = False
                self.save_config(config)
                print()
                print("[*] Config saved successfully!")
                print(f"[*] File: {self.config_path}")
                print()
                print("NOTE: Dynamic region detection has been DISABLED.")
                print("      Your manual regions will now be used.")
            except Exception as e:
                print(f"[ERROR] Failed to save config: {e}")
        else:
            print()
            print("[*] Not saved. You can manually add these values to config.json:")
            print()
            print(f'"question_region": {json.dumps(question_region, indent=2)}')
            print()
            print(f'"answer_region": {json.dumps(answer_region, indent=2)}')


def main():
    """Main entry point"""
    config_path = Path(__file__).parent.parent / "docs" / "config.json"

    if not config_path.exists():
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)

    calibrator = RegionCalibrator(config_path)
    calibrator.calibrate()


if __name__ == '__main__':
    main()
