# How to Open and View the Code

## 🚀 Quick Start (3 Steps)

### 1️⃣ Open Terminal
Press `Cmd + Space`, type "Terminal", press Enter

### 2️⃣ Navigate to Project
```bash
cd /Users/suriyanarayanan/granular_certificate_registry
```

### 3️⃣ Run Quick Demo
```bash
python3 quick_demo.py
```

**That's it!** You'll see the system in action! 🎉

---

## 📂 View Code Files

### Option 1: Using VS Code (Recommended)

1. **Open VS Code**
   - Press `Cmd + Space`, type "Code", press Enter
   - Or open from Applications

2. **Open the Project**
   - File → Open Folder (or `Cmd + O`)
   - Navigate to: `/Users/suriyanarayanan/granular_certificate_registry`
   - Click "Open"

3. **Explore Files**
   - Look in the left sidebar
   - Click on any `.py` file to view it
   - Main code is in `granular_certificate_registry/` folder

### Option 2: Using Finder (Mac)

1. **Open Finder**
   - Press `Cmd + Space`, type "Finder", press Enter

2. **Go to Project**
   - Press `Cmd + Shift + G` (Go to Folder)
   - Type: `/Users/suriyanarayanan/granular_certificate_registry`
   - Press Enter

3. **Open Files**
   - Double-click any `.py` file
   - It will open in your default editor

### Option 3: Using Terminal

```bash
# Go to project
cd /Users/suriyanarayanan/granular_certificate_registry

# List all Python files
ls -la granular_certificate_registry/*.py

# View a file (scroll with arrow keys, press 'q' to quit)
less granular_certificate_registry/models.py

# Or open in default editor
open granular_certificate_registry/models.py
```

---

## 🎯 Main Code Files to Explore

### Core System Files:
1. **`granular_certificate_registry/models.py`**
   - Data models (AnnualCertificate, HourlyCertificate)
   - Start here to understand the data structures

2. **`granular_certificate_registry/processor.py`**
   - Conversion engine (annual → hourly)
   - The main processing logic

3. **`granular_certificate_registry/validator.py`**
   - Validation system
   - Ensures data correctness

4. **`granular_certificate_registry/registry.py`**
   - Certificate storage and tracking
   - Query and management functions

5. **`granular_certificate_registry/trading.py`**
   - Trading system
   - Certificate ownership transfer

6. **`granular_certificate_registry/api.py`**
   - REST API interface
   - Web endpoints

### Example Files:
- **`examples/example_usage.py`** - Comprehensive examples
- **`quick_demo.py`** - Quick demonstration script

---

## 🏃 Run and See Results

### Method 1: Quick Demo (Easiest)
```bash
cd /Users/suriyanarayanan/granular_certificate_registry
python3 quick_demo.py
```

### Method 2: Full Examples
```bash
python3 examples/example_usage.py
```

### Method 3: Start API Server
```bash
# Start server
python3 -m granular_certificate_registry.api

# Then open browser to:
# http://localhost:8000/docs
```

### Method 4: Interactive Python
```bash
python3
```

Then type:
```python
from granular_certificate_registry import AnnualCertificate, SourceType, CertificateStatus

cert = AnnualCertificate(
    certificate_id="TEST",
    total_mwh=1000.0,
    year=2024,
    source_type=SourceType.SOLAR,
    status=CertificateStatus.CANCELED
)

print(cert)
```

---

## 📊 What You'll See

When you run `quick_demo.py`, you'll see:

```
🌱 GRANULAR CERTIFICATE REGISTRY - QUICK DEMO 🌱

📝 Step 1: Creating an annual certificate...
   ✅ Created: CERT-2024-001
   📊 Total MWh: 1000.0
   ...

📈 Step 3: Generating hourly generation data...
   ✅ Generated 8760 hours of data
   ...

🔄 Step 4: Converting annual certificate to hourly certificates...
   ✅ Conversion complete!
   📦 Created 8760 hourly certificates
   ...

📋 Step 5: Sample hourly certificates (first 10):
   1. HOURLY-CERT-2024-001-2024010100
      Time: 2024-01-01 00:00
      MWh: 0.114155
   ...
```

---

## 🔧 If You Get Errors

### "Python not found"
```bash
# Try python3 instead
python3 quick_demo.py
```

### "Module not found"
```bash
# Install dependencies
pip3 install -r requirements.txt
```

### "Permission denied"
```bash
# Install with --user flag
pip3 install --user -r requirements.txt
```

---

## 📚 More Information

- **`HOW_TO_RUN.md`** - Detailed running instructions
- **`README.md`** - Full documentation
- **`QUICKSTART.md`** - Quick start guide
- **`ARCHITECTURE.md`** - System architecture

---

## ✅ Checklist

- [ ] Opened terminal
- [ ] Navigated to project folder
- [ ] Ran `python3 quick_demo.py`
- [ ] Saw the results!
- [ ] Opened code files in VS Code or editor
- [ ] Explored the main modules

**You're all set!** 🎉

