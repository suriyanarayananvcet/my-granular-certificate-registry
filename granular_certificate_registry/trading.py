"""
Certificate Trading System

Manages trading and transfer of certificates between owners.
"""

from datetime import datetime
from typing import List, Dict, Optional
from .models import (
    HourlyCertificate,
    CertificateTrade,
    CertificateStatus
)
from .registry import CertificateRegistry


class CertificateTrading:
    """Manages certificate trading"""
    
    def __init__(self, registry: CertificateRegistry):
        """
        Initialize trading system.
        
        Args:
            registry: Certificate registry instance
        """
        self.registry = registry
        self.trades: Dict[str, CertificateTrade] = {}
    
    def trade_certificates(
        self,
        certificate_ids: List[str],
        from_owner: str,
        to_owner: str,
        price_per_mwh: Optional[float] = None
    ) -> CertificateTrade:
        """
        Trade certificates from one owner to another.
        
        Args:
            certificate_ids: List of certificate IDs to trade
            from_owner: Current owner
            to_owner: New owner
            price_per_mwh: Optional price per MWh
            
        Returns:
            CertificateTrade object
        """
        # Validate certificates exist and belong to from_owner
        certificates = []
        total_mwh = 0.0
        
        for cert_id in certificate_ids:
            cert = self.registry.get_certificate(cert_id)
            if not cert:
                raise ValueError(f"Certificate {cert_id} not found")
            
            if cert.owner != from_owner:
                raise ValueError(
                    f"Certificate {cert_id} does not belong to {from_owner}, "
                    f"current owner: {cert.owner}"
                )
            
            if cert.status != CertificateStatus.ACTIVE:
                raise ValueError(
                    f"Certificate {cert_id} is not active, status: {cert.status}"
                )
            
            certificates.append(cert)
            total_mwh += cert.mwh
        
        # Calculate total price if price_per_mwh provided
        total_price = price_per_mwh * total_mwh if price_per_mwh else None
        
        # Create trade record
        trade_id = f"TRADE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.trades)}"
        trade = CertificateTrade(
            trade_id=trade_id,
            certificate_ids=certificate_ids,
            from_owner=from_owner,
            to_owner=to_owner,
            price_per_mwh=price_per_mwh,
            total_price=total_price,
            metadata={
                'total_mwh': total_mwh,
                'certificate_count': len(certificates)
            }
        )
        
        # Execute trade - update owners
        for cert_id in certificate_ids:
            self.registry.update_certificate_owner(cert_id, to_owner)
            # Optionally mark as traded
            # self.registry.update_certificate_status(cert_id, CertificateStatus.TRADED)
        
        # Store trade record
        self.trades[trade_id] = trade
        
        return trade
    
    def get_trade(self, trade_id: str) -> Optional[CertificateTrade]:
        """Get a trade by ID"""
        return self.trades.get(trade_id)
    
    def get_trades_by_owner(self, owner: str) -> List[CertificateTrade]:
        """Get all trades involving an owner"""
        return [
            trade for trade in self.trades.values()
            if trade.from_owner == owner or trade.to_owner == owner
        ]
    
    def get_trade_history(self, certificate_id: str) -> List[CertificateTrade]:
        """Get trade history for a certificate"""
        return [
            trade for trade in self.trades.values()
            if certificate_id in trade.certificate_ids
        ]
    
    def get_trading_statistics(self) -> Dict[str, any]:
        """Get trading statistics"""
        total_trades = len(self.trades)
        total_certificates_traded = sum(
            len(trade.certificate_ids) for trade in self.trades.values()
        )
        total_mwh_traded = sum(
            trade.metadata.get('total_mwh', 0) for trade in self.trades.values()
        )
        total_value = sum(
            trade.total_price for trade in self.trades.values()
            if trade.total_price
        )
        
        return {
            'total_trades': total_trades,
            'total_certificates_traded': total_certificates_traded,
            'total_mwh_traded': total_mwh_traded,
            'total_value': total_value,
            'average_price_per_mwh': (
                total_value / total_mwh_traded
                if total_mwh_traded > 0 and total_value else None
            )
        }

