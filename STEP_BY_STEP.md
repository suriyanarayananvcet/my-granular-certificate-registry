# Step-by-Step Guide: How to Open and Run the Code

## 📋 Complete Step-by-Step Process

### STEP 1: Open Terminal

**On Mac:**
1. Press `Command (⌘) + Space` to open Spotlight
2. Type: `Terminal`
3. Press `Enter`
4. Terminal window will open

**Alternative:**
- Go to Applications → Utilities → Terminal

---

### STEP 2: Navigate to Project Folder

**In the Terminal, type:**
```bash
cd /Users/suriyanarayanan/granular_certificate_registry
```

**Press Enter**

**Verify you're in the right place:**
```bash
pwd
```

**You should see:**
```
/Users/suriyanarayanan/granular_certificate_registry
```

---

### STEP 3: Check What Files Are There

**List all files:**
```bash
ls -la
```

**You should see folders like:**
- `granular_certificate_registry/` (main code)
- `examples/` (example scripts)
- `tests/` (test files)
- `README.md` (documentation)

**List Python files:**
```bash
ls granular_certificate_registry/*.py
```

**You should see:**
- `models.py`
- `processor.py`
- `validator.py`
- `registry.py`
- `trading.py`
- `api.py`

---

### STEP 4: Install Dependencies (First Time Only)

**Check if Python is installed:**
```bash
python3 --version
```

**You should see something like:**
```
Python 3.14.0
```

**Install required packages:**
```bash
pip3 install -r requirements.txt
```

**Wait for installation to complete** (may take 1-2 minutes)

**If you get permission errors, use:**
```bash
pip3 install --user -r requirements.txt
```

---

### STEP 5: Run the Quick Demo (See Results!)

**Run this command:**
```bash
python3 quick_demo.py
```

**What happens:**
- The script will run
- You'll see output showing:
  - Creating annual certificate
  - Generating hourly data
  - Converting to hourly certificates
  - Sample results

**Expected output:**
```
🌱 GRANULAR CERTIFICATE REGISTRY - QUICK DEMO 🌱
============================================================

📝 Step 1: Creating an annual certificate...
   ✅ Created: CERT-2024-001
   📊 Total MWh: 1000.0
   ...
```

**If it works:** ✅ You'll see "DEMO COMPLETE!" at the end

**If there's an error:** See "Troubleshooting" section below

---

### STEP 6: View the Code Files

**Option A: Using Terminal to View**

**View a specific file:**
```bash
cat granular_certificate_registry/models.py
```

**Or use less (better for long files):**
```bash
less granular_certificate_registry/models.py
```
- Press `Space` to scroll down
- Press `q` to quit

**Option B: Using VS Code (Recommended)**

1. **Open VS Code:**
   ```bash
   code .
   ```
   (This opens VS Code in current folder)

2. **Or manually:**
   - Open VS Code application
   - File → Open Folder
   - Navigate to: `/Users/suriyanarayanan/granular_certificate_registry`
   - Click "Open"

3. **Explore files:**
   - Click on `granular_certificate_registry` folder in left sidebar
   - Click on any `.py` file to view it
   - Start with `models.py` to see data structures

**Option C: Using Finder (Mac)**

1. **Open Finder**
2. **Press `Command + Shift + G`**
3. **Type:** `/Users/suriyanarayanan/granular_certificate_registry`
4. **Press Enter**
5. **Double-click any `.py` file** to open in default editor

---

### STEP 7: Run More Examples

**Run comprehensive examples:**
```bash
python3 examples/example_usage.py
```

**This shows:**
- Basic conversion
- Registry and tracking
- Certificate trading
- Validation
- Query examples

---

### STEP 8: Start the API Server

**Start the server:**
```bash
python3 -m granular_certificate_registry.api
```

**You should see:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal window open!**

