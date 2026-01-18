# Documentation Index

## 🎯 Purpose & Clarification

Start here to understand what this script should actually be:

- **[ACTUAL_PURPOSE.md](ACTUAL_PURPOSE.md)** ⭐ **READ THIS FIRST**
  - What the script actually is (background helper, not GUI app)
  - How it should work (invisible, automatic, read-only)
  - Current issues (GUI, writes to DB, manual operation)
  - Correct implementation requirements

- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)** ⭐ **THEN READ THIS**
  - Detailed step-by-step refactoring plan
  - Which components need to be created/modified/removed
  - Before and after comparison
  - Estimated effort (10-15 hours)

---

## 🚀 Getting Started

- **[README.md](../README.md)** - Project overview
- **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - How to setup and run
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick lookup guide
- **[QUICK_START.md](QUICK_START.md)** - 5-minute quick start

---

## 🔧 Implementation & Technical Details

- **[MAIN_PY_INTEGRATION_GUIDE.md](MAIN_PY_INTEGRATION_GUIDE.md)** - Code changes made so far
- **[SYSTEM_INTEGRATION_SUMMARY.md](SYSTEM_INTEGRATION_SUMMARY.md)** - Architecture overview
- **[INTEGRATION_COMPLETE.md](INTEGRATION_COMPLETE.md)** - What was accomplished in Phase 1
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Complete project summary

---

## ⚠️ Clarifications & Issues

- **[ACTUAL_PURPOSE.md](ACTUAL_PURPOSE.md)** - What this script should be (NOT a GUI app)
- **[REFACTORING_PLAN.md](REFACTORING_PLAN.md)** - Plan to fix the code
- **[BUG_FIX_LOG.md](BUG_FIX_LOG.md)** - Bugs found and fixed so far

---

## 📊 Planning & Architecture

- **[INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)** - Original integration technical plan
- **[INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md)** - Verification checklist
- **[FOLDER_REORGANIZATION_SUMMARY.md](../FOLDER_REORGANIZATION_SUMMARY.md)** - How files were organized

---

## 🛠️ Advanced Topics

- **[CPP_INTEGRATION_GUIDE.md](CPP_INTEGRATION_GUIDE.md)** - C++ performance optimizations (optional)

---

## 📋 Configuration

- **[config.json](config.json)** - Application configuration file

---

## ❌ Legacy/Outdated Documentation

- **[README.md](README.md)** - Old guide (refer to root README instead)
- **[reference.md](reference.md)** - Original reference (outdated)
- **[reference_MVP.md](reference_MVP.md)** - MVP reference (outdated)
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - v2.0 improvements (outdated)

---

## 📖 Reading Order

### For Understanding What to Do
1. [ACTUAL_PURPOSE.md](ACTUAL_PURPOSE.md) - Clarify the true purpose
2. [REFACTORING_PLAN.md](REFACTORING_PLAN.md) - Understand what changes are needed
3. [FOLDER_REORGANIZATION_SUMMARY.md](../FOLDER_REORGANIZATION_SUMMARY.md) - See current organization

### For Getting Started
1. [README.md](../README.md) - Project overview
2. [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Setup guide
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick answers

### For Technical Details
1. [MAIN_PY_INTEGRATION_GUIDE.md](MAIN_PY_INTEGRATION_GUIDE.md) - Code changes
2. [SYSTEM_INTEGRATION_SUMMARY.md](SYSTEM_INTEGRATION_SUMMARY.md) - Architecture
3. [CPP_INTEGRATION_GUIDE.md](CPP_INTEGRATION_GUIDE.md) - Performance optimization

### For Troubleshooting
1. [BUG_FIX_LOG.md](BUG_FIX_LOG.md) - Known issues and fixes
2. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - FAQ and common problems

---

## 🎯 Current Status

### ✅ Completed
- Project reorganized into src/, docs/, data/ folders
- Hybrid database system created
- Integration into main.py (10 integration points)
- Comprehensive documentation
- Bug fixes applied

### ❌ Issues Identified
- Current implementation is GUI-based (should be background script)
- Current implementation writes to database (should be read-only)
- Current implementation requires manual setup (should be automatic)

### 🔄 Next Steps
1. Read ACTUAL_PURPOSE.md to understand the issue
2. Read REFACTORING_PLAN.md for detailed implementation plan
3. Begin refactoring to convert to background helper script

---

## 💡 Quick Facts

- **Type**: Background helper script (NOT a GUI application)
- **Operation**: Automatic and invisible (NO GUI window)
- **Database**: Read-only (NEVER write)
- **Purpose**: Auto-correct wrong answers on questionnaires
- **Flow**: Monitor screen → Detect click → Check if wrong → Auto-correct

---

## 📁 File Structure

```
docs/
├── INDEX.md                          ← You are here
├── ACTUAL_PURPOSE.md                 ← What it should be
├── REFACTORING_PLAN.md              ← How to fix it
├── SETUP_INSTRUCTIONS.md            ← How to setup
├── QUICK_REFERENCE.md               ← Fast answers
├── INTEGRATION_COMPLETE.md          ← What was done
├── MAIN_PY_INTEGRATION_GUIDE.md     ← Code changes
├── SYSTEM_INTEGRATION_SUMMARY.md    ← Architecture
├── BUG_FIX_LOG.md                   ← Issues & fixes
├── CPP_INTEGRATION_GUIDE.md         ← Performance
├── config.json                      ← Configuration
└── (legacy docs)
```

---

## 🔗 Quick Links

| Need | File |
|------|------|
| Understand purpose | [ACTUAL_PURPOSE.md](ACTUAL_PURPOSE.md) |
| See refactoring plan | [REFACTORING_PLAN.md](REFACTORING_PLAN.md) |
| Setup instructions | [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) |
| Quick answers | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| Code details | [MAIN_PY_INTEGRATION_GUIDE.md](MAIN_PY_INTEGRATION_GUIDE.md) |
| Architecture | [SYSTEM_INTEGRATION_SUMMARY.md](SYSTEM_INTEGRATION_SUMMARY.md) |
| Fix issues | [BUG_FIX_LOG.md](BUG_FIX_LOG.md) |
| Optimize performance | [CPP_INTEGRATION_GUIDE.md](CPP_INTEGRATION_GUIDE.md) |

---

## ⚡ TL;DR

- **Current**: GUI app that writes to DB (WRONG ❌)
- **Should be**: Background script that reads from DB (RIGHT ✅)
- **Action**: Read ACTUAL_PURPOSE.md and REFACTORING_PLAN.md
- **Effort**: 10-15 hours to refactor

---

**Last Updated**: December 2, 2025
**Status**: Documentation Index Created
