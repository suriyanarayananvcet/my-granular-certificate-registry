"""
Example usage of the Granular Certificate Registry System

This demonstrates how to:
1. Create an annual certificate
2. Convert it to hourly certificates
3. Validate the conversion
4. Register certificates
5. Trade certificates
"""

from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from granular_certificate_registry import (
    AnnualCertificate,
    CertificateProcessor,
    CertificateValidator,
    CertificateRegistry,
    CertificateTrading,
    SourceType,
    CertificateStatus
)


def example_basic_conversion():
    """Basic example: Convert annual certificate to hourly"""
    print("=" * 60)
    print("Example 1: Basic Annual to Hourly Conversion")
    print("=" * 60)
    
    # Step 1: Create an annual certificate
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-001",
        total_mwh=1000.0,
        year=2024,
        source_type=SourceType.SOLAR,
        status=CertificateStatus.CANCELED,
        issuer="Solar Farm Inc.",
        metadata={"location": "California", "facility_id": "SF-001"}
    )
    
    print(f"\nCreated annual certificate:")
    print(f"  ID: {annual_cert.certificate_id}")
    print(f"  Total MWh: {annual_cert.total_mwh}")
    print(f"  Year: {annual_cert.year}")
    print(f"  Source: {annual_cert.source_type}")
    
    # Step 2: Create processor and generate hourly data
    processor = CertificateProcessor()
    
    # Create hourly data with uniform distribution
    hourly_data = processor.create_hourly_data_from_total(
        total_mwh=annual_cert.total_mwh,
        year=annual_cert.year,
        source_type=annual_cert.source_type
    )
    
    print(f"\nGenerated {len(hourly_data)} hours of data")
    print(f"  Total MWh in hourly data: {hourly_data['mwh'].sum():.4f}")
    
    # Step 3: Convert to hourly certificates
    result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)
    
    print(f"\nConversion completed:")
    print(f"  Total hourly certificates: {result.total_hours}")
    print(f"  Total MWh converted: {result.total_mwh_converted:.4f}")
    print(f"  Validation passed: {result.validation_passed}")
    
    if result.validation_errors:
        print(f"  Validation errors: {result.validation_errors}")
    
    # Step 4: Show sample hourly certificates
    print(f"\nSample hourly certificates (first 5):")
    for cert in result.hourly_certificates[:5]:
        print(f"  {cert.certificate_id}: {cert.timestamp} = {cert.mwh:.4f} MWh")
    
    return annual_cert, result


def example_with_registry():
    """Example with registry and tracking"""
    print("\n" + "=" * 60)
    print("Example 2: Registry and Tracking")
    print("=" * 60)
    
    # Create components
    registry = CertificateRegistry()
    processor = CertificateProcessor()
    
    # Create and register annual certificate
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-002",
        total_mwh=500.0,
        year=2024,
        source_type=SourceType.WIND,
        status=CertificateStatus.CANCELED
    )
    
    registry.register_annual_certificate(annual_cert)
    print(f"\nRegistered annual certificate: {annual_cert.certificate_id}")
    
    # Convert to hourly
    hourly_data = processor.create_hourly_data_from_total(
        annual_cert.total_mwh,
        annual_cert.year,
        annual_cert.source_type
    )
    
    result = processor.convert_to_hourly(annual_cert, hourly_data)
    
    # Register hourly certificates
    registration_stats = registry.register_certificates(result.hourly_certificates)
    print(f"\nRegistration stats:")
    print(f"  Registered: {registration_stats['registered']}")
    print(f"  Skipped: {registration_stats['skipped']}")
    
    # Get statistics
    stats = registry.get_statistics()
    print(f"\nRegistry statistics:")
    print(f"  Total annual certificates: {stats['total_annual_certificates']}")
    print(f"  Total hourly certificates: {stats['total_hourly_certificates']}")
    print(f"  Total MWh: {stats['total_mwh']:.2f}")
    
    # Query certificates
    hourly_certs = registry.get_certificates_by_parent(annual_cert.certificate_id)
    print(f"\nFound {len(hourly_certs)} hourly certificates for parent {annual_cert.certificate_id}")
    
    return registry, annual_cert


