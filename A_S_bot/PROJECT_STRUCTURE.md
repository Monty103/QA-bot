# Project Structure Guide

## Overview

The project is organized into logical folders for easy navigation and maintenance:

```
A_S_bot/
├── README.md                          ← Start here!
├── PROJECT_STRUCTURE.md               ← This file
│
├── src/                               ← 📝 Source Code
│   ├── main.py                        ← Main application
│   ├── remote_database.py             ← Cloud API client
│   ├── hybrid_database.py             ← Unified DB manager
│   ├── test_integration.py            ← Test suite
│   └── cpp_extensions/                ← Optional C++ optimizations
│       ├── hybrid_ocr.py
│       ├── hybrid_color_detection.py
│       ├── fast_ocr.cpp
│       ├── fast_color_detection.cpp
│       └── build.bat
│
├── data/                              ← 💾 Database Files
│   └── test_questions.db              ← SQLite database
│
├── docs/                              ← 📚 Documentation
│   ├── config.json                    ← Configuration settings
│   ├── SETUP_INSTRUCTIONS.md          ← ⭐ Read this first!
│   ├── QUICK_REFERENCE.md             ← Fast lookup guide
│   ├── INTEGRATION_COMPLETE.md        ← Full details
│   ├── MAIN_PY_INTEGRATION_GUIDE.md   ← Code changes
│   ├── SYSTEM_INTEGRATION_SUMMARY.md  ← Architecture
│   ├── IMPLEMENTATION_SUMMARY.md      ← Project overview
│   ├── INTEGRATION_CHECKLIST.md       ← Verification
│   ├── INTEGRATION_PLAN.md            ← Technical plan
│   ├── BUG_FIX_LOG.md                 ← Issues & fixes
│   ├── CPP_INTEGRATION_GUIDE.md       ← C++ optimization
│   ├── README.md                      ← Original guide
│   ├── IMPROVEMENTS.md                ← v2.0 improvements
│   ├── QUICK_START.md                 ← 5-minute guide
│   ├── reference.md
│   └── reference_MVP.md
│
├── reference_prog/                    ← 🔍 Reference Code
│   ├── API_REFERENCE.md               ← Cloud API docs
│   ├── questionnaire_scraper.py       ← Original scraper
│   ├── semi-manual.py                 ← Semi-auto version
│   └── ultimate_database_qa_gui.py    ← GUI reference
│
└── __pycache__/                       ← Auto-generated (ignore)
```

## Quick Navigation

### 🚀 To Get Started
1. Read: [README.md](README.md) (overview)
2. Read: [docs/SETUP_INSTRUCTIONS.md](docs/SETUP_INSTRUCTIONS.md) (setup)
3. Run: `cd src && python test_integration.py` (verify)
4. Run: `cd src && python main.py` (start app)

### 📖 To Learn How It Works
- **Quick answers**: [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)
- **Full explanation**: [docs/INTEGRATION_COMPLETE.md](docs/INTEGRATION_COMPLETE.md)
- **Code details**: [docs/MAIN_PY_INTEGRATION_GUIDE.md](docs/MAIN_PY_INTEGRATION_GUIDE.md)
- **Architecture**: [docs/SYSTEM_INTEGRATION_SUMMARY.md](docs/SYSTEM_INTEGRATION_SUMMARY.md)

### 🔧 To Fix Issues
- **Bug list**: [docs/BUG_FIX_LOG.md](docs/BUG_FIX_LOG.md)
- **Setup help**: [docs/SETUP_INSTRUCTIONS.md](docs/SETUP_INSTRUCTIONS.md)
- **Configuration**: [docs/config.json](docs/config.json)

### 💻 To Modify Code
- **Main app**: [src/main.py](src/main.py)
- **API client**: [src/remote_database.py](src/remote_database.py)
- **DB manager**: [src/hybrid_database.py](src/hybrid_database.py)
- **Tests**: [src/test_integration.py](src/test_integration.py)

### ⚡ For Performance Optimization
- **C++ guide**: [docs/CPP_INTEGRATION_GUIDE.md](docs/CPP_INTEGRATION_GUIDE.md)
- **Build scripts**: [src/cpp_extensions/build.bat](src/cpp_extensions/build.bat)

### 🌐 For API Reference
- **API docs**: [reference_prog/API_REFERENCE.md](reference_prog/API_REFERENCE.md)

## Folder Purposes

### `src/` - Source Code
Contains all Python source code and optional C++ extensions.

**Key Files:**
- `main.py` - Main application (1,300+ lines)
- `hybrid_database.py` - Database manager (650+ lines)
- `remote_database.py` - API client (430+ lines)
- `test_integration.py` - Tests (210+ lines)
- `cpp_extensions/` - C++ optimizations (optional)

**When to access:**
- Modifying application logic
- Fixing bugs
- Adding features
- Building C++ extensions

---

### `data/` - Database Files
Contains SQLite database and related data files.

**Files:**
- `test_questions.db` - Main database (auto-created)

**When to access:**
- Backing up data
- Analyzing database
- Resetting database (delete and restart app)

