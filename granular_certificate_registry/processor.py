"""
Certificate Processing Engine

Converts annual certificates into hourly certificates using real electricity generation data.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from .models import (
    AnnualCertificate,
    HourlyCertificate,
    HourlyGenerationData,
    ConversionResult,
    SourceType,
    CertificateStatus
)


class CertificateProcessor:
    """Processes annual certificates into hourly certificates"""
    
    def __init__(self):
        self.processed_certificates: Dict[str, List[HourlyCertificate]] = {}
    
    def load_hourly_data(self, file_path: str, source_type: Optional[SourceType] = None) -> pd.DataFrame:
        """
        Load hourly generation data from CSV file.
        
        Expected CSV format:
        - timestamp: datetime string
        - mwh: float (MWh generated)
        - source_type: string (optional, if not provided uses parameter)
        
        Args:
            file_path: Path to CSV file
            source_type: Source type if not in CSV
            
        Returns:
            DataFrame with hourly generation data
        """
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        if 'source_type' not in df.columns and source_type:
            df['source_type'] = source_type.value
        
        # Ensure we have exactly 8760 hours for a full year
        if len(df) != 8760:
            raise ValueError(f"Expected 8760 hours of data, got {len(df)}")
        
        return df
    
    def create_hourly_data_from_total(
        self, 
        total_mwh: float, 
        year: int,
        source_type: SourceType,
        distribution: Optional[List[float]] = None
    ) -> pd.DataFrame:
        """
        Create hourly data from total MWh with optional distribution pattern.
        
        Args:
            total_mwh: Total MWh for the year
            year: Year
            source_type: Source type
            distribution: Optional list of 8760 values representing hourly distribution (0-1)
            
        Returns:
            DataFrame with hourly generation data
        """
        start_date = datetime(year, 1, 1, 0, 0, 0)
        hours = []
        
        if distribution:
            if len(distribution) != 8760:
                raise ValueError("Distribution must have exactly 8760 values")
            # Normalize distribution
            dist_sum = sum(distribution)
            if dist_sum == 0:
                raise ValueError("Distribution cannot sum to zero")
            normalized = [d / dist_sum for d in distribution]
            hourly_mwh = [total_mwh * n for n in normalized]
        else:
            # Uniform distribution
            hourly_mwh = [total_mwh / 8760] * 8760
        
        for i, mwh in enumerate(hourly_mwh):
            timestamp = start_date + timedelta(hours=i)
            hours.append({
                'timestamp': timestamp,
                'mwh': mwh,
                'source_type': source_type.value
            })
        
        return pd.DataFrame(hours)
    
    def convert_to_hourly(
        self,
        annual_cert: AnnualCertificate,
        hourly_data: pd.DataFrame,
        validate: bool = True
    ) -> ConversionResult:
        """
        Convert annual certificate to hourly certificates.
        
        Args:
            annual_cert: Annual certificate to convert
            hourly_data: DataFrame with hourly generation data (8760 hours)
            validate: Whether to validate the conversion
            
        Returns:
            ConversionResult with hourly certificates
        """
        if annual_cert.status != CertificateStatus.CANCELED:
            raise ValueError(f"Certificate must be canceled before conversion. Current status: {annual_cert.status}")
        
        if len(hourly_data) != 8760:
            raise ValueError(f"Expected 8760 hours of data, got {len(hourly_data)}")
        
        # Calculate total MWh in hourly data
        total_hourly_mwh = hourly_data['mwh'].sum()
        
        # Calculate scaling factor to match annual certificate total
        if total_hourly_mwh == 0:
            raise ValueError("Hourly data total is zero")
        
        scale_factor = annual_cert.total_mwh / total_hourly_mwh
        
        # Create hourly certificates
        hourly_certificates = []
        for idx, row in hourly_data.iterrows():
            timestamp = pd.to_datetime(row['timestamp'])
            hourly_mwh = row['mwh'] * scale_factor
            
            # Skip hours with zero generation
            if hourly_mwh <= 0:
                continue
            
            hourly_cert_id = f"HOURLY-{annual_cert.certificate_id}-{timestamp.strftime('%Y%m%d%H')}"
            
            hourly_cert = HourlyCertificate(
                certificate_id=hourly_cert_id,
                parent_certificate_id=annual_cert.certificate_id,
                timestamp=timestamp,
                mwh=hourly_mwh,
                source_type=annual_cert.source_type,
                status=CertificateStatus.ACTIVE,
                metadata={
                    'original_hourly_mwh': float(row['mwh']),
                    'scale_factor': scale_factor,
                    'year': annual_cert.year
                }
            )
            hourly_certificates.append(hourly_cert)
        
        # Store processed certificates
        self.processed_certificates[annual_cert.certificate_id] = hourly_certificates
        
        # Create conversion result
        result = ConversionResult(
            annual_certificate=annual_cert,
            hourly_certificates=hourly_certificates,
            total_hours=len(hourly_certificates),
            total_mwh_converted=sum(cert.mwh for cert in hourly_certificates)
        )
        
        # Validate if requested
        if validate:
            from .validator import CertificateValidator
            validator = CertificateValidator()
            validation_result = validator.validate_conversion(annual_cert, hourly_certificates)
            result.validation_passed = validation_result['valid']
            result.validation_errors = validation_result.get('errors', [])
        
        return result
    
    def get_processed_certificates(self, annual_cert_id: str) -> Optional[List[HourlyCertificate]]:
        """Get processed hourly certificates for an annual certificate"""
        return self.processed_certificates.get(annual_cert_id)
    
    def get_all_processed_certificates(self) -> Dict[str, List[HourlyCertificate]]:
        """Get all processed certificates"""
        return self.processed_certificates.copy()

