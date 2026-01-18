"""
Performance Benchmark - C++ vs Python
Measures actual performance improvements
"""

import numpy as np
import cv2
import time
from typing import Tuple

# Import hybrid modules
from hybrid_ocr import HybridOCRPreprocessor, is_cpp_available as ocr_cpp_available
from hybrid_color_detection import HybridColorDetector, is_cpp_available as color_cpp_available


def create_test_image(size: Tuple[int, int] = (400, 600)) -> np.ndarray:
    """Create realistic test image with text-like patterns"""
    img = np.random.randint(200, 255, (*size, 3), dtype=np.uint8)

    # Add some "text-like" dark regions
    for _ in range(20):
        x = np.random.randint(0, size[1] - 100)
        y = np.random.randint(0, size[0] - 30)
        w = np.random.randint(50, 100)
        h = np.random.randint(15, 30)
        cv2.rectangle(img, (x, y), (x+w, y+h), (50, 50, 50), -1)

    return img


def create_test_image_with_blocks(size: Tuple[int, int] = (400, 600)) -> np.ndarray:
    """Create test image with colored blocks"""
    img = np.ones((*size, 3), dtype=np.uint8) * 240  # Light gray background

    # Add green blocks
    for i in range(4):
        y = 50 + i * 80
        cv2.rectangle(img, (50, y), (550, y+50), (0, 200, 0), -1)  # Green

    # Add red blocks
    for i in range(3):
        y = 70 + i * 100
        cv2.rectangle(img, (100, y), (500, y+40), (0, 0, 200), -1)  # Red

    return img


def benchmark_ocr_preprocessing(iterations: int = 50):
    """Benchmark OCR preprocessing"""
    print("\n" + "="*60)
    print("OCR PREPROCESSING BENCHMARK")
    print("="*60)

    img = create_test_image()
    print(f"Test image size: {img.shape}")
    print(f"Iterations: {iterations}")
    print()

    preprocessor_cpp = HybridOCRPreprocessor(use_cpp=True)
    preprocessor_py = HybridOCRPreprocessor(use_cpp=False)

    # Warmup
    for _ in range(3):
        _ = preprocessor_cpp.preprocess_for_ocr(img)
        _ = preprocessor_py.preprocess_for_ocr(img)

    # Benchmark C++
    if ocr_cpp_available():
        print("[C++ Mode] Starting benchmark...")
        start = time.perf_counter()
        for _ in range(iterations):
            result_cpp = preprocessor_cpp.preprocess_for_ocr(img)
        time_cpp = (time.perf_counter() - start) / iterations * 1000
        print(f"✅ C++ Average: {time_cpp:.2f}ms per image")
    else:
        print("❌ C++ not available (extensions not built)")
        time_cpp = None

    # Benchmark Python
    print("[Python Mode] Starting benchmark...")
    start = time.perf_counter()
    for _ in range(iterations):
        result_py = preprocessor_py.preprocess_for_ocr(img)
    time_py = (time.perf_counter() - start) / iterations * 1000
    print(f"✅ Python Average: {time_py:.2f}ms per image")

    # Results
    print()
    print("Results:")
    print("-" * 60)
    if time_cpp:
        speedup = time_py / time_cpp
        improvement = ((time_py - time_cpp) / time_py) * 100
        print(f"C++ Time:     {time_cpp:.2f}ms")
        print(f"Python Time:  {time_py:.2f}ms")
        print(f"Speedup:      {speedup:.2f}x")
        print(f"Improvement:  {improvement:.1f}% faster")
    else:
        print(f"Python Time:  {time_py:.2f}ms")
        print("Build C++ extensions to see comparison!")


