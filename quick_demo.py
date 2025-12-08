#!/usr/bin/env python3
"""
Quick Demo - See the system in action immediately!
Run this file to see a simple demonstration.
"""

import sys
import os

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from granular_certificate_registry import (
        AnnualCertificate,
        CertificateProcessor,
        CertificateRegistry,
        SourceType,
        CertificateStatus
    )
    
    print("=" * 70)
    print("🌱 GRANULAR CERTIFICATE REGISTRY - QUICK DEMO 🌱")
    print("=" * 70)
    print()
    
    # Step 1: Create an annual certificate
    print("📝 Step 1: Creating an annual certificate...")
    annual_cert = AnnualCertificate(
        certificate_id="CERT-2024-001",
        total_mwh=1000.0,
        year=2024,
        source_type=SourceType.SOLAR,
        status=CertificateStatus.CANCELED,
        issuer="Solar Farm Inc."
    )
    
    print(f"   ✅ Created: {annual_cert.certificate_id}")
    print(f"   📊 Total MWh: {annual_cert.total_mwh}")
    print(f"   📅 Year: {annual_cert.year}")
    print(f"   ⚡ Source: {annual_cert.source_type}")
    print()
    
    # Step 2: Create processor
    print("⚙️  Step 2: Initializing certificate processor...")
    processor = CertificateProcessor()
    print("   ✅ Processor ready")
    print()
    
    # Step 3: Generate hourly data
    print("📈 Step 3: Generating hourly generation data (8760 hours)...")
    hourly_data = processor.create_hourly_data_from_total(
        total_mwh=annual_cert.total_mwh,
        year=annual_cert.year,
        source_type=annual_cert.source_type
    )
    
    print(f"   ✅ Generated {len(hourly_data)} hours of data")
    print(f"   📊 Total MWh in data: {hourly_data['mwh'].sum():.4f}")
    print(f"   📊 Average per hour: {hourly_data['mwh'].mean():.4f}")
    print()
    
    # Step 4: Convert to hourly certificates
    print("🔄 Step 4: Converting annual certificate to hourly certificates...")
    result = processor.convert_to_hourly(annual_cert, hourly_data, validate=True)
    
    print(f"   ✅ Conversion complete!")
    print(f"   📦 Created {result.total_hours} hourly certificates")
    print(f"   📊 Total MWh converted: {result.total_mwh_converted:.4f}")
    print(f"   ✅ Validation: {'PASSED' if result.validation_passed else 'FAILED'}")
    print()
    
    # Step 5: Show sample certificates
    print("📋 Step 5: Sample hourly certificates (first 10):")
    print("   " + "-" * 65)
    for i, cert in enumerate(result.hourly_certificates[:10], 1):
        print(f"   {i:2d}. {cert.certificate_id}")
        print(f"       Time: {cert.timestamp.strftime('%Y-%m-%d %H:00')}")
        print(f"       MWh:  {cert.mwh:.6f}")
        print()
    
    # Step 6: Register certificates
    print("📚 Step 6: Registering certificates in registry...")
    registry = CertificateRegistry()
    registry.register_annual_certificate(annual_cert)
    stats = registry.register_certificates(result.hourly_certificates)
    
    print(f"   ✅ Registered {stats['registered']} hourly certificates")
    print()
    
    # Step 7: Get statistics
    print("📊 Step 7: Registry Statistics:")
    reg_stats = registry.get_statistics()
    print(f"   📦 Annual certificates: {reg_stats['total_annual_certificates']}")
    print(f"   📦 Hourly certificates: {reg_stats['total_hourly_certificates']}")
    print(f"   ⚡ Total MWh: {reg_stats['total_mwh']:.2f}")
    print()
    
    # Step 8: Query example
    print("🔍 Step 8: Query example - Get certificates for a specific time...")
    from datetime import datetime
    target_time = datetime(2024, 3, 15, 14, 0, 0)  # March 15, 2024 at 2 PM
    certs_at_time = registry.get_certificates_by_timestamp(target_time)
    
    print(f"   🔎 Searching for certificates at: {target_time.strftime('%Y-%m-%d %H:00')}")
    if certs_at_time:
        cert = certs_at_time[0]
        print(f"   ✅ Found: {cert.certificate_id}")
        print(f"      MWh: {cert.mwh:.6f}")
        print(f"      Source: {cert.source_type}")
    print()
    
    print("=" * 70)
    print("🎉 DEMO COMPLETE! The system is working perfectly! 🎉")
    print("=" * 70)
    print()
    print("💡 Next steps:")
    print("   1. Run 'python examples/example_usage.py' for more examples")
    print("   2. Start API: 'python -m granular_certificate_registry.api'")
    print("   3. Visit http://localhost:8000/docs for API documentation")
    print("   4. Read HOW_TO_RUN.md for detailed instructions")
    print()

except ImportError as e:
    print("❌ Error: Missing dependencies")
    print(f"   {e}")
    print()
    print("💡 Solution: Install dependencies with:")
    print("   pip install -r requirements.txt")
    print()
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

