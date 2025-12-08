"""
Granular Certificate Registry System

A system that converts annual energy certificates into hourly certificates
using real electricity generation data.
"""

from .models import (
    AnnualCertificate,
    HourlyCertificate,
    HourlyGenerationData,
    CertificateStatus,
    SourceType
)
from .processor import CertificateProcessor
from .validator import CertificateValidator
from .registry import CertificateRegistry
from .trading import CertificateTrading

__version__ = "1.0.0"
__all__ = [
    "AnnualCertificate",
    "HourlyCertificate",
    "HourlyGenerationData",
    "CertificateStatus",
    "SourceType",
    "CertificateProcessor",
    "CertificateValidator",
    "CertificateRegistry",
    "CertificateTrading",
]

