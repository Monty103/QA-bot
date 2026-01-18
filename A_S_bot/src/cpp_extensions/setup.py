"""
Setup script for building C++ extensions
Builds optimized C++ modules for performance-critical operations

Usage:
    python setup.py build_ext --inplace
"""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import pybind11

class get_pybind_include(object):
    """Helper class to determine the pybind11 include path"""
    def __str__(self):
        import pybind11
        return pybind11.get_include()

# Compiler flags for optimization
extra_compile_args = []
extra_link_args = []

if sys.platform == 'win32':
    # Windows (MSVC)
    extra_compile_args = [
        '/O2',          # Maximum optimization
        '/Ot',          # Favor fast code
        '/arch:AVX2',   # Use AVX2 instructions (if available)
        '/fp:fast',     # Fast floating point
        '/GL',          # Whole program optimization
    ]
    extra_link_args = ['/LTCG']  # Link-time code generation
else:
    # Linux/Mac (GCC/Clang)
    extra_compile_args = [
        '-O3',                  # Maximum optimization
        '-march=native',        # Optimize for current CPU
        '-ffast-math',          # Fast math operations
        '-funroll-loops',       # Unroll loops
        '-ftree-vectorize',     # Auto-vectorization
        '-std=c++17',           # C++17 standard
    ]

# Extension 1: Fast OCR preprocessing
ext_fast_ocr = Extension(
    'fast_ocr_cpp',
    sources=['fast_ocr.cpp'],
    include_dirs=[
        get_pybind_include(),
        pybind11.get_include(),
    ],
    language='c++',
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

# Extension 2: Fast color detection
ext_fast_color = Extension(
    'fast_color_detection_cpp',
    sources=['fast_color_detection.cpp'],
    include_dirs=[
        get_pybind_include(),
        pybind11.get_include(),
    ],
    language='c++',
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args,
)

setup(
    name='auto_test_corrector_cpp',
    version='2.0',
    author='Auto Test Corrector Team',
    description='Optimized C++ extensions for performance-critical operations',
    ext_modules=[ext_fast_ocr, ext_fast_color],
    install_requires=['pybind11>=2.6.0'],
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
    python_requires='>=3.7',
)