def example_trading():
    """Example of certificate trading"""
    print("\n" + "=" * 60)
    print("Example 3: Certificate Trading")
    print("=" * 60)
    
    # Setup
    registry = CertificateRegistry()
    trading = CertificateTrading(registry)
    processor = CertificateProcessor()
    
    # Create annual certificate
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-003",
        total_mwh=2000.0,
        year=2024,
        source_type=SourceType.SOLAR,
        status=CertificateStatus.CANCELED
    )
    
    registry.register_annual_certificate(annual_cert)
    
    # Convert to hourly
    hourly_data = processor.create_hourly_data_from_total(
        annual_cert.total_mwh,
        annual_cert.year,
        annual_cert.source_type
    )
    
    result = processor.convert_to_hourly(annual_cert, hourly_data)
    registry.register_certificates(result.hourly_certificates)
    
    # Assign initial owner
    for cert in result.hourly_certificates[:100]:  # First 100 certificates
        registry.update_certificate_owner(cert.certificate_id, "Solar Farm Inc.")
    
    print(f"\nAssigned first 100 certificates to 'Solar Farm Inc.'")
    
    # Get certificates owned by Solar Farm Inc.
    owner_certs = registry.get_certificates_by_owner("Solar Farm Inc.")
    print(f"  Total certificates owned: {len(owner_certs)}")
    print(f"  Total MWh owned: {sum(c.mwh for c in owner_certs):.2f}")
    
    # Trade some certificates
    cert_ids_to_trade = [c.certificate_id for c in owner_certs[:50]]
    
    print(f"\nTrading {len(cert_ids_to_trade)} certificates...")
    trade = trading.trade_certificates(
        certificate_ids=cert_ids_to_trade,
        from_owner="Solar Farm Inc.",
        to_owner="Green Energy Corp.",
        price_per_mwh=50.0
    )
    
    print(f"\nTrade completed:")
    print(f"  Trade ID: {trade.trade_id}")
    print(f"  From: {trade.from_owner}")
    print(f"  To: {trade.to_owner}")
    print(f"  Certificates: {len(trade.certificate_ids)}")
    print(f"  Total MWh: {trade.metadata['total_mwh']:.2f}")
    print(f"  Price per MWh: ${trade.price_per_mwh}")
    print(f"  Total price: ${trade.total_price:.2f}")
    
    # Check new ownership
    new_owner_certs = registry.get_certificates_by_owner("Green Energy Corp.")
    print(f"\nGreen Energy Corp. now owns {len(new_owner_certs)} certificates")
    
    # Trading statistics
    trading_stats = trading.get_trading_statistics()
    print(f"\nTrading statistics:")
    print(f"  Total trades: {trading_stats['total_trades']}")
    print(f"  Total MWh traded: {trading_stats['total_mwh_traded']:.2f}")
    print(f"  Total value: ${trading_stats['total_value']:.2f}")
    
    return trading


def example_validation():
    """Example of validation"""
    print("\n" + "=" * 60)
    print("Example 4: Validation")
    print("=" * 60)
    
    validator = CertificateValidator()
    processor = CertificateProcessor()
    
    # Create annual certificate
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-004",
        total_mwh=750.0,
        year=2024,
        source_type=SourceType.HYDRO,
        status=CertificateStatus.CANCELED
    )
    
    # Convert to hourly
    hourly_data = processor.create_hourly_data_from_total(
        annual_cert.total_mwh,
        annual_cert.year,
        annual_cert.source_type
    )
    
    result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)
    
    # Validate conversion
    validation = validator.validate_conversion(annual_cert, result.hourly_certificates)
    
    print(f"\nValidation results:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Annual MWh: {validation['total_mwh_annual']:.4f}")
    print(f"  Hourly MWh total: {validation['total_mwh_hourly']:.4f}")
    print(f"  Difference: {validation['mwh_difference']:.6f} MWh")
    print(f"  Total hourly certificates: {validation['total_hourly_certs']}")
    
    if validation['errors']:
        print(f"\n  Errors:")
        for error in validation['errors']:
            print(f"    - {error}")
    
    if validation['warnings']:
        print(f"\n  Warnings:")
        for warning in validation['warnings']:
            print(f"    - {warning}")
    
    return validation


def example_query_by_timestamp():
    """Example of querying certificates by timestamp"""
    print("\n" + "=" * 60)
    print("Example 5: Query by Timestamp")
    print("=" * 60)
    
    registry = CertificateRegistry()
    processor = CertificateProcessor()
    
    # Create and convert certificate
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-005",
        total_mwh=1000.0,
        year=2024,
        source_type=SourceType.SOLAR,
        status=CertificateStatus.CANCELED
    )
    
    registry.register_annual_certificate(annual_cert)
    hourly_data = processor.create_hourly_data_from_total(
        annual_cert.total_mwh,
        annual_cert.year,
        annual_cert.source_type
    )
    
    result = processor.convert_to_hourly(annual_cert, hourly_data)
    registry.register_certificates(result.hourly_certificates)
    
    # Query for a specific date/time
    target_time = datetime(2024, 3, 15, 14, 0, 0)  # March 15, 2024 at 2 PM
    certs_at_time = registry.get_certificates_by_timestamp(target_time)
    
    print(f"\nCertificates at {target_time}:")
    print(f"  Found {len(certs_at_time)} certificates")
    
    if certs_at_time:
        cert = certs_at_time[0]
        print(f"  Example: {cert.certificate_id}")
        print(f"    MWh: {cert.mwh:.4f}")
        print(f"    Source: {cert.source_type}")
        print(f"    Parent: {cert.parent_certificate_id}")
    
    # Query for a date range
    start_date = datetime(2024, 6, 1, 0, 0, 0)
    end_date = datetime(2024, 6, 30, 23, 0, 0)
    certs_in_range = registry.get_certificates_by_date_range(start_date, end_date)
    
    print(f"\nCertificates in June 2024:")
    print(f"  Found {len(certs_in_range)} certificates")
    print(f"  Total MWh: {sum(c.mwh for c in certs_in_range):.2f}")
    
    return certs_at_time, certs_in_range


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Granular Certificate Registry System - Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_conversion()
    example_with_registry()
    example_trading()
    example_validation()
    example_query_by_timestamp()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)

