# Granular Certificate Registry System

A complete system that converts annual energy certificates into hourly certificates using real electricity generation data.

## What This System Does

**Input:** Annual energy certificate (e.g., 1000 MWh for the whole year)

**Process:** Matches with hourly electricity generation data (8760 hours)

**Output:** 8760 hourly certificates (one for each hour)

## Example

**Before:** 1 certificate = 1000 MWh (whole year)

**After:**
- Hour 1 = 0.5 MWh certificate
- Hour 2 = 0.3 MWh certificate
- Hour 3 = 0.7 MWh certificate
- ...8760 hours total

## Why This Matters

**Old way:** "I used 1000 MWh of renewable energy this year"

**Your way:** "I used 0.5 MWh of renewable energy at 2pm on March 15th"

## Features

✅ Takes canceled yearly certificates  
✅ Matches them with hourly electricity data  
✅ Creates thousands of hourly certificates  
✅ Validates everything is correct  
✅ Manages certificate trading and tracking  

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from granular_certificate_registry import CertificateProcessor, AnnualCertificate

# Create an annual certificate
annual_cert = AnnualCertificate(
    certificate_id="CERT-2024-001",
    total_mwh=1000.0,
    year=2024,
    source_type="solar",
    status="canceled"
)

# Load hourly generation data
processor = CertificateProcessor()
hourly_data = processor.load_hourly_data("hourly_generation_data.csv")

# Convert to hourly certificates
hourly_certificates = processor.convert_to_hourly(annual_cert, hourly_data)

# Validate
processor.validate_conversion(annual_cert, hourly_certificates)

# Register certificates
registry = CertificateRegistry()
registry.register_certificates(hourly_certificates)
```

## Project Structure

```
granular_certificate_registry/
├── __init__.py
├── models.py              # Data models
├── processor.py           # Certificate processing engine
├── validator.py           # Validation system
├── registry.py            # Certificate registry and tracking
├── trading.py             # Trading system
└── api.py                 # API interface

examples/
├── example_usage.py
└── sample_data.csv

tests/
└── test_system.py
```

## API Usage

Start the API server:
```bash
python -m granular_certificate_registry.api
```

Then use the API endpoints:
- `POST /certificates/annual` - Register annual certificate
- `POST /certificates/convert` - Convert annual to hourly
- `GET /certificates/hourly/{certificate_id}` - Get hourly certificates
- `POST /certificates/trade` - Trade certificates
- `GET /certificates/validate/{certificate_id}` - Validate certificates

## License

MIT