**Note:** Path configured in [docs/config.json](docs/config.json)

---

### `docs/` - Documentation
Comprehensive guides, configuration, and technical documentation.

**Main Guides (Read in Order):**
1. [SETUP_INSTRUCTIONS.md](docs/SETUP_INSTRUCTIONS.md) - Setup guide
2. [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Quick lookup
3. [INTEGRATION_COMPLETE.md](docs/INTEGRATION_COMPLETE.md) - Full details

**Technical References:**
- [MAIN_PY_INTEGRATION_GUIDE.md](docs/MAIN_PY_INTEGRATION_GUIDE.md) - Code changes
- [SYSTEM_INTEGRATION_SUMMARY.md](docs/SYSTEM_INTEGRATION_SUMMARY.md) - Architecture
- [INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md) - Technical plan

**Support Docs:**
- [BUG_FIX_LOG.md](docs/BUG_FIX_LOG.md) - Known issues
- [CPP_INTEGRATION_GUIDE.md](docs/CPP_INTEGRATION_GUIDE.md) - C++ optimization
- [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - Project overview

**Configuration:**
- [config.json](docs/config.json) - Application settings

---

### `reference_prog/` - Reference Implementations
Original code and API documentation for reference and learning.

**Files:**
- `API_REFERENCE.md` - Complete API documentation
- `questionnaire_scraper.py` - Original scraper tool
- `semi-manual.py` - Semi-automatic version
- `ultimate_database_qa_gui.py` - GUI reference

**When to access:**
- Learning how the system works
- Understanding API structure
- Implementing similar features
- Reference implementations

---

## File Types Quick Reference

### Python Files (`.py`)
- `main.py` - Main application
- `*_database.py` - Database managers
- `test_*.py` - Test suites

**Location:** `src/`

**How to run:**
```bash
cd src
python filename.py
```

---

### Markdown Files (`.md`)
Documentation and guides.

**Location:** `docs/` and project root

**How to read:**
- In IDE/editor
- On GitHub
- With markdown viewer

---

### Configuration Files
- `config.json` - Application settings

**Location:** `docs/`

**How to edit:**
- Text editor
- IDE JSON editor
- Note: Path relative to `src/` folder when running

---

### Database Files (`.db`)
- `test_questions.db` - SQLite database

**Location:** `data/`

**How to access:**
- Via Python (automatic)
- Via SQLite browser
- Via SQLite command line

---

### C++ Extension Files
- `*.cpp` - C++ source code
- `*.py` - Python wrappers
- `build.bat` - Build script

**Location:** `src/cpp_extensions/`

**How to build:**
```bash
cd src/cpp_extensions
build.bat
```

---

## Navigation Tips

### 🔍 Finding Files

**I want to find the...**
- Main application → `src/main.py`
- Configuration → `docs/config.json`
- Database → `data/test_questions.db`
- API client → `src/remote_database.py`
- DB manager → `src/hybrid_database.py`
- Tests → `src/test_integration.py`
- Setup guide → `docs/SETUP_INSTRUCTIONS.md`
- Quick help → `docs/QUICK_REFERENCE.md`
- API docs → `reference_prog/API_REFERENCE.md`

### 🚀 Common Tasks

**To run the application:**
```bash
cd src
python main.py
```

**To run tests:**
```bash
cd src
python test_integration.py
```

**To modify settings:**
Edit: `docs/config.json`

**To check database:**
File: `data/test_questions.db`

**To read documentation:**
Start with: `docs/SETUP_INSTRUCTIONS.md`

---

## Important Notes

### 📌 Database Path
- Configured in `docs/config.json`
- Default: `data/test_questions.db`
- Auto-created on first run

### 📌 Configuration
- Edit `docs/config.json` for settings
- Changes take effect on app restart
- Default values suitable for most users

### 📌 Python Version
- Requires Python 3.7+
- Tested with Python 3.9+

### 📌 Dependencies
Install once:
```bash
pip install fuzzywuzzy python-Levenshtein pytesseract pillow pyautogui opencv-python requests
```

### 📌 C++ Extensions (Optional)
- Not required for operation
- Provides 40-50% performance boost
- See `docs/CPP_INTEGRATION_GUIDE.md`

---

## Folder Organization Benefits

✅ **Clean Structure** - Easy to find files
✅ **Separation of Concerns** - Code, data, docs separate
✅ **Easy Maintenance** - Organized for updates
✅ **Clear Navigation** - Intuitive folder names
✅ **Scalable** - Room for future expansion

---

## Summary

The project is organized into:

| Folder | Purpose | Contains |
|--------|---------|----------|
| `src/` | Source code | Python + C++ files |
| `data/` | Database files | SQLite database |
| `docs/` | Documentation | Guides, config, reference |
| `reference_prog/` | Reference code | Original implementations |

**Start here:** [README.md](README.md)
**Then read:** [docs/SETUP_INSTRUCTIONS.md](docs/SETUP_INSTRUCTIONS.md)

---

**Status**: Project organized and ready to use ✓
