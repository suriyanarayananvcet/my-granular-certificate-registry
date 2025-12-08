# Quick Start Guide

## Installation

```bash
# Navigate to project directory
cd granular_certificate_registry

# Install dependencies
pip install -r requirements.txt

# Install the package (optional)
pip install -e .
```

## Basic Usage

### 1. Using the Python API

```python
from granular_certificate_registry import (
    AnnualCertificate,
    CertificateProcessor,
    CertificateRegistry,
    SourceType,
    CertificateStatus
)

# Create an annual certificate
annual_cert = AnnualCertificate(
    certificate_id="CERT-2024-001",
    total_mwh=1000.0,
    year=2024,
    source_type=SourceType.SOLAR,
    status=CertificateStatus.CANCELED
)

# Create processor
processor = CertificateProcessor()

# Generate hourly data (or load from CSV)
hourly_data = processor.create_hourly_data_from_total(
    total_mwh=annual_cert.total_mwh,
    year=annual_cert.year,
    source_type=annual_cert.source_type
)

# Convert to hourly certificates
result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)

# Register certificates
registry = CertificateRegistry()
registry.register_certificates(result.hourly_certificates)

# Query certificates
hourly_certs = registry.get_certificates_by_parent("CERT-2024-001")
print(f"Created {len(hourly_certs)} hourly certificates")
```

### 2. Using the REST API

Start the API server:

```bash
python -m granular_certificate_registry.api
```

Or using uvicorn directly:

```bash
uvicorn granular_certificate_registry.api:app --reload
```

The API will be available at `http://localhost:8000`

#### API Endpoints

**Register Annual Certificate:**
```bash
curl -X POST "http://localhost:8000/certificates/annual" \
  -H "Content-Type: application/json" \
  -d '{
    "certificate_id": "CERT-2024-001",
    "total_mwh": 1000.0,
    "year": 2024,
    "source_type": "solar"
  }'
```

**Convert to Hourly:**
```bash
curl -X POST "http://localhost:8000/certificates/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "annual_certificate_id": "CERT-2024-001",
    "use_uniform_distribution": true
  }'
```

**Get Hourly Certificates:**
```bash
curl "http://localhost:8000/certificates/hourly?parent_id=CERT-2024-001"
```

**Trade Certificates:**
```bash
curl -X POST "http://localhost:8000/certificates/trade" \
  -H "Content-Type: application/json" \
  -d '{
    "certificate_ids": ["HOURLY-CERT-2024-001-2024010100"],
    "from_owner": "Solar Farm Inc.",
    "to_owner": "Green Energy Corp.",
    "price_per_mwh": 50.0
  }'
```

**Get Statistics:**
```bash
curl "http://localhost:8000/certificates/statistics"
```

### 3. Running Examples

```bash
# Run example usage
python examples/example_usage.py

# Generate sample data
python examples/generate_sample_data.py
```

### 4. Running Tests

```bash
python -m pytest tests/
# or
python -m unittest discover tests
```

## Key Concepts

### Annual Certificate
A certificate representing energy production for an entire year (e.g., 1000 MWh).

### Hourly Certificate
A certificate representing energy production for a single hour (e.g., 0.5 MWh at 2pm on March 15th).

### Conversion Process
1. Annual certificate must be in "canceled" status
2. Hourly generation data is matched (8760 hours)
3. Annual total is distributed proportionally across hours
4. Hourly certificates are created and validated

### Certificate Status
- `CANCELED`: Ready for conversion
- `ACTIVE`: Available for use/trading
- `TRADED`: Has been traded
- `RETIRED`: No longer valid
- `PENDING`: Awaiting processing

## Example Workflow

```python
# 1. Create annual certificate
annual_cert = AnnualCertificate(
    certificate_id="CERT-2024-001",
    total_mwh=1000.0,
    year=2024,
    source_type=SourceType.SOLAR,
    status=CertificateStatus.CANCELED
)

# 2. Register annual certificate
registry = CertificateRegistry()
registry.register_annual_certificate(annual_cert)

# 3. Load or generate hourly data
processor = CertificateProcessor()
hourly_data = processor.create_hourly_data_from_total(
    annual_cert.total_mwh,
    annual_cert.year,
    annual_cert.source_type
)

# 4. Convert to hourly certificates
result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)

# 5. Register hourly certificates
registry.register_certificates(result.hourly_certificates)

# 6. Query and use certificates
certs_at_time = registry.get_certificates_by_timestamp(
    datetime(2024, 3, 15, 14, 0, 0)
)

# 7. Trade certificates
trading = CertificateTrading(registry)
trade = trading.trade_certificates(
    certificate_ids=[c.certificate_id for c in certs_at_time[:10]],
    from_owner="Owner1",
    to_owner="Owner2",
    price_per_mwh=50.0
)
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [examples/example_usage.py](examples/example_usage.py) for more examples
- Explore the API documentation at `http://localhost:8000/docs` when the server is running

