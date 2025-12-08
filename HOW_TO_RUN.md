# How to Open and Run the Code

## 📂 Step 1: Navigate to the Project

Open your terminal and go to the project directory:

```bash
cd /Users/suriyanarayanan/granular_certificate_registry
```

## 📖 Step 2: View the Code Files

### Option A: Using Terminal (Quick View)

```bash
# List all Python files
find granular_certificate_registry -name "*.py"

# View a specific file
cat granular_certificate_registry/models.py
# or
less granular_certificate_registry/models.py
```

### Option B: Using VS Code or Your IDE

1. Open VS Code (or your preferred editor)
2. File → Open Folder
3. Navigate to: `/Users/suriyanarayanan/granular_certificate_registry`
4. Explore the files in the sidebar

### Option C: Using Finder (Mac)

1. Open Finder
2. Press `Cmd + Shift + G`
3. Type: `/Users/suriyanarayanan/granular_certificate_registry`
4. Click "Go"
5. Double-click any `.py` file to open in your default editor

## 🔧 Step 3: Install Dependencies

```bash
# Make sure you're in the project directory
cd /Users/suriyanarayanan/granular_certificate_registry

# Install required packages
pip install -r requirements.txt
```

If you get permission errors, use:
```bash
pip install --user -r requirements.txt
```

## 🚀 Step 4: Run Examples to See Results

### Run the Main Example Script

```bash
python examples/example_usage.py
```

This will show you:
- ✅ Basic conversion example
- ✅ Registry and tracking
- ✅ Certificate trading
- ✅ Validation results
- ✅ Query by timestamp

### Generate Sample Data

```bash
python examples/generate_sample_data.py
```

This creates a `sample_data.csv` file with 8760 hours of data.

## 🌐 Step 5: Start the API Server

### Start the Server

```bash
python -m granular_certificate_registry.api
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### View API Documentation

1. Open your web browser
2. Go to: `http://localhost:8000/docs`
3. You'll see interactive API documentation (Swagger UI)

### Test API Endpoints

**Using Browser:**
- Visit: `http://localhost:8000/` (root endpoint)
- Visit: `http://localhost:8000/certificates/statistics` (statistics)

**Using curl:**
```bash
# Get root info
curl http://localhost:8000/

# Get statistics
curl http://localhost:8000/certificates/statistics
```

## 🧪 Step 6: Run Tests

```bash
# Run all tests
python -m unittest discover tests

# Or run specific test file
python tests/test_system.py
```

## 💻 Step 7: Interactive Python Session

You can also test the code interactively:

```bash
python
```

Then in Python:
```python
# Import the system
from granular_certificate_registry import (
    AnnualCertificate,
    CertificateProcessor,
    CertificateRegistry,
    SourceType,
    CertificateStatus
)

# Create a certificate
cert = AnnualCertificate(
    certificate_id="TEST-001",
    total_mwh=1000.0,
    year=2024,
    source_type=SourceType.SOLAR,
    status=CertificateStatus.CANCELED
)

print(f"Created certificate: {cert.certificate_id}")
print(f"Total MWh: {cert.total_mwh}")

# Create processor
processor = CertificateProcessor()

# Generate hourly data
hourly_data = processor.create_hourly_data_from_total(
    cert.total_mwh,
    cert.year,
    cert.source_type
)

print(f"Generated {len(hourly_data)} hours of data")

# Convert to hourly certificates
result = processor.convert_to_hourly(cert, hourly_data)

print(f"Created {len(result.hourly_certificates)} hourly certificates")
print(f"Total MWh: {result.total_mwh_converted:.2f}")

# Show first few certificates
for cert in result.hourly_certificates[:5]:
    print(f"  {cert.certificate_id}: {cert.mwh:.4f} MWh at {cert.timestamp}")
```

## 📊 Quick Demo Commands

Here's a quick one-liner to see it in action:

```bash
cd /Users/suriyanarayanan/granular_certificate_registry && python examples/example_usage.py
```

## 🐛 Troubleshooting

### If Python is not found:
```bash
# Try python3 instead
python3 examples/example_usage.py
```

### If packages are missing:
```bash
pip install pydantic pandas numpy fastapi uvicorn
```

### If you see import errors:
```bash
# Make sure you're in the right directory
pwd
# Should show: /Users/suriyanarayanan/granular_certificate_registry

# Install the package in development mode
pip install -e .
```

## 📝 What You'll See

When you run `example_usage.py`, you'll see output like:

```
============================================================
Granular Certificate Registry System - Examples
============================================================

============================================================
Example 1: Basic Annual to Hourly Conversion
============================================================

Created annual certificate:
  ID: CERT-2024-001
  Total MWh: 1000.0
  Year: 2024
  Source: solar

Generated 8760 hours of data
  Total MWh in hourly data: 1000.0000

Conversion completed:
  Total hourly certificates: 8760
  Total MWh converted: 1000.0000
  Validation passed: True

Sample hourly certificates (first 5):
  HOURLY-CERT-2024-001-2024010100: 2024-01-01 00:00:00 = 0.1142 MWh
  HOURLY-CERT-2024-001-2024010101: 2024-01-01 01:00:00 = 0.1142 MWh
  ...
```

## 🎯 Recommended First Steps

1. **View the code structure:**
   ```bash
   ls -la granular_certificate_registry/
   ```

2. **Read the main README:**
   ```bash
   cat README.md
   ```

3. **Run the examples:**
   ```bash
   python examples/example_usage.py
   ```

4. **Start the API:**
   ```bash
   python -m granular_certificate_registry.api
   ```
   Then visit `http://localhost:8000/docs` in your browser

That's it! You're ready to explore the system! 🚀

