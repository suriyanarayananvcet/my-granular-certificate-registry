"""
Tests for the Granular Certificate Registry System
"""

import unittest
from datetime import datetime
from granular_certificate_registry import (
    AnnualCertificate,
    HourlyCertificate,
    CertificateProcessor,
    CertificateValidator,
    CertificateRegistry,
    CertificateTrading,
    SourceType,
    CertificateStatus
)


class TestCertificateModels(unittest.TestCase):
    """Test certificate models"""
    
    def test_annual_certificate_creation(self):
        """Test creating an annual certificate"""
        cert = AnnualCertificate(
            certificate_id="TEST-001",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR
        )
        
        self.assertEqual(cert.certificate_id, "TEST-001")
        self.assertEqual(cert.total_mwh, 1000.0)
        self.assertEqual(cert.year, 2024)
        self.assertEqual(cert.source_type, SourceType.SOLAR)
        self.assertEqual(cert.status, CertificateStatus.CANCELED)
    
    def test_hourly_certificate_creation(self):
        """Test creating an hourly certificate"""
        cert = HourlyCertificate(
            certificate_id="HOURLY-TEST-001-2024010100",
            parent_certificate_id="TEST-001",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            mwh=0.5,
            source_type=SourceType.SOLAR
        )
        
        self.assertEqual(cert.certificate_id, "HOURLY-TEST-001-2024010100")
        self.assertEqual(cert.mwh, 0.5)
        self.assertEqual(cert.parent_certificate_id, "TEST-001")


class TestCertificateProcessor(unittest.TestCase):
    """Test certificate processor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = CertificateProcessor()
        self.annual_cert = AnnualCertificate(
            certificate_id="TEST-002",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR,
            status=CertificateStatus.CANCELED
        )
    
    def test_create_hourly_data(self):
        """Test creating hourly data"""
        hourly_data = self.processor.create_hourly_data_from_total(
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR
        )
        
        self.assertEqual(len(hourly_data), 8760)
        self.assertAlmostEqual(hourly_data['mwh'].sum(), 1000.0, places=2)
    
    def test_convert_to_hourly(self):
        """Test converting annual to hourly certificates"""
        hourly_data = self.processor.create_hourly_data_from_total(
            self.annual_cert.total_mwh,
            self.annual_cert.year,
            self.annual_cert.source_type
        )
        
        result = self.processor.convert_to_hourly(self.annual_cert, hourly_data)
        
        self.assertGreater(len(result.hourly_certificates), 0)
        self.assertAlmostEqual(
            result.total_mwh_converted,
            self.annual_cert.total_mwh,
            places=2
        )
    
    def test_conversion_requires_canceled_status(self):
        """Test that conversion requires canceled status"""
        active_cert = AnnualCertificate(
            certificate_id="TEST-003",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR,
            status=CertificateStatus.ACTIVE
        )
        
        hourly_data = self.processor.create_hourly_data_from_total(
            active_cert.total_mwh,
            active_cert.year,
            active_cert.source_type
        )
        
        with self.assertRaises(ValueError):
            self.processor.convert_to_hourly(active_cert, hourly_data)


class TestCertificateValidator(unittest.TestCase):
    """Test certificate validator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = CertificateValidator()
        self.processor = CertificateProcessor()
        self.annual_cert = AnnualCertificate(
            certificate_id="TEST-004",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR,
            status=CertificateStatus.CANCELED
        )
    
    def test_validate_conversion(self):
        """Test validating a conversion"""
        hourly_data = self.processor.create_hourly_data_from_total(
            self.annual_cert.total_mwh,
            self.annual_cert.year,
            self.annual_cert.source_type
        )
        
        result = self.processor.convert_to_hourly(self.annual_cert, hourly_data)
        validation = self.validator.validate_conversion(
            self.annual_cert,
            result.hourly_certificates
        )
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
    
    def test_validate_annual_certificate(self):
        """Test validating an annual certificate"""
        validation = self.validator.validate_annual_certificate(self.annual_cert)
        self.assertTrue(validation['valid'])
    
    def test_validate_hourly_certificate(self):
        """Test validating an hourly certificate"""
        cert = HourlyCertificate(
            certificate_id="HOURLY-TEST-005-2024010100",
            parent_certificate_id="TEST-005",
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            mwh=0.5,
            source_type=SourceType.SOLAR
        )
        
        validation = self.validator.validate_hourly_certificate(cert)
        self.assertTrue(validation['valid'])


class TestCertificateRegistry(unittest.TestCase):
    """Test certificate registry"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = CertificateRegistry()
        self.processor = CertificateProcessor()
    
    def test_register_annual_certificate(self):
        """Test registering an annual certificate"""
        cert = AnnualCertificate(
            certificate_id="TEST-006",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR
        )
        
        result = self.registry.register_annual_certificate(cert)
        self.assertTrue(result)
        
        retrieved = self.registry.get_annual_certificate("TEST-006")
        self.assertEqual(retrieved.certificate_id, "TEST-006")
    
    def test_register_hourly_certificates(self):
        """Test registering hourly certificates"""
        annual_cert = AnnualCertificate(
            certificate_id="TEST-007",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR,
            status=CertificateStatus.CANCELED
        )
        
        hourly_data = self.processor.create_hourly_data_from_total(
            annual_cert.total_mwh,
            annual_cert.year,
            annual_cert.source_type
        )
        
        result = self.processor.convert_to_hourly(annual_cert, hourly_data)
        stats = self.registry.register_certificates(result.hourly_certificates)
        
        self.assertGreater(stats['registered'], 0)
        
        # Test querying by parent
        hourly_certs = self.registry.get_certificates_by_parent("TEST-007")
        self.assertGreater(len(hourly_certs), 0)


class TestCertificateTrading(unittest.TestCase):
    """Test certificate trading"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.registry = CertificateRegistry()
        self.trading = CertificateTrading(self.registry)
        self.processor = CertificateProcessor()
        
        # Create and register certificates
        annual_cert = AnnualCertificate(
            certificate_id="TEST-008",
            total_mwh=1000.0,
            year=2024,
            source_type=SourceType.SOLAR,
            status=CertificateStatus.CANCELED
        )
        
        self.registry.register_annual_certificate(annual_cert)
        
        hourly_data = self.processor.create_hourly_data_from_total(
            annual_cert.total_mwh,
            annual_cert.year,
            annual_cert.source_type
        )
        
        result = self.processor.convert_to_hourly(annual_cert, hourly_data)
        self.registry.register_certificates(result.hourly_certificates)
        
        # Assign owner to some certificates
        for cert in result.hourly_certificates[:100]:
            self.registry.update_certificate_owner(cert.certificate_id, "Owner1")
        
        self.cert_ids = [c.certificate_id for c in result.hourly_certificates[:50]]
    
    def test_trade_certificates(self):
        """Test trading certificates"""
        trade = self.trading.trade_certificates(
            certificate_ids=self.cert_ids,
            from_owner="Owner1",
            to_owner="Owner2",
            price_per_mwh=50.0
        )
        
        self.assertEqual(trade.from_owner, "Owner1")
        self.assertEqual(trade.to_owner, "Owner2")
        self.assertEqual(len(trade.certificate_ids), 50)
        
        # Verify ownership changed
        owner2_certs = self.registry.get_certificates_by_owner("Owner2")
        self.assertGreaterEqual(len(owner2_certs), 50)


if __name__ == '__main__':
    unittest.main()

