# 📚 Quick Reference Guide

## Files You Now Have

### **Core System Files**
- `main.py` - Auto Test Corrector (existing, to be updated)
- `config.json` - Configuration settings
- `cpp_extensions/` - C++ performance extensions

### **New Database Files** ✨
- `remote_database.py` - Cloud API manager
- `hybrid_database.py` - Unified local + remote DB manager

### **Documentation Files**
- `INTEGRATION_PLAN.md` - Full technical plan (read this first!)
- `SYSTEM_INTEGRATION_SUMMARY.md` - High-level overview
- `MAIN_PY_INTEGRATION_GUIDE.md` - Step-by-step code changes
- `QUICK_REFERENCE.md` - This file
mai
### **Reference Files** (Your Original Code)
- `reference_prog/API_REFERENCE.md` - Cloud API specification
- `reference_prog/questionnaire_scraper.py` - Data collection tool
- `reference_prog/ultimate_database_qa_gui.py` - Data builder

---

## 🚀 Three-Step Start

### **Step 1: Understand the System**
Read in this order: 
1. This file (2 min)
2. `SYSTEM_INTEGRATION_SUMMARY.md` (10 min)
3. `INTEGRATION_PLAN.md` (20 min)

### **Step 2: Review the Code**
- `remote_database.py` - See API implementation
- `hybrid_database.py` - See hybrid logic
`````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````````
### **Step 3: Integrate into main.py**
- Follow `MAIN_PY_INTEGRATION_GUIDE.md` step-by-step
- 10 code changes required (~30  minutes)

---

## 📋 File Structure

```
A_S_bot/
├── main.py                          ← Your auto-corrector (to update)
├── config.json                      ← Settings
├── CPP_INTEGRATION_GUIDE.md        ← C++ performance (optional)
├── IMPROVEMENTS.md                  ← v2.0 improvements
├── README.md                        ← User guide
├── QUICK_START.md                   ← 5-min guide
│
├── INTEGRATION_PLAN.md              ← 🆕 READ THIS FIRST!
├── SYSTEM_INTEGRATION_SUMMARY.md   ← 🆕 Overview
├── MAIN_PY_INTEGRATION_GUIDE.md    ← 🆕 Code changes
├── QUICK_REFERENCE.md               ← 🆕 This file
│
├── remote_database.py               ← 🆕 API manager
├── hybrid_database.py               ← 🆕 Hybrid DB
│
├── cpp_extensions/                  ← C++ optimizations
├── reference_prog/                  ← Your original tools
│   ├── API_REFERENCE.md            ← Cloud API spec
│   ├── questionnaire_scraper.py    ← Data collection
│   └── ultimate_database_qa_gui.py  ← Data builder
```

---

## 🎯 Quick Facts

### **What Is RemoteAPIManager?**
- Interface to cloud database API
- All 20+ endpoints implemented
- Error handling built-in
- Use: `api = RemoteAPIManager()`

### **What Is HybridDatabaseManager?**
- Unified interface: Local SQLite + Remote API
- Automatic fallback (API → SQLite)
- Offline support with sync queue
- Use: `db = HybridDatabaseManager()`

### **Key Differences**

| Feature | Old (main.py) | New (Hybrid) |
|---------|---------------|--------------|
| Online | ❌ No | ✅ Yes (API) |
| Offline | ✅ Yes (SQLite) | ✅ Yes (SQLite) |
| Cloud Sync | ❌ No | ✅ Auto |
| Fallback | ❌ None | ✅ Automatic |
| Multi-device | ❌ No | ✅ Yes |

---

## 💡 Quick Usage Examples

### **Example 1: Create a Question**
```python
from hybrid_database import HybridDatabaseManager

db = HybridDatabaseManager()

# Creates in SQLite AND tries to sync to API
q_id = db.create_question(
    "What is Python?",
    "single",  # or "multi"
    1
)

db.add_answer(q_id, "Programming language", True)
db.add_answer(q_id, "A snake", False)

db.close()
```

### **Example 2: Get Questions (Works Online/Offline)**
```python
from hybrid_database import HybridDatabaseManager

db = HybridDatabaseManager()

# Tries API first, falls back to SQLite
questions = db.get_all_questions(include_answers=True)

for q in questions:
    print(f"Q: {q['question_text']}")
    for a in q['answers']:
        status = "✓" if a['is_correct'] else "✗"
        print(f"  {status} {a['answer_text']}")

db.close()
```

### **Example 3: Log Corrections**
```python
from hybrid_database import HybridDatabaseManager

db = HybridDatabaseManager()

# Saves locally, syncs to API when online
db.log_correction(
    question_text="What is 2+2?",
    wrong_answer="5",
    correct_answer="4",
    correction_successful=True
)

db.close()
```

### **Example 4: Check Connection Status**
```python
from hybrid_database import HybridDatabaseManager

db = HybridDatabaseManager()

mode = db.get_mode()
# Returns: "hybrid" (online), "offline" (no API), "local" (API disabled)

if db.is_connected():
    print("Connected to cloud!")
else:
    print("Using local cache")

db.close()
```

---

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "tesseract_path": "C:\\dt\\Tesseract-OCR\\tesseract.exe",
  "database_file": "test_questions.db",
  "fuzzy_match_threshold": 85,
  "monitoring_interval_seconds": 0.5,
  "correction_delay_seconds": 0.2,
  "enable_auto_correction": true,
  "log_corrections_to_database": true
}
```

