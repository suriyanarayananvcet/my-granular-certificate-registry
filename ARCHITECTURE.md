# System Architecture

## Overview

The Granular Certificate Registry System converts annual energy certificates into hourly certificates using real electricity generation data. This document describes the system architecture and design decisions.

## System Components

### 1. Data Models (`models.py`)

Core data structures representing certificates and related entities:

- **AnnualCertificate**: Represents a yearly energy certificate
- **HourlyCertificate**: Represents an hourly energy certificate
- **HourlyGenerationData**: Represents hourly electricity generation data
- **CertificateTrade**: Represents a certificate trade transaction
- **ConversionResult**: Result of annual to hourly conversion

### 2. Certificate Processor (`processor.py`)

Handles the core conversion logic:

- **CertificateProcessor**: Main processing engine
  - `load_hourly_data()`: Loads hourly data from CSV
  - `create_hourly_data_from_total()`: Generates hourly data from total
  - `convert_to_hourly()`: Converts annual certificate to hourly certificates

**Key Algorithm:**
1. Validate annual certificate is canceled
2. Load/generate 8760 hours of generation data
3. Calculate scaling factor: `scale_factor = annual_total / hourly_data_total`
4. Create hourly certificates: `hourly_mwh = hourly_data_mwh * scale_factor`
5. Validate conversion

### 3. Certificate Validator (`validator.py`)

Ensures data integrity and correctness:

- **CertificateValidator**: Validation engine
  - `validate_conversion()`: Validates annual to hourly conversion
  - `validate_hourly_certificate()`: Validates single hourly certificate
  - `validate_annual_certificate()`: Validates annual certificate

**Validation Checks:**
- MWh totals match (within tolerance)
- Year consistency
- Source type consistency
- Parent certificate ID matching
- No duplicate timestamps
- Certificate ID uniqueness
- Status validation

### 4. Certificate Registry (`registry.py`)

Manages certificate storage and retrieval:

- **CertificateRegistry**: Central registry
  - Stores annual and hourly certificates
  - Indexes by parent, owner, timestamp, source type
  - Provides query methods
  - Tracks ownership

**Indexes:**
- `certificates_by_parent`: Maps parent ID → hourly certificate IDs
- `certificates_by_owner`: Maps owner → certificate IDs
- `certificates_by_timestamp`: Maps timestamp → certificate IDs
- `certificates_by_source`: Maps source type → certificate IDs

### 5. Certificate Trading (`trading.py`)

Manages certificate trading:

- **CertificateTrading**: Trading system
  - `trade_certificates()`: Executes certificate trades
  - `get_trade()`: Retrieves trade by ID
  - `get_trades_by_owner()`: Gets trades for an owner
  - `get_trade_history()`: Gets history for a certificate

**Trading Process:**
1. Validate certificates exist and belong to seller
2. Validate certificates are active
3. Calculate total price (if price_per_mwh provided)
4. Create trade record
5. Update certificate owners
6. Store trade record

### 6. API Interface (`api.py`)

RESTful API for system interaction:

- FastAPI-based REST API
- Endpoints for all major operations
- Request/response validation
- Error handling

**Endpoints:**
- `POST /certificates/annual`: Register annual certificate
- `POST /certificates/convert`: Convert to hourly
- `GET /certificates/hourly`: Get hourly certificates
- `POST /certificates/trade`: Trade certificates
- `GET /certificates/validate`: Validate certificates
- `GET /certificates/statistics`: Get statistics

## Data Flow

### Conversion Flow

```
Annual Certificate (1000 MWh)
    ↓
Hourly Generation Data (8760 hours)
    ↓
Certificate Processor
    ↓
Scaling & Distribution
    ↓
Hourly Certificates (8760 certificates)
    ↓
Validation
    ↓
Registry Storage
```

### Trading Flow

```
Certificate Query
    ↓
Owner Validation
    ↓
Trade Creation
    ↓
Ownership Update
    ↓
Trade Record Storage
```

## Design Decisions

### 1. In-Memory Storage

The current implementation uses in-memory dictionaries for storage. This is suitable for:
- Development and testing
- Small to medium datasets
- Prototyping

For production, consider:
- Database backend (PostgreSQL, MongoDB)
- Persistent storage
- Distributed storage for scale

### 2. Uniform vs. Real Data Distribution

The system supports both:
- **Uniform distribution**: Equal MWh per hour
- **Real data**: Actual hourly generation patterns

Real data provides more accurate temporal matching.

### 3. Scaling Factor

When hourly data total doesn't match annual total exactly:
- Calculate scaling factor
- Apply to all hourly values
- Ensures exact match to annual total

### 4. Certificate Status

Status workflow:
- `CANCELED` → Ready for conversion
- `ACTIVE` → Available for use/trading
- `TRADED` → Has been traded
- `RETIRED` → No longer valid

### 5. Validation Tolerance

Default tolerance: 0.01 MWh (0.1% of typical 1000 MWh certificate)

Allows for floating-point precision issues while ensuring accuracy.

## Scalability Considerations

### Current Limitations

1. **Memory**: All certificates stored in memory
2. **Single Process**: No distributed processing
3. **No Persistence**: Data lost on restart

### Future Enhancements

1. **Database Backend**
   - PostgreSQL for relational data
   - MongoDB for document storage
   - Redis for caching

2. **Distributed Processing**
   - Batch processing for large conversions
   - Parallel validation
   - Distributed registry

3. **Persistence**
   - Save/load registry state
   - Transaction logging
   - Audit trail

4. **Performance**
   - Caching frequently accessed certificates
   - Index optimization
   - Query optimization

## Security Considerations

### Current State

- Basic validation
- Ownership checks
- Status validation

### Recommended Enhancements

1. **Authentication & Authorization**
   - User authentication
   - Role-based access control
   - API keys

2. **Data Integrity**
   - Cryptographic signatures
   - Blockchain integration
   - Immutable audit log

3. **Privacy**
   - Encrypted storage
   - Access logging
   - Data anonymization

## Testing Strategy

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test component interactions
3. **Validation Tests**: Test conversion accuracy
4. **Performance Tests**: Test with large datasets

## Deployment

### Development
```bash
python -m granular_certificate_registry.api
```

### Production
```bash
uvicorn granular_certificate_registry.api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### Docker (Future)
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "granular_certificate_registry.api:app", "--host", "0.0.0.0"]
```

## Monitoring & Observability

### Recommended Metrics

1. **Conversion Metrics**
   - Conversion success rate
   - Average conversion time
   - Validation failure rate

2. **Registry Metrics**
   - Total certificates
   - Certificates by source type
   - Certificates by status

3. **Trading Metrics**
   - Trades per day
   - Total MWh traded
   - Average price per MWh

4. **API Metrics**
   - Request rate
   - Response time
   - Error rate

## Future Enhancements

1. **Blockchain Integration**: Immutable certificate ledger
2. **Real-time Processing**: Stream processing for live data
3. **Advanced Analytics**: Certificate usage patterns
4. **Multi-tenant Support**: Multiple organizations
5. **Certificate Expiration**: Time-based validity
6. **Batch Operations**: Bulk conversions and trades

