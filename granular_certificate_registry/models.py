"""
Data models for the Granular Certificate Registry System
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, validator
import pandas as pd


class CertificateStatus(str, Enum):
    """Status of a certificate"""
    ACTIVE = "active"
    CANCELED = "canceled"
    TRADED = "traded"
    RETIRED = "retired"
    PENDING = "pending"


class SourceType(str, Enum):
    """Type of renewable energy source"""
    SOLAR = "solar"
    WIND = "wind"
    HYDRO = "hydro"
    GEOTHERMAL = "geothermal"
    BIOMASS = "biomass"
    OTHER = "other"


class AnnualCertificate(BaseModel):
    """Annual energy certificate model"""
    certificate_id: str = Field(..., description="Unique certificate identifier")
    total_mwh: float = Field(..., gt=0, description="Total MWh for the year")
    year: int = Field(..., ge=2000, le=2100, description="Year of the certificate")
    source_type: SourceType = Field(..., description="Type of renewable energy source")
    status: CertificateStatus = Field(default=CertificateStatus.CANCELED, description="Certificate status")
    issuer: Optional[str] = Field(None, description="Certificate issuer")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True


class HourlyGenerationData(BaseModel):
    """Hourly electricity generation data"""
    timestamp: datetime = Field(..., description="Hour timestamp")
    mwh: float = Field(..., ge=0, description="MWh generated in this hour")
    source_type: SourceType = Field(..., description="Type of energy source")
    
    class Config:
        use_enum_values = True


class HourlyCertificate(BaseModel):
    """Hourly energy certificate model"""
    certificate_id: str = Field(..., description="Unique hourly certificate identifier")
    parent_certificate_id: str = Field(..., description="Parent annual certificate ID")
    timestamp: datetime = Field(..., description="Hour timestamp")
    mwh: float = Field(..., gt=0, description="MWh for this hour")
    source_type: SourceType = Field(..., description="Type of renewable energy source")
    status: CertificateStatus = Field(default=CertificateStatus.ACTIVE, description="Certificate status")
    owner: Optional[str] = Field(None, description="Current owner")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        use_enum_values = True

    @validator('certificate_id')
    def validate_certificate_id(cls, v):
        """Ensure certificate ID follows format"""
        if not v.startswith('HOURLY-'):
            raise ValueError("Hourly certificate ID must start with 'HOURLY-'")
        return v


class CertificateTrade(BaseModel):
    """Certificate trade model"""
    trade_id: str = Field(..., description="Unique trade identifier")
    certificate_ids: List[str] = Field(..., description="List of certificate IDs being traded")
    from_owner: str = Field(..., description="Current owner")
    to_owner: str = Field(..., description="New owner")
    trade_date: datetime = Field(default_factory=datetime.now, description="Trade timestamp")
    price_per_mwh: Optional[float] = Field(None, ge=0, description="Price per MWh")
    total_price: Optional[float] = Field(None, ge=0, description="Total trade price")
    metadata: dict = Field(default_factory=dict, description="Additional trade metadata")

    class Config:
        use_enum_values = True


class ConversionResult(BaseModel):
    """Result of annual to hourly conversion"""
    annual_certificate: AnnualCertificate
    hourly_certificates: List[HourlyCertificate]
    total_hours: int
    total_mwh_converted: float
    conversion_date: datetime = Field(default_factory=datetime.now)
    validation_passed: bool = False
    validation_errors: List[str] = Field(default_factory=list)

