"""
Certificate Registry and Tracking System

Manages registration, storage, and tracking of certificates.
"""

from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict
from .models import (
    AnnualCertificate,
    HourlyCertificate,
    CertificateStatus,
    SourceType
)


class CertificateRegistry:
    """Registry for managing certificates"""
    
    def __init__(self):
        """Initialize the registry"""
        self.annual_certificates: Dict[str, AnnualCertificate] = {}
        self.hourly_certificates: Dict[str, HourlyCertificate] = {}
        self.certificates_by_parent: Dict[str, List[str]] = defaultdict(list)
        self.certificates_by_owner: Dict[str, Set[str]] = defaultdict(set)
        self.certificates_by_timestamp: Dict[datetime, List[str]] = defaultdict(list)
        self.certificates_by_source: Dict[SourceType, Set[str]] = defaultdict(set)
    
    def register_annual_certificate(self, cert: AnnualCertificate) -> bool:
        """
        Register an annual certificate.
        
        Args:
            cert: Annual certificate to register
            
        Returns:
            True if registered successfully, False if already exists
        """
        if cert.certificate_id in self.annual_certificates:
            return False
        
        self.annual_certificates[cert.certificate_id] = cert
        return True
    
    def register_hourly_certificate(self, cert: HourlyCertificate) -> bool:
        """
        Register a single hourly certificate.
        
        Args:
            cert: Hourly certificate to register
            
        Returns:
            True if registered successfully, False if already exists
        """
        if cert.certificate_id in self.hourly_certificates:
            return False
        
        self.hourly_certificates[cert.certificate_id] = cert
        self.certificates_by_parent[cert.parent_certificate_id].append(cert.certificate_id)
        
        if cert.owner:
            self.certificates_by_owner[cert.owner].add(cert.certificate_id)
        
        # Index by timestamp (rounded to hour)
        hour_timestamp = cert.timestamp.replace(minute=0, second=0, microsecond=0)
        self.certificates_by_timestamp[hour_timestamp].append(cert.certificate_id)
        
        self.certificates_by_source[cert.source_type].add(cert.certificate_id)
        
        return True
    
    def register_certificates(self, certificates: List[HourlyCertificate]) -> Dict[str, int]:
        """
        Register multiple hourly certificates.
        
        Args:
            certificates: List of hourly certificates
            
        Returns:
            Dictionary with registration statistics
        """
        registered = 0
        skipped = 0
        
        for cert in certificates:
            if self.register_hourly_certificate(cert):
                registered += 1
            else:
                skipped += 1
        
        return {
            'registered': registered,
            'skipped': skipped,
            'total': len(certificates)
        }
    
    def get_certificate(self, certificate_id: str) -> Optional[HourlyCertificate]:
        """Get a certificate by ID"""
        return self.hourly_certificates.get(certificate_id)
    
    def get_annual_certificate(self, certificate_id: str) -> Optional[AnnualCertificate]:
        """Get an annual certificate by ID"""
        return self.annual_certificates.get(certificate_id)
    
    def get_certificates_by_parent(self, parent_id: str) -> List[HourlyCertificate]:
        """Get all hourly certificates for a parent annual certificate"""
        cert_ids = self.certificates_by_parent.get(parent_id, [])
        return [self.hourly_certificates[cid] for cid in cert_ids if cid in self.hourly_certificates]
    
    def get_certificates_by_owner(self, owner: str) -> List[HourlyCertificate]:
        """Get all certificates owned by a specific owner"""
        cert_ids = self.certificates_by_owner.get(owner, set())
        return [self.hourly_certificates[cid] for cid in cert_ids if cid in self.hourly_certificates]
    
    def get_certificates_by_timestamp(
        self,
        timestamp: datetime,
        exact: bool = False
    ) -> List[HourlyCertificate]:
        """
        Get certificates for a specific timestamp.
        
        Args:
            timestamp: Timestamp to search for
            exact: If True, match exact timestamp; if False, match hour
            
        Returns:
            List of certificates
        """
        if exact:
            search_timestamp = timestamp
        else:
            search_timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
        
        cert_ids = self.certificates_by_timestamp.get(search_timestamp, [])
        return [self.hourly_certificates[cid] for cid in cert_ids if cid in self.hourly_certificates]
    
    def get_certificates_by_source(self, source_type: SourceType) -> List[HourlyCertificate]:
        """Get all certificates for a specific source type"""
        cert_ids = self.certificates_by_source.get(source_type, set())
        return [self.hourly_certificates[cid] for cid in cert_ids if cid in self.hourly_certificates]
    
    def get_certificates_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[HourlyCertificate]:
        """Get all certificates in a date range"""
        results = []
        current = start_date.replace(minute=0, second=0, microsecond=0)
        end = end_date.replace(minute=0, second=0, microsecond=0)
        
        while current <= end:
            results.extend(self.get_certificates_by_timestamp(current))
            current = current.replace(hour=current.hour + 1) if current.hour < 23 else \
                     current.replace(day=current.day + 1, hour=0)
        
        return results
    
    def update_certificate_status(
        self,
        certificate_id: str,
        status: CertificateStatus
    ) -> bool:
        """
        Update certificate status.
        
        Args:
            certificate_id: Certificate ID
            status: New status
            
        Returns:
            True if updated, False if certificate not found
        """
        if certificate_id not in self.hourly_certificates:
            return False
        
        self.hourly_certificates[certificate_id].status = status
        return True
    
    def update_certificate_owner(
        self,
        certificate_id: str,
        owner: str
    ) -> bool:
        """
        Update certificate owner.
        
        Args:
            certificate_id: Certificate ID
            owner: New owner
            
        Returns:
            True if updated, False if certificate not found
        """
        if certificate_id not in self.hourly_certificates:
            return False
        
        cert = self.hourly_certificates[certificate_id]
        
        # Remove from old owner
        if cert.owner:
            self.certificates_by_owner[cert.owner].discard(certificate_id)
        
        # Add to new owner
        cert.owner = owner
        self.certificates_by_owner[owner].add(certificate_id)
        
        return True
    
    def get_statistics(self) -> Dict[str, any]:
        """Get registry statistics"""
        total_mwh = sum(cert.mwh for cert in self.hourly_certificates.values())
        
        return {
            'total_annual_certificates': len(self.annual_certificates),
            'total_hourly_certificates': len(self.hourly_certificates),
            'total_mwh': total_mwh,
            'certificates_by_source': {
                source.value: len(certs)
                for source, certs in self.certificates_by_source.items()
            },
            'certificates_by_status': {
                status.value: sum(
                    1 for cert in self.hourly_certificates.values()
                    if cert.status == status
                )
                for status in CertificateStatus
            },
            'total_owners': len(self.certificates_by_owner)
        }

