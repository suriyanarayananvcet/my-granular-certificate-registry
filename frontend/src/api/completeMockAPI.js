// Complete Mock API for Full Granular Certificate Registry Demo

// Generate realistic data
const generateHourlyData = (totalMWh, hours = 8760) => {
  const hourlyData = [];
  let remaining = totalMWh * 1000; // Convert to kWh
  
  for (let i = 0; i < hours; i++) {
    const hour = i % 24;
    const isDay = hour >= 6 && hour <= 18;
    const baseGeneration = isDay ? Math.random() * 150 + 50 : Math.random() * 30 + 5;
    const generation = Math.min(baseGeneration, remaining);
    remaining -= generation;
    
    hourlyData.push({
      id: i + 1,
      hour: hour,
      day: Math.floor(i / 24) + 1,
      generation_kwh: parseFloat(generation.toFixed(3)),
      certificate_id: `GC-2024-${String(i + 1).padStart(6, '0')}`,
      timestamp: new Date(2024, 0, Math.floor(i / 24) + 1, hour).toISOString(),
      status: 'active',
      device_id: 'SOLAR-001'
    });
    
    if (remaining <= 0) break;
  }
  return hourlyData;
};

// Mock Data
export const mockData = {
  user: {
    id: 1,
    name: "Admin User",
    email: "admin@registry.com",
    role: 4,
    organisation: "Green Energy Corp",
    accounts: [
      { id: 1, account_name: "Main Trading Account", user_ids: [1] },
      { id: 2, account_name: "Storage Account", user_ids: [1] }
    ]
  },
  
  certificates: [
    {
      id: "CERT-2024-001",
      issuance_id: "ISS-2024-001",
      bundle_id_range: "1-8760",
      total_mwh: 1000.0,
      year: 2024,
      source_type: "solar",
      technology: "photovoltaic",
      status: "active",
      device_id: "SOLAR-001",
      device_name: "Solar Farm Alpha",
      location: "California, USA",
      hourly_certificates: 8760,
      created_at: "2024-01-01T00:00:00Z",
      expires_at: "2026-01-01T00:00:00Z",
      account_id: 1
    },
    {
      id: "CERT-2024-002",
      issuance_id: "ISS-2024-002", 
      bundle_id_range: "8761-17520",
      total_mwh: 750.5,
      year: 2024,
      source_type: "wind",
      technology: "onshore_wind",
      status: "converted",
      device_id: "WIND-001",
      device_name: "Wind Farm Beta",
      location: "Texas, USA",
      hourly_certificates: 8760,
      created_at: "2024-01-01T00:00:00Z",
      expires_at: "2026-01-01T00:00:00Z",
      account_id: 1
    },
    {
      id: "CERT-2024-003",
      issuance_id: "ISS-2024-003",
      bundle_id_range: "17521-26280", 
      total_mwh: 500.0,
      year: 2024,
      source_type: "hydro",
      technology: "run_of_river",
      status: "transferred",
      device_id: "HYDRO-001",
      device_name: "River Power Station",
      location: "Oregon, USA",
      hourly_certificates: 8760,
      created_at: "2024-01-01T00:00:00Z",
      expires_at: "2026-01-01T00:00:00Z",
      account_id: 2
    }
  ],

  devices: [
    {
      id: "SOLAR-001",
      name: "Solar Farm Alpha",
      technology: "photovoltaic",
      capacity_mw: 100,
      location: "California, USA",
      account_id: 1,
      status: "active",
      commissioned_date: "2023-06-15"
    },
    {
      id: "WIND-001", 
      name: "Wind Farm Beta",
      technology: "onshore_wind",
      capacity_mw: 75,
      location: "Texas, USA", 
      account_id: 1,
      status: "active",
      commissioned_date: "2023-08-20"
    },
    {
      id: "STORAGE-001",
      name: "Battery Storage Facility",
      technology: "lithium_ion",
      capacity_mw: 50,
      location: "Nevada, USA",
      account_id: 2,
      status: "active",
      commissioned_date: "2024-01-10"
    }
  ],

  accounts: [
    {
      id: 1,
      account_name: "Main Trading Account",
      certificates_count: 2,
      total_mwh: 1750.5,
      active_certificates: 1,
      transferred_certificates: 1,
      devices_count: 2
    },
    {
      id: 2,
      account_name: "Storage Account", 
      certificates_count: 1,
      total_mwh: 500.0,
      active_certificates: 0,
      transferred_certificates: 1,
      devices_count: 1
    }
  ],

  storageRecords: [
    {
      id: "SCR-001",
      device_id: "STORAGE-001",
      charge_start: "2024-01-15T10:00:00Z",
      charge_end: "2024-01-15T14:00:00Z", 
      energy_charged_kwh: 200000,
      allocated_certificates: ["GC-2024-000100", "GC-2024-000101"],
      status: "allocated"
    },
    {
      id: "SDR-001",
      device_id: "STORAGE-001",
      discharge_start: "2024-01-15T18:00:00Z",
      discharge_end: "2024-01-15T22:00:00Z",
      energy_discharged_kwh: 180000,
      storage_efficiency: 0.9,
      scr_reference: "SCR-001",
      status: "completed"
    }
  ]
};

// API Functions
export const mockLogin = (credentials) => {
  return Promise.resolve({
    data: {
      access_token: "demo_token_12345",
      token_type: "bearer", 
      user_id: 1
    }
  });
};

export const mockUserMe = () => {
  return Promise.resolve({ data: mockData.user });
};

export const mockCertificates = (params = {}) => {
  let certificates = [...mockData.certificates];
  
  // Apply filters
  if (params.source_type) {
    certificates = certificates.filter(c => c.source_type === params.source_type);
  }
  if (params.status) {
    certificates = certificates.filter(c => c.status === params.status);
  }
  if (params.device_id) {
    certificates = certificates.filter(c => c.device_id === params.device_id);
  }
  
  return Promise.resolve({ data: certificates });
};

export const mockHourlyData = (certificateId) => {
  const cert = mockData.certificates.find(c => c.id === certificateId);
  if (!cert) return Promise.resolve({ data: [] });
  
  const hourlyData = generateHourlyData(cert.total_mwh, 24); // Show 24 hours for demo
  return Promise.resolve({ data: hourlyData });
};

export const mockAccounts = () => {
  return Promise.resolve({ data: mockData.accounts });
};

export const mockDevices = () => {
  return Promise.resolve({ data: mockData.devices });
};

export const mockStorageRecords = () => {
  return Promise.resolve({ data: mockData.storageRecords });
};

export const mockTransferCertificate = (transferData) => {
  return Promise.resolve({
    data: {
      id: "TRANSFER-001",
      from_account: transferData.from_account,
      to_account: transferData.to_account,
      certificate_id: transferData.certificate_id,
      amount_mwh: transferData.amount_mwh,
      status: "completed",
      timestamp: new Date().toISOString()
    }
  });
};

export const mockCancelCertificate = (cancelData) => {
  return Promise.resolve({
    data: {
      id: "CANCEL-001", 
      certificate_id: cancelData.certificate_id,
      amount_mwh: cancelData.amount_mwh,
      reason: cancelData.reason,
      status: "cancelled",
      timestamp: new Date().toISOString()
    }
  });
};

export const mockCreateCertificate = (certData) => {
  return Promise.resolve({
    data: {
      id: `CERT-2024-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
      ...certData,
      status: "active",
      created_at: new Date().toISOString(),
      hourly_certificates: 8760
    }
  });
};