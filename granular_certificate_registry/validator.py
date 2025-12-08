"""
Certificate Validation System

Validates certificate conversions and data integrity.
"""

from typing import List, Dict, Any
from datetime import datetime
from .models import AnnualCertificate, HourlyCertificate


class CertificateValidator:
    """Validates certificate conversions and data integrity"""
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize validator.
        
        Args:
            tolerance: Tolerance for MWh matching (default 0.01 MWh = 0.1%)
        """
        self.tolerance = tolerance
    
    def validate_conversion(
        self,
        annual_cert: AnnualCertificate,
        hourly_certs: List[HourlyCertificate]
    ) -> Dict[str, Any]:
        """
        Validate that hourly certificates match the annual certificate.
        
        Args:
            annual_cert: Original annual certificate
            hourly_certs: List of hourly certificates
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check total MWh matches
        total_hourly_mwh = sum(cert.mwh for cert in hourly_certs)
        mwh_diff = abs(total_hourly_mwh - annual_cert.total_mwh)
        
        if mwh_diff > self.tolerance:
            errors.append(
                f"MWh mismatch: Annual={annual_cert.total_mwh:.4f} MWh, "
                f"Hourly total={total_hourly_mwh:.4f} MWh, "
                f"Difference={mwh_diff:.4f} MWh"
            )
        
        # Check year matches
        for cert in hourly_certs:
            if cert.timestamp.year != annual_cert.year:
                errors.append(
                    f"Year mismatch: Hourly cert {cert.certificate_id} "
                    f"has year {cert.timestamp.year}, expected {annual_cert.year}"
                )
        
        # Check source type matches
        for cert in hourly_certs:
            if cert.source_type != annual_cert.source_type:
                errors.append(
                    f"Source type mismatch: Hourly cert {cert.certificate_id} "
                    f"has {cert.source_type}, expected {annual_cert.source_type}"
                )
        
        # Check parent certificate ID
        for cert in hourly_certs:
            if cert.parent_certificate_id != annual_cert.certificate_id:
                errors.append(
                    f"Parent ID mismatch: Hourly cert {cert.certificate_id} "
                    f"has parent {cert.parent_certificate_id}, "
                    f"expected {annual_cert.certificate_id}"
                )
        
        # Check for duplicate timestamps
        timestamps = [cert.timestamp for cert in hourly_certs]
        if len(timestamps) != len(set(timestamps)):
            errors.append("Duplicate timestamps found in hourly certificates")
        
        # Check for gaps in hourly sequence
        if len(hourly_certs) < 8760:
            warnings.append(
                f"Only {len(hourly_certs)} hourly certificates created, "
                f"expected up to 8760 (some hours may have zero generation)"
            )
        
        # Check certificate IDs are unique
        cert_ids = [cert.certificate_id for cert in hourly_certs]
        if len(cert_ids) != len(set(cert_ids)):
            errors.append("Duplicate certificate IDs found")
        
        # Check all certificates are active
        inactive_certs = [c for c in hourly_certs if c.status.value != "active"]
        if inactive_certs:
            warnings.append(
                f"{len(inactive_certs)} certificates are not in active status"
            )
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'total_mwh_annual': annual_cert.total_mwh,
            'total_mwh_hourly': total_hourly_mwh,
            'mwh_difference': mwh_diff,
            'total_hourly_certs': len(hourly_certs)
        }
    
    def validate_hourly_certificate(self, cert: HourlyCertificate) -> Dict[str, Any]:
        """
        Validate a single hourly certificate.
        
        Args:
            cert: Hourly certificate to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check MWh is positive
        if cert.mwh <= 0:
            errors.append(f"MWh must be positive, got {cert.mwh}")
        
        # Check certificate ID format
        if not cert.certificate_id.startswith('HOURLY-'):
            errors.append("Certificate ID must start with 'HOURLY-'")
        
        # Check timestamp is valid
        if cert.timestamp.year < 2000 or cert.timestamp.year > 2100:
            warnings.append(f"Unusual year: {cert.timestamp.year}")
        
        # Check parent certificate ID exists
        if not cert.parent_certificate_id:
            errors.append("Parent certificate ID is required")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_annual_certificate(self, cert: AnnualCertificate) -> Dict[str, Any]:
        """
        Validate an annual certificate.
        
        Args:
            cert: Annual certificate to validate
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Check MWh is positive
        if cert.total_mwh <= 0:
            errors.append(f"Total MWh must be positive, got {cert.total_mwh}")
        
        # Check year is valid
        if cert.year < 2000 or cert.year > 2100:
            warnings.append(f"Unusual year: {cert.year}")
        
        # Check status
        if cert.status.value not in ['canceled', 'active', 'traded', 'retired', 'pending']:
            errors.append(f"Invalid status: {cert.status}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