def benchmark_color_detection(iterations: int = 50):
    """Benchmark color block detection"""
    print("\n" + "="*60)
    print("COLOR BLOCK DETECTION BENCHMARK")
    print("="*60)

    img = create_test_image_with_blocks()
    print(f"Test image size: {img.shape}")
    print(f"Iterations: {iterations}")
    print()

    detector_cpp = HybridColorDetector(use_cpp=True)
    detector_py = HybridColorDetector(use_cpp=False)

    # Warmup
    for _ in range(3):
        _ = detector_cpp.detect_green_blocks(img)
        _ = detector_cpp.detect_red_blocks(img)
        _ = detector_py.detect_green_blocks(img)
        _ = detector_py.detect_red_blocks(img)

    # Benchmark C++ - Green
    if color_cpp_available():
        print("[C++ Mode] Benchmarking green block detection...")
        start = time.perf_counter()
        for _ in range(iterations):
            result_cpp_green = detector_cpp.detect_green_blocks(img)
        time_cpp_green = (time.perf_counter() - start) / iterations * 1000

        print("[C++ Mode] Benchmarking red block detection...")
        start = time.perf_counter()
        for _ in range(iterations):
            result_cpp_red = detector_cpp.detect_red_blocks(img)
        time_cpp_red = (time.perf_counter() - start) / iterations * 1000

        time_cpp = time_cpp_green + time_cpp_red
        print(f"✅ C++ Green: {time_cpp_green:.2f}ms, Red: {time_cpp_red:.2f}ms, Total: {time_cpp:.2f}ms")
    else:
        print("❌ C++ not available (extensions not built)")
        time_cpp = None

    # Benchmark Python
    print("[Python Mode] Benchmarking green block detection...")
    start = time.perf_counter()
    for _ in range(iterations):
        result_py_green = detector_py.detect_green_blocks(img)
    time_py_green = (time.perf_counter() - start) / iterations * 1000

    print("[Python Mode] Benchmarking red block detection...")
    start = time.perf_counter()
    for _ in range(iterations):
        result_py_red = detector_py.detect_red_blocks(img)
    time_py_red = (time.perf_counter() - start) / iterations * 1000

    time_py = time_py_green + time_py_red
    print(f"✅ Python Green: {time_py_green:.2f}ms, Red: {time_py_red:.2f}ms, Total: {time_py:.2f}ms")

    # Results
    print()
    print("Results:")
    print("-" * 60)
    if time_cpp:
        speedup = time_py / time_cpp
        improvement = ((time_py - time_cpp) / time_py) * 100
        print(f"C++ Time:     {time_cpp:.2f}ms")
        print(f"Python Time:  {time_py:.2f}ms")
        print(f"Speedup:      {speedup:.2f}x")
        print(f"Improvement:  {improvement:.1f}% faster")
    else:
        print(f"Python Time:  {time_py:.2f}ms")
        print("Build C++ extensions to see comparison!")


def overall_summary():
    """Print overall summary"""
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)

    print("\nC++ Extensions Status:")
    print(f"  OCR Preprocessing:   {'✅ Available' if ocr_cpp_available() else '❌ Not built'}")
    print(f"  Color Detection:     {'✅ Available' if color_cpp_available() else '❌ Not built'}")

    if ocr_cpp_available() or color_cpp_available():
        print("\n✅ C++ extensions are working!")
        print("   Your application will use optimized C++ code automatically.")
    else:
        print("\n⚠️  C++ extensions not built")
        print("   Run 'build.bat' in cpp_extensions folder to build them.")
        print("   The application will work but use slower Python code.")

    print("\nExpected Performance Gains with C++ Extensions:")
    print("  - OCR Preprocessing:     2-3x faster")
    print("  - Color Detection:       3-4x faster")
    print("  - Overall System:        40-50% faster")


def main():
    """Run all benchmarks"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  AUTO TEST CORRECTOR - PERFORMANCE BENCHMARK              ║")
    print("╚════════════════════════════════════════════════════════════╝")

    overall_summary()

    # Run benchmarks
    benchmark_ocr_preprocessing(iterations=50)
    benchmark_color_detection(iterations=50)

    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
