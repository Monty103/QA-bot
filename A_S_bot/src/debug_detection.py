#!/usr/bin/env python3
"""
Debug Detection Script - Visualize what the OCR and bubble detection sees
Run this to capture a screenshot and see the detection results visually

Now with DYNAMIC region detection!
"""

import sys
import json
import cv2
import numpy as np
import pyautogui
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from question_reader import QuestionReader
from radio_detector import RadioButtonDetector
from region_detector import RegionDetector


def load_config(config_path):
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def draw_detection_results(img, question_region, answer_region, answers, question_text,
                           is_dynamic=False, anchors_found=None):
    """
    Draw detection results on image for visualization

    Args:
        img: Original screenshot (numpy array)
        question_region: Question region dict
        answer_region: Answer region dict
        answers: List of detected answers
        question_text: Extracted question text
        is_dynamic: Whether regions were detected dynamically
        anchors_found: Dict of which anchors were found

    Returns:
        Annotated image
    """
    # Convert to BGR if needed (for OpenCV drawing)
    if len(img.shape) == 3 and img.shape[2] == 3:
        result = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    else:
        result = img.copy()

    # Draw question region (blue rectangle)
    qx, qy = question_region['x'], question_region['y']
    qw, qh = question_region['width'], question_region['height']
    cv2.rectangle(result, (qx, qy), (qx + qw, qy + qh), (255, 0, 0), 2)
    label = "QUESTION (dynamic)" if is_dynamic else "QUESTION (fixed)"
    cv2.putText(result, label, (qx, qy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # Draw answer region (green rectangle)
    ax, ay = answer_region['x'], answer_region['y']
    aw, ah = answer_region['width'], answer_region['height']
    cv2.rectangle(result, (ax, ay), (ax + aw, ay + ah), (0, 255, 0), 2)
    label = "ANSWERS (dynamic)" if is_dynamic else "ANSWERS (fixed)"
    cv2.putText(result, label, (ax, ay - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Draw detected bubbles
    for i, answer in enumerate(answers):
        pos = answer['position']
        is_selected = answer.get('selected', False)
        bubble_type = answer.get('bubble_type', 'circle')
        text = answer.get('text', '')[:50]  # Truncate long text

        # Color based on selection state
        if is_selected:
            color = (0, 165, 255)  # Orange for selected
        else:
            color = (128, 128, 128)  # Gray for unselected

        # Draw bubble marker
        if bubble_type == 'circle':
            cv2.circle(result, pos, 15, color, 3)
        else:
            # Square for checkbox
            cv2.rectangle(result,
                         (pos[0] - 12, pos[1] - 12),
                         (pos[0] + 12, pos[1] + 12),
                         color, 3)

        # Draw answer number
        cv2.putText(result, str(i + 1), (pos[0] - 5, pos[1] + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Draw text label
        label = f"[{'SEL' if is_selected else '---'}] {bubble_type}: {text}"
        cv2.putText(result, label, (pos[0] + 25, pos[1] + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    # Draw info box at top
    info_y = 25
    cv2.rectangle(result, (5, 5), (700, 80), (0, 0, 0), -1)

    # Question text
    if question_text:
        cv2.putText(result, f"Q: {question_text[:70]}", (10, info_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Detection method
    method = "DYNAMIC (anchor-based)" if is_dynamic else "FIXED (config values)"
    cv2.putText(result, f"Method: {method}", (10, info_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Anchors found
    if anchors_found:
        anchors_str = ", ".join([k for k, v in anchors_found.items() if v])
        cv2.putText(result, f"Anchors: {anchors_str}", (10, info_y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    return result


def main():
    """Main debug function"""
    print("=" * 60)
    print("OCR & Bubble Detection Debug Tool")
    print("With DYNAMIC Region Detection")
    print("=" * 60)

    # Load config
    config_path = Path(__file__).parent.parent / "docs" / "config.json"
    if not config_path.exists():
        print(f"[ERROR] Config not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    print(f"[*] Loaded config from: {config_path}")

    # Initialize detectors
    tesseract_path = config['tesseract_path']
    ocr_language = config.get('ocr_language', 'srp+eng')

    reader = QuestionReader(tesseract_path, ocr_language)
    detector = RadioButtonDetector(tesseract_path, ocr_language)
    region_detector = RegionDetector()

    # Fixed regions from config (fallback)
    fixed_question_region = config.get('question_region', {
        'x': 30, 'y': 125, 'width': 900, 'height': 50
    })
    fixed_answer_region = config.get('answer_region', {
        'x': 25, 'y': 160, 'width': 900, 'height': 200
    })

    # Countdown before capture
    print("\n[*] Capturing screenshot in 3 seconds...")
    print("[*] Make sure the questionnaire is visible on screen!")
    import time
    for i in range(3, 0, -1):
        print(f"    {i}...")
        time.sleep(1)

    # Capture screenshot
    print("[*] Capturing...")
    screenshot = pyautogui.screenshot()
    img = np.array(screenshot)

    print(f"[*] Screenshot size: {img.shape[1]}x{img.shape[0]}")

    # ==========================================
    # DYNAMIC REGION DETECTION
    # ==========================================
    print("\n" + "=" * 40)
    print("DYNAMIC REGION DETECTION")
    print("=" * 40)

    regions = region_detector.detect_regions(screenshot)

    dynamic_question_region = regions.get('question_region', fixed_question_region)
    dynamic_answer_region = regions.get('answer_region', fixed_answer_region)
    anchors_found = regions.get('anchors_found', {})

    print(f"[*] Dynamic question region: {dynamic_question_region}")
    print(f"[*] Dynamic answer region: {dynamic_answer_region}")
    print(f"[*] Anchors found: {anchors_found}")

    # Extract question with dynamic regions
    print("\n[*] Extracting question text (dynamic regions)...")
    raw_text_dyn = reader.extract_question(screenshot, dynamic_question_region)
    question_text_dyn = reader.clean_text(raw_text_dyn) if raw_text_dyn else ""
    print(f"[*] Question: {question_text_dyn[:80] if question_text_dyn else '(empty)'}")

    # Detect bubbles with dynamic regions
    print("\n[*] Detecting bubbles (dynamic regions)...")
    answers_dyn = detector.find_radio_buttons(screenshot, dynamic_answer_region)
    print(f"[*] Found {len(answers_dyn)} bubbles")

    for i, ans in enumerate(answers_dyn):
        status = "SELECTED" if ans['selected'] else "unselected"
        print(f"    [{i+1}] {ans['bubble_type']:6s} | {status:10s} | text=\"{ans['text'][:40]}\"")

    # ==========================================
    # FIXED REGION DETECTION (for comparison)
    # ==========================================
    print("\n" + "=" * 40)
    print("FIXED REGION DETECTION (comparison)")
    print("=" * 40)

    print(f"[*] Fixed question region: {fixed_question_region}")
    print(f"[*] Fixed answer region: {fixed_answer_region}")

    # Extract question with fixed regions
    raw_text_fix = reader.extract_question(screenshot, fixed_question_region)
    question_text_fix = reader.clean_text(raw_text_fix) if raw_text_fix else ""
    print(f"[*] Question: {question_text_fix[:80] if question_text_fix else '(empty)'}")

    # Detect bubbles with fixed regions
    answers_fix = detector.find_radio_buttons(screenshot, fixed_answer_region)
    print(f"[*] Found {len(answers_fix)} bubbles")

    # ==========================================
    # SAVE RESULTS
    # ==========================================
    print("\n[*] Creating visualizations...")

    output_dir = Path(__file__).parent.parent / "debug_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save dynamic detection result
    annotated_dyn = draw_detection_results(
        img, dynamic_question_region, dynamic_answer_region,
        answers_dyn, question_text_dyn, is_dynamic=True, anchors_found=anchors_found
    )
    dyn_path = output_dir / f"dynamic_{timestamp}.png"
    cv2.imwrite(str(dyn_path), annotated_dyn)
    print(f"[*] Saved DYNAMIC detection: {dyn_path}")

    # Save fixed detection result
    annotated_fix = draw_detection_results(
        img, fixed_question_region, fixed_answer_region,
        answers_fix, question_text_fix, is_dynamic=False
    )
    fix_path = output_dir / f"fixed_{timestamp}.png"
    cv2.imwrite(str(fix_path), annotated_fix)
    print(f"[*] Saved FIXED detection: {fix_path}")

    # Save original
    orig_path = output_dir / f"original_{timestamp}.png"
    cv2.imwrite(str(orig_path), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print(f"[*] Saved original: {orig_path}")

    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)
    print(f"{'':20s} | {'DYNAMIC':^15s} | {'FIXED':^15s}")
    print("-" * 55)
    print(f"{'Bubbles found':20s} | {len(answers_dyn):^15d} | {len(answers_fix):^15d}")
    print(f"{'Question detected':20s} | {'Yes' if question_text_dyn else 'No':^15s} | {'Yes' if question_text_fix else 'No':^15s}")
    print(f"{'Region Y (question)':20s} | {dynamic_question_region['y']:^15d} | {fixed_question_region['y']:^15d}")
    print(f"{'Region Y (answers)':20s} | {dynamic_answer_region['y']:^15d} | {fixed_answer_region['y']:^15d}")
    print("=" * 60)

    # Recommendation
    if len(answers_dyn) > len(answers_fix):
        print("\n>>> DYNAMIC detection found more bubbles - recommended!")
    elif len(answers_dyn) < len(answers_fix):
        print("\n>>> FIXED detection found more bubbles - check anchor templates")
    else:
        print("\n>>> Both methods found same number of bubbles")

    print(f"\nCheck debug_output folder: {output_dir}")

    # Open the dynamic result
    try:
        import os
        os.startfile(str(dyn_path))
    except:
        print(f"[*] Open manually: {dyn_path}")


if __name__ == '__main__':
    main()
