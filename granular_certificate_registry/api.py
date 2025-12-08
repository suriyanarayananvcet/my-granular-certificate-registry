"""
API Interface for Granular Certificate Registry

RESTful API for interacting with the certificate system.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .models import (
    AnnualCertificate,
    HourlyCertificate,
    CertificateStatus,
    SourceType,
    CertificateTrade
)
from .processor import CertificateProcessor
from .validator import CertificateValidator
from .registry import CertificateRegistry
from .trading import CertificateTrading

app = FastAPI(
    title="Granular Certificate Registry API",
    description="API for converting annual energy certificates into hourly certificates",
    version="1.0.0"
)

# Initialize components
processor = CertificateProcessor()
validator = CertificateValidator()
registry = CertificateRegistry()
trading = CertificateTrading(registry)


# Request/Response models
class AnnualCertificateRequest(BaseModel):
    certificate_id: str
    total_mwh: float
    year: int
    source_type: str
    issuer: Optional[str] = None
    metadata: dict = {}


class ConversionRequest(BaseModel):
    annual_certificate_id: str
    hourly_data_file: Optional[str] = None
    use_uniform_distribution: bool = False


class TradeRequest(BaseModel):
    certificate_ids: List[str]
    from_owner: str
    to_owner: str
    price_per_mwh: Optional[float] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Granular Certificate Registry API",
        "version": "1.0.0",
        "endpoints": {
            "register_annual": "POST /certificates/annual",
            "convert_to_hourly": "POST /certificates/convert",
            "get_hourly": "GET /certificates/hourly/{certificate_id}",
            "trade": "POST /certificates/trade",
            "validate": "GET /certificates/validate/{certificate_id}",
            "statistics": "GET /certificates/statistics"
        }
    }


@app.post("/certificates/annual", response_model=dict)
async def register_annual_certificate(request: AnnualCertificateRequest):
    """Register an annual certificate"""
    try:
        cert = AnnualCertificate(
            certificate_id=request.certificate_id,
            total_mwh=request.total_mwh,
            year=request.year,
            source_type=SourceType(request.source_type),
            status=CertificateStatus.CANCELED,
            issuer=request.issuer,
            metadata=request.metadata
        )
        
        # Validate
        validation = validator.validate_annual_certificate(cert)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail=validation['errors'])
        
        # Register
        success = registry.register_annual_certificate(cert)
        if not success:
            raise HTTPException(status_code=409, detail="Certificate already exists")
        
        return {
            "success": True,
            "certificate": cert.dict(),
            "message": "Annual certificate registered successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/certificates/convert", response_model=dict)
async def convert_to_hourly(request: ConversionRequest):
    """Convert annual certificate to hourly certificates"""
    try:
        # Get annual certificate
        annual_cert = registry.get_annual_certificate(request.annual_certificate_id)
        if not annual_cert:
            raise HTTPException(
                status_code=404,
                detail=f"Annual certificate {request.annual_certificate_id} not found"
            )
        
        # Load or create hourly data
        if request.hourly_data_file:
            hourly_data = processor.load_hourly_data(request.hourly_data_file)
        else:
            # Create uniform distribution
            hourly_data = processor.create_hourly_data_from_total(
                annual_cert.total_mwh,
                annual_cert.year,
                annual_cert.source_type
            )
        
        # Convert
        result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)
        
        # Register hourly certificates
        registration_stats = registry.register_certificates(result.hourly_certificates)
        
        return {
            "success": True,
            "conversion": {
                "annual_certificate_id": annual_cert.certificate_id,
                "total_hourly_certificates": result.total_hours,
                "total_mwh_converted": result.total_mwh_converted,
                "validation_passed": result.validation_passed,
                "validation_errors": result.validation_errors
            },
            "registration": registration_stats,
            "message": "Conversion completed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/certificates/hourly/{certificate_id}", response_model=dict)
async def get_hourly_certificate(certificate_id: str):
    """Get a specific hourly certificate"""
    cert = registry.get_certificate(certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    return {
        "success": True,
        "certificate": cert.dict()
    }


@app.get("/certificates/hourly", response_model=dict)
async def get_hourly_certificates(
    parent_id: Optional[str] = Query(None, description="Filter by parent certificate ID"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get hourly certificates with optional filters"""
    if parent_id:
        certificates = registry.get_certificates_by_parent(parent_id)
    elif owner:
        certificates = registry.get_certificates_by_owner(owner)
    elif source_type:
        certificates = registry.get_certificates_by_source(SourceType(source_type))
    elif start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        certificates = registry.get_certificates_by_date_range(start, end)
    else:
        certificates = list(registry.hourly_certificates.values())
    
    return {
        "success": True,
        "count": len(certificates),
        "certificates": [cert.dict() for cert in certificates]
    }


@app.post("/certificates/trade", response_model=dict)
async def trade_certificates(request: TradeRequest):
    """Trade certificates between owners"""
    try:
        trade = trading.trade_certificates(
            request.certificate_ids,
            request.from_owner,
            request.to_owner,
            request.price_per_mwh
        )
        
        return {
            "success": True,
            "trade": trade.dict(),
            "message": "Trade completed successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/certificates/validate/{certificate_id}", response_model=dict)
async def validate_certificate(certificate_id: str):
    """Validate a certificate or conversion"""
    # Check if it's an annual certificate
    annual_cert = registry.get_annual_certificate(certificate_id)
    if annual_cert:
        validation = validator.validate_annual_certificate(annual_cert)
        hourly_certs = registry.get_certificates_by_parent(certificate_id)
        
        if hourly_certs:
            conversion_validation = validator.validate_conversion(annual_cert, hourly_certs)
            return {
                "success": True,
                "type": "annual_with_conversion",
                "annual_validation": validation,
                "conversion_validation": conversion_validation
            }
        else:
            return {
                "success": True,
                "type": "annual",
                "validation": validation
            }
    
    # Check if it's an hourly certificate
    hourly_cert = registry.get_certificate(certificate_id)
    if hourly_cert:
        validation = validator.validate_hourly_certificate(hourly_cert)
        return {
            "success": True,
            "type": "hourly",
            "validation": validation
        }
    
    raise HTTPException(status_code=404, detail="Certificate not found")


@app.get("/certificates/statistics", response_model=dict)
async def get_statistics():
    """Get registry statistics"""
    stats = registry.get_statistics()
    trading_stats = trading.get_trading_statistics()
    
    return {
        "success": True,
        "registry": stats,
        "trading": trading_stats
    }


@app.get("/trades/{trade_id}", response_model=dict)
async def get_trade(trade_id: str):
    """Get a specific trade"""
    trade = trading.get_trade(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return {
        "success": True,
        "trade": trade.dict()
    }


@app.get("/trades", response_model=dict)
async def get_trades(owner: Optional[str] = Query(None)):
    """Get trades, optionally filtered by owner"""
    if owner:
        trades = trading.get_trades_by_owner(owner)
    else:
        trades = list(trading.trades.values())
    
    return {
        "success": True,
        "count": len(trades),
        "trades": [trade.dict() for trade in trades]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