**Open a NEW terminal window** (don't close the server)

**In the new terminal, test the API:**
```bash
curl http://localhost:8000/
```

**Or open in browser:**
1. Open your web browser
2. Go to: `http://localhost:8000/docs`
3. You'll see interactive API documentation
4. You can test endpoints directly from the browser!

**To stop the server:**
- Go back to the terminal running the server
- Press `Ctrl + C`

---

### STEP 9: Run Tests

**Run all tests:**
```bash
python3 -m unittest discover tests
```

**Or run specific test file:**
```bash
python3 tests/test_system.py
```

---

## 🎯 Quick Reference Commands

**Copy and paste these one at a time:**

```bash
# 1. Go to project
cd /Users/suriyanarayanan/granular_certificate_registry

# 2. Check files
ls -la

# 3. Install dependencies (first time only)
pip3 install -r requirements.txt

# 4. Run quick demo
python3 quick_demo.py

# 5. View code in VS Code
code .

# 6. Run full examples
python3 examples/example_usage.py

# 7. Start API server
python3 -m granular_certificate_registry.api
```

---

## 🔍 What Each File Does

### Main Code Files:

1. **`models.py`**
   - Defines data structures
   - AnnualCertificate, HourlyCertificate classes
   - **Start here to understand the system**

2. **`processor.py`**
   - Converts annual → hourly certificates
   - Main conversion logic
   - **This is the core engine**

3. **`validator.py`**
   - Validates conversions
   - Checks data correctness
   - **Ensures accuracy**

4. **`registry.py`**
   - Stores certificates
   - Tracks ownership
   - **Database-like functionality**

5. **`trading.py`**
   - Handles certificate trading
   - Ownership transfer
   - **Trading system**

6. **`api.py`**
   - REST API endpoints
   - Web interface
   - **API server**

### Example Files:

- **`quick_demo.py`** - Quick demonstration (run this first!)
- **`examples/example_usage.py`** - Comprehensive examples

---

## 🐛 Troubleshooting

### Problem: "command not found: python3"

**Solution:**
```bash
# Try python instead
python quick_demo.py

# Or check if Python is installed
which python3
```

### Problem: "ModuleNotFoundError"

**Solution:**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Or with user flag
pip3 install --user -r requirements.txt
```

### Problem: "Permission denied"

**Solution:**
```bash
# Use --user flag
pip3 install --user -r requirements.txt
```

### Problem: "No such file or directory"

**Solution:**
```bash
# Make sure you're in the right folder
pwd

# Should show: /Users/suriyanarayanan/granular_certificate_registry

# If not, navigate there
cd /Users/suriyanarayanan/granular_certificate_registry
```

### Problem: "Import error"

**Solution:**
```bash
# Install the package in development mode
pip3 install -e .

# Then try again
python3 quick_demo.py
```

---

## ✅ Success Checklist

After following all steps, you should be able to:

- [ ] Open terminal and navigate to project
- [ ] See all project files listed
- [ ] Run `python3 quick_demo.py` successfully
- [ ] See output showing certificate conversion
- [ ] Open code files in VS Code or editor
- [ ] Run `examples/example_usage.py`
- [ ] Start API server and access `http://localhost:8000/docs`
- [ ] Understand what each main file does

---

## 📊 Expected Output Example

When you run `quick_demo.py`, you should see:

```
🌱 GRANULAR CERTIFICATE REGISTRY - QUICK DEMO 🌱
======================================================================

📝 Step 1: Creating an annual certificate...
   ✅ Created: CERT-2024-001
   📊 Total MWh: 1000.0
   📅 Year: 2024
   ⚡ Source: solar

⚙️  Step 2: Initializing certificate processor...
   ✅ Processor ready

📈 Step 3: Generating hourly generation data (8760 hours)...
   ✅ Generated 8760 hours of data
   📊 Total MWh in data: 1000.0000
   📊 Average per hour: 0.114155

🔄 Step 4: Converting annual certificate to hourly certificates...
   ✅ Conversion complete!
   📦 Created 8760 hourly certificates
   📊 Total MWh converted: 1000.0000
   ✅ Validation: PASSED

📋 Step 5: Sample hourly certificates (first 10):
   ---------------------------------------------------------------
   1. HOURLY-CERT-2024-001-2024010100
      Time: 2024-01-01 00:00
      MWh:  0.114155
   ...

🎉 DEMO COMPLETE! The system is working perfectly! 🎉
```

---

## 🎓 Learning Path

**Day 1:**
1. Run `quick_demo.py` ✅
2. Read `models.py` to understand data structures
3. Run `examples/example_usage.py`

**Day 2:**
4. Read `processor.py` to understand conversion logic
5. Start API server and test endpoints
6. Read `validator.py` to understand validation

**Day 3:**
7. Read `registry.py` and `trading.py`
8. Modify examples to create your own certificates
9. Explore API endpoints

---

## 💡 Pro Tips

1. **Keep Terminal open** - You'll use it frequently
2. **Use VS Code** - Best for viewing and editing code
3. **Read comments** - Code has helpful comments
4. **Start simple** - Run `quick_demo.py` first
5. **Experiment** - Try modifying the examples

---

## 🆘 Need Help?

1. Check error messages carefully
2. Read the troubleshooting section above
3. Verify you're in the correct directory (`pwd`)
4. Make sure dependencies are installed
5. Try running commands one at a time

---

**You're all set! Follow these steps and you'll be running the system in no time! 🚀**



