### **For Hybrid Database**
In code:
```python
db = HybridDatabaseManager(
    sqlite_path="test_questions.db",
    api_url="https://question-database-api.onrender.com",
    use_api=True,        # Set False to disable API
    sync_interval=30     # Auto-sync every 30 seconds
)
```

---

## ✅ Integration Checklist

Quick version - detailed steps in `MAIN_PY_INTEGRATION_GUIDE.md`:

```
□ Step 1: Add imports (line 35)
  from hybrid_database import HybridDatabaseManager

□ Step 2: Update __init__() (line 300)
  self.db = HybridDatabaseManager()

□ Step 3: Update match_question() (line 706)
  Use: self.db.get_all_questions()

□ Step 4: Update log_correction() (line 1039)
  Use: self.db.log_correction()

□ Step 5: Update import_existing_data() (line 1063)
  Use: self.db.create_question() and self.db.add_answer()

□ Step 6: Add database mode indicator to GUI
  Track and display current mode (online/offline)

□ Step 7: Test with integration test script
  python test_integration.py

□ Step 8: Run main.py and verify
  Test both online and offline modes
```

---

## 🌐 API Endpoints Quick Reference

### **Questions**
```
GET    /api/questions                 - Get all
GET    /api/questions/{id}            - Get one
POST   /api/questions                 - Create
PUT    /api/questions/{id}            - Update
DELETE /api/questions/{id}            - Delete
GET    /api/questions/search?q=text   - Search
```

### **Answers**
```
GET    /api/questions/{id}/answers    - Get answers
POST   /api/questions/{id}/answers    - Add answer
PUT    /api/answers/{id}              - Update
DELETE /api/answers/{id}              - Delete
```

### **Corrections**
```
GET    /api/corrections               - Get log
POST   /api/corrections               - Log correction
GET    /api/corrections/stats         - Get stats
```

### **Health**
```
GET    /api/health                    - Check status
```

**Base URL:** `https://question-database-api.onrender.com`

---

## 🔍 Troubleshooting

### **"Can't import HybridDatabaseManager"**
- Make sure `hybrid_database.py` is in project root
- Check you have `remote_database.py` too

### **"Can't connect to API"**
- Normal! System falls back to local SQLite
- Check API URL is correct
- Try: `python -c "from remote_database import RemoteAPIManager; print(RemoteAPIManager().is_connected())"`

### **"Sync queue not processing"**
- Background thread auto-syncs every 30 seconds
- Manually force: `db._process_sync_queue()`
- Check logs for errors

### **"Questions not showing"**
- Might be offline (that's OK!)
- Check SQLite has data: `sqlite3 test_questions.db "SELECT COUNT(*) FROM questions;"`
- Load from API: `db.get_all_questions()`

---

## 📞 Key Methods You'll Use

### **Getting Data**
```python
db.get_all_questions(include_answers=True)
db.get_question(question_id, include_answers=True)
db.search_questions("query text")
db.get_answers(question_id, correct_only=False)
db.get_statistics()
```

### **Creating Data**
```python
db.create_question(text, type, required_answers)
db.add_answer(question_id, answer_text, is_correct)
```

### **Updating Data**
```python
db.update_question(question_id, text, type, required)
db.update_answer(answer_id, text, is_correct)
```

### **Deleting Data**
```python
db.delete_question(question_id)
db.delete_answer(answer_id)
```

### **Logging**
```python
db.log_correction(question_text, wrong, correct, successful)
```

### **Status**
```python
db.is_connected()       # True/False
db.get_mode()          # "hybrid", "offline", "local"
db.close()             # Cleanup
```

---

## 🎓 Learning Path

**Time needed: 1 hour**

1. **5 min:** Read this file
2. **10 min:** Read `SYSTEM_INTEGRATION_SUMMARY.md`
3. **15 min:** Read `INTEGRATION_PLAN.md`
4. **15 min:** Review `remote_database.py` code
5. **10 min:** Review `hybrid_database.py` code

Then implement the 10 changes from `MAIN_PY_INTEGRATION_GUIDE.md` (~30 min)

---

## 🚀 After Integration

You'll have:
- ✅ Cloud-connected system
- ✅ Offline support with auto-sync
- ✅ Unified database interface
- ✅ Zero manual database management
- ✅ Real-time statistics
- ✅ Multi-device support

---

## 📝 Important Notes

1. **API URL is public** - Anyone can read the database
   - Add authentication if needed (see API_REFERENCE.md)

2. **Sync is automatic** - No manual intervention needed
   - Can be customized in constructor

3. **No data loss** - Always saved locally first
   - API sync is bonus, not required

4. **Fallback is seamless** - App works offline
   - Users won't notice connection issues

5. **Backward compatible** - Old code still works
   - Just swap database calls

---

## 💬 Questions?

- **How to use API?** → See `API_REFERENCE.md`
- **How to integrate?** → See `MAIN_PY_INTEGRATION_GUIDE.md`
- **Technical details?** → See `INTEGRATION_PLAN.md`
- **High-level overview?** → See `SYSTEM_INTEGRATION_SUMMARY.md`
- **Code examples?** → See docstrings in source files

---

**Ready to integrate? Start with `INTEGRATION_PLAN.md`!** 🚀
