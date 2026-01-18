#!/usr/bin/env python3
"""
Automatic Questionnaire Helper - Entry Point

This is the main entry point for the background questionnaire helper script.
The actual implementation is in helper.py

Usage:
    python src/main.py --config docs/config.json

Or directly run helper.py:
    python src/helper.py --config docs/config.json
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from helper import QuestionnaireHelper
import argparse


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Automatic Questionnaire Helper',
        epilog='Example: python src/main.py --config ../docs/config.json'
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
