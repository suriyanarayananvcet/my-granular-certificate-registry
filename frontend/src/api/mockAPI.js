// Mock API for demo when backend is unavailable
export const mockLogin = () => {
  return Promise.resolve({
    data: {
      access_token: "demo_token_12345",
      token_type: "bearer",
      user_id: 1
    }
  });
};

export const mockCertificates = () => {
  return Promise.resolve({
    data: [
      {
        id: "CERT-2024-001",
        total_mwh: 1000.0,
        year: 2024,
        source_type: "solar",
        status: "active",
        hourly_certificates: 8760,
        device_id: "SOLAR-001"
      },
      {
        id: "CERT-2024-002", 
        total_mwh: 750.5,
        year: 2024,
        source_type: "wind",
        status: "converted",
        hourly_certificates: 8760,
        device_id: "WIND-001"
      }
    ]
  });
};

export const mockHourlyData = () => {
  return Promise.resolve({
    data: Array.from({length: 24}, (_, i) => ({
      hour: i,
      generation_kwh: Math.random() * 100 + 20,
      certificate_id: `GC-${String(i).padStart(4, '0')}`,
      timestamp: `2024-01-01T${String(i).padStart(2, '0')}:00:00Z`
    }))
  });
};