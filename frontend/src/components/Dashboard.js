import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Button, Modal, Form, Input, Select, DatePicker, Statistic, Tabs, Progress } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { mockCertificates, mockUserMe, mockAccounts, mockDevices, mockStorageRecords } from '../api/completeMockAPI';

const { TabPane } = Tabs;
const { Option } = Select;

const Dashboard = () => {
  const [certificates, setCertificates] = useState([]);
  const [hourlyData, setHourlyData] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [storageRecords, setStorageRecords] = useState([]);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Use mock data directly
      const userRes = await mockUserMe();
      const user = userRes.data;
      setUserId(user.id);
      
      const accountsRes = await mockAccounts();
      setAccounts(accountsRes.data);
      
      const certsRes = await mockCertificates();
      setCertificates(certsRes.data);
      
      const devicesRes = await mockDevices();
      setDevices(devicesRes.data);
      
      const storageRes = await mockStorageRecords();
      setStorageRecords(storageRes.data);
      
      // Load hourly data for first certificate
      if (certsRes.data.length > 0) {
        handleCertificateSelect(certsRes.data[0]);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const handleCertificateSelect = async (certificate) => {
    setSelectedCertificate(certificate);
    // Generate mock hourly data for the selected certificate
    const mockHourlyData = Array.from({ length: 24 }, (_, hour) => ({
      id: `${certificate.id}-H${hour}`,
      hour,
      certificate_id: `GC-${certificate.id}-${String(hour).padStart(2, '0')}`,
      generation_kwh: Math.random() * 50 + 10,
      status: 'active'
    }));
    setHourlyData(mockHourlyData);
  };

  const handleTransfer = async (values) => {
    // Actually transfer the certificate
    const updatedCerts = certificates.map(cert => {
      if (cert.id === selectedCertificate.id) {
        const transferAmount = parseFloat(values.amount);
        if (transferAmount >= cert.total_mwh) {
          return { ...cert, status: 'transferred', total_mwh: 0 };
        } else {
          return { ...cert, total_mwh: cert.total_mwh - transferAmount };
        }
      }
      return cert;
    });
    
    setCertificates(updatedCerts);
    setShowTransferModal(false);
    alert(`Transferred ${values.amount} MWh successfully!`);
  };

  const handleCreateCertificate = async (values) => {
    // Create new certificate and add to list
    const newCert = {
      id: `CERT-${Date.now()}`,
      source_type: values.source_type,
      total_mwh: parseFloat(values.total_mwh),
      hourly_certificates: Math.floor(parseFloat(values.total_mwh) * 1000),
      status: 'active',
      device_name: devices.find(d => d.id === values.device_id)?.name || 'Unknown Device',
      device_id: values.device_id
    };
    
    setCertificates(prev => [...prev, newCert]);
    setShowCreateModal(false);
    alert('Certificate created successfully!');
  };

  const certificateColumns = [
    {
      title: 'Certificate ID',
      dataIndex: 'id',
      key: 'id',
      render: (text) => <Button type="link" onClick={() => handleCertificateSelect(certificates.find(c => c.id === text))}>{text}</Button>
    },
    {
      title: 'Energy Source',
      dataIndex: 'source_type',
      key: 'source_type',
      render: (text) => <span style={{ textTransform: 'capitalize' }}>{text}</span>
    },
    {
      title: 'Total MWh',
      dataIndex: 'total_mwh',
      key: 'total_mwh',
      render: (value) => `${value.toLocaleString()} MWh`
    },
    {
      title: 'Hourly Certificates',
      dataIndex: 'hourly_certificates',
      key: 'hourly_certificates',
      render: (value) => `${value.toLocaleString()} GCs`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <span style={{
          color: status === 'active' ? 'green' : status === 'transferred' ? 'blue' : 'orange',
          fontWeight: 'bold'
        }}>
          {status?.toUpperCase() || 'N/A'}
        </span>
      )
    },
    {
      title: 'Device',
      dataIndex: 'device_name',
      key: 'device_name'
    }
  ];

  const hourlyColumns = [
    {
      title: 'Hour',
      dataIndex: 'hour',
      key: 'hour',
      render: (hour) => `${String(hour).padStart(2, '0')}:00`
    },
    {
      title: 'GC ID',
      dataIndex: 'certificate_id',
      key: 'certificate_id'
    },
    {
      title: 'Generation (kWh)',
      dataIndex: 'generation_kwh',
      key: 'generation_kwh',
      render: (value) => `${value.toFixed(3)} kWh`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <span style={{ color: 'green', fontWeight: 'bold' }}>{status?.toUpperCase() || 'N/A'}</span>
    }
  ];

  const totalMWh = certificates.reduce((sum, cert) => sum + cert.total_mwh, 0);
  const totalGCs = certificates.reduce((sum, cert) => sum + cert.hourly_certificates, 0);
  const activeCertificates = certificates.filter(c => c.status === 'active').length;

  const sourceDistribution = certificates.reduce((acc, cert) => {
    acc[cert.source_type] = (acc[cert.source_type] || 0) + cert.total_mwh;
    return acc;
  }, {});

  const pieData = Object.entries(sourceDistribution).map(([source, mwh]) => ({
    name: source,
    value: mwh,
    color: source === 'solar' ? '#ffd700' : source === 'wind' ? '#87ceeb' : '#90ee90'
  }));

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Energy Certificates"
              value={certificates.length}
              suffix="EACs"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Energy"
              value={totalMWh.toFixed(1)}
              suffix="MWh"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Granular Certificates"
              value={totalGCs.toLocaleString()}
              suffix="GCs"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Certificates"
              value={activeCertificates}
              suffix={`/ ${certificates.length}`}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="1">
        <TabPane tab="📊 Dashboard Overview" key="1">
          <Row gutter={[16, 16]}>
            <Col span={16}>
              <Card title="Energy Source Distribution" style={{ height: '400px' }}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value} MWh`}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={8}>
              <Card title="System Status" style={{ height: '400px' }}>
                <div style={{ marginBottom: '20px' }}>
                  <p>Certificate Conversion Rate</p>
                  <Progress percent={certificates.length > 0 ? Math.round((certificates.filter(c => c.hourly_certificates > 0).length / certificates.length) * 100) : 0} status="active" />
                  <small>{certificates.filter(c => c.hourly_certificates > 0).length} of {certificates.length} converted</small>
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <p>Storage Efficiency</p>
                  <Progress percent={storageRecords.length > 0 ? Math.round(storageRecords.reduce((avg, r) => avg + (r.storage_efficiency || 0.9), 0) / storageRecords.length * 100) : 90} strokeColor="#52c41a" />
                  <small>{storageRecords.length} storage operations</small>
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <p>Active Devices</p>
                  <Progress percent={devices.length > 0 ? Math.round((devices.filter(d => d.status === 'active').length / devices.length) * 100) : 0} strokeColor="#1890ff" />
                  <small>{devices.filter(d => d.status === 'active').length} of {devices.length} active</small>
                </div>
                <div>
                  <p>System Health</p>
                  <Progress percent={certificates.length > 0 && devices.length > 0 ? Math.round(((certificates.filter(c => c.status === 'active').length / certificates.length) + (devices.filter(d => d.status === 'active').length / devices.length)) / 2 * 100) : 95} strokeColor="#722ed1" />
                  <small>Overall system performance</small>
                </div>
              </Card>
            </Col>
          </Row>
          <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
            <Col span={24}>
              <Card title="Quick Actions">
                <Row gutter={[16, 16]}>
                  <Col span={6}>
                    <Button 
                      type="primary" 
                      block 
                      size="large"
                      onClick={() => setShowCreateModal(true)}
                    >
                      Create Certificate
                    </Button>
                  </Col>
                  <Col span={6}>
                    <Button 
                      block 
                      size="large"
                      onClick={() => {
                        const activeCerts = certificates.filter(c => c.status === 'active');
                        if (activeCerts.length > 0) {
                          setSelectedCertificate(activeCerts[0]);
                          setShowTransferModal(true);
                        } else {
                          alert('No active certificates to transfer');
                        }
                      }}
                    >
                      Transfer Certificate
                    </Button>
                  </Col>
                  <Col span={6}>
                    <Button 
                      block 
                      size="large"
                      onClick={() => {
                        const newDevice = {
                          id: `DEV-${Date.now()}`,
                          name: `Device ${devices.length + 1}`,
                          technology: ['solar', 'wind', 'hydro'][Math.floor(Math.random() * 3)],
                          capacity_mw: Math.floor(Math.random() * 100) + 10,
                          location: `Location ${devices.length + 1}`,
                          status: 'active'
                        };
                        setDevices(prev => [...prev, newDevice]);
                        alert('New device registered!');
                      }}
                    >
                      Add Device
                    </Button>
                  </Col>
                  <Col span={6}>
                    <Button 
                      block 
                      size="large"
                      onClick={() => {
                        loadData();
                        alert('Data refreshed!');
                      }}
                    >
                      Refresh Data
                    </Button>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="📋 Certificate Management" key="2">
          <Card
            title="Energy Attribute Certificates (EACs)"
            extra={
              <Button type="primary" onClick={() => setShowCreateModal(true)}>
                Create New Certificate
              </Button>
            }
          >
            <Table
              columns={certificateColumns}
              dataSource={certificates}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="⏰ Hourly Granular Certificates" key="3">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title={`Hourly Generation Data - ${selectedCertificate?.id || 'Select a Certificate'}`}>
                {selectedCertificate && (
                  <div style={{ marginBottom: '16px' }}>
                    <p><strong>Certificate:</strong> {selectedCertificate.id}</p>
                    <p><strong>Total Energy:</strong> {selectedCertificate.total_mwh} MWh → {selectedCertificate.hourly_certificates.toLocaleString()} Hourly GCs</p>
                    <p><strong>Source:</strong> {selectedCertificate.source_type} ({selectedCertificate.device_name})</p>
                  </div>
                )}
              </Card>
            </Col>
            <Col span={24}>
              <Card title="24-Hour Generation Profile">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="hour" />
                    <YAxis />
                    <Tooltip formatter={(value) => [`${value.toFixed(3)} kWh`, 'Generation']} />
                    <Line type="monotone" dataKey="generation_kwh" stroke="#8884d8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={24}>
              <Card title="Hourly Certificate Details">
                <Table
                  columns={hourlyColumns}
                  dataSource={hourlyData}
                  rowKey="id"
                  pagination={{ pageSize: 12 }}
                  size="small"
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="🔄 Certificate Trading" key="4">
          <Card title="Certificate Transfer & Trading">
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title="Select Certificate to Trade" size="small">
                  <Table
                    columns={[
                      { title: 'ID', dataIndex: 'id', key: 'id' },
                      { title: 'Type', dataIndex: 'source_type', key: 'source_type' },
                      { title: 'Amount', dataIndex: 'total_mwh', key: 'total_mwh', render: (val) => `${val} MWh` },
                      { title: 'Status', dataIndex: 'status', key: 'status' },
                      {
                        title: 'Actions',
                        key: 'actions',
                        render: (_, cert) => (
                          <div>
                            <Button 
                              size="small" 
                              onClick={() => { setSelectedCertificate(cert); setShowTransferModal(true); }}
                              disabled={cert.status !== 'active'}
                            >
                              Transfer
                            </Button>
                            <Button 
                              size="small" 
                              danger 
                              style={{ marginLeft: '8px' }}
                              onClick={() => {
                                setCertificates(prev => prev.map(c => 
                                  c.id === cert.id ? { ...c, status: 'cancelled' } : c
                                ));
                                alert('Certificate cancelled!');
                              }}
                              disabled={cert.status !== 'active'}
                            >
                              Cancel
                            </Button>
                          </div>
                        )
                      }
                    ]}
                    dataSource={certificates}
                    rowKey="id"
                    size="small"
                    pagination={{ pageSize: 5 }}
                  />
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="🔋 Storage Management" key="5">
          <Card title="Storage Device Operations">
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title="Storage Operations Control" size="small">
                  <Row gutter={[16, 16]}>
                    <Col span={8}>
                      <Button 
                        type="primary" 
                        block
                        onClick={() => {
                          const newRecord = {
                            id: `SCR-${Date.now()}`,
                            energy_charged_kwh: Math.random() * 1000 + 500,
                            status: 'active'
                          };
                          setStorageRecords(prev => [...prev, newRecord]);
                          alert('Storage charge initiated!');
                        }}
                      >
                        Start Charging
                      </Button>
                    </Col>
                    <Col span={8}>
                      <Button 
                        block
                        onClick={() => {
                          const newRecord = {
                            id: `SDR-${Date.now()}`,
                            energy_discharged_kwh: Math.random() * 800 + 400,
                            storage_efficiency: 0.85 + Math.random() * 0.1,
                            status: 'active'
                          };
                          setStorageRecords(prev => [...prev, newRecord]);
                          alert('Storage discharge initiated!');
                        }}
                      >
                        Start Discharging
                      </Button>
                    </Col>
                    <Col span={8}>
                      <Button 
                        danger
                        block
                        onClick={() => {
                          setStorageRecords([]);
                          alert('All storage records cleared!');
                        }}
                      >
                        Clear Records
                      </Button>
                    </Col>
                  </Row>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Storage Charge Records (SCR)" size="small">
                  {storageRecords.filter(r => r.id?.startsWith('SCR')).map(record => (
                    <div key={record.id} style={{ marginBottom: '12px', padding: '8px', border: '1px solid #e6f7ff', borderRadius: '4px' }}>
                      <p><strong>{record.id}</strong></p>
                      <p>Energy Charged: {(record.energy_charged_kwh / 1000).toFixed(1)} MWh</p>
                      <p>Status: <span style={{ color: 'green' }}>{record.status?.toUpperCase() || 'N/A'}</span></p>
                      <Button 
                        size="small" 
                        danger
                        onClick={() => {
                          setStorageRecords(prev => prev.filter(r => r.id !== record.id));
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Storage Discharge Records (SDR)" size="small">
                  {storageRecords.filter(r => r.id?.startsWith('SDR')).map(record => (
                    <div key={record.id} style={{ marginBottom: '12px', padding: '8px', border: '1px solid #f6ffed', borderRadius: '4px' }}>
                      <p><strong>{record.id}</strong></p>
                      <p>Energy Discharged: {(record.energy_discharged_kwh / 1000).toFixed(1)} MWh</p>
                      <p>Efficiency: {(record.storage_efficiency * 100).toFixed(1)}%</p>
                      <p>Status: <span style={{ color: 'green' }}>{record.status?.toUpperCase() || 'N/A'}</span></p>
                      <Button 
                        size="small" 
                        danger
                        onClick={() => {
                          setStorageRecords(prev => prev.filter(r => r.id !== record.id));
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="⚡ Device Management" key="6">
          <Card 
            title="Registered Devices"
            extra={
              <Button 
                type="primary"
                onClick={() => {
                  const newDevice = {
                    id: `DEV-${Date.now()}`,
                    name: `Device ${devices.length + 1}`,
                    technology: ['solar', 'wind', 'hydro'][Math.floor(Math.random() * 3)],
                    capacity_mw: Math.floor(Math.random() * 100) + 10,
                    location: `Location ${devices.length + 1}`,
                    status: 'active'
                  };
                  setDevices(prev => [...prev, newDevice]);
                  alert('New device registered!');
                }}
              >
                Add Device
              </Button>
            }
          >
            <Row gutter={[16, 16]}>
              {devices.map(device => (
                <Col span={8} key={device.id}>
                  <Card size="small" title={device.name}>
                    <p><strong>ID:</strong> {device.id}</p>
                    <p><strong>Technology:</strong> {device.technology}</p>
                    <p><strong>Capacity:</strong> {device.capacity_mw} MW</p>
                    <p><strong>Location:</strong> {device.location}</p>
                    <p><strong>Status:</strong> <span style={{ color: device.status === 'active' ? 'green' : 'red' }}>{device.status?.toUpperCase() || 'N/A'}</span></p>
                    <div style={{ marginTop: '8px' }}>
                      <Button 
                        size="small"
                        onClick={() => {
                          setDevices(prev => prev.map(d => 
                            d.id === device.id 
                              ? { ...d, status: d.status === 'active' ? 'inactive' : 'active' }
                              : d
                          ));
                        }}
                      >
                        Toggle Status
                      </Button>
                      <Button 
                        size="small" 
                        danger
                        style={{ marginLeft: '8px' }}
                        onClick={() => {
                          setDevices(prev => prev.filter(d => d.id !== device.id));
                          alert('Device removed!');
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </TabPane>
      </Tabs>

      {/* Transfer Modal */}
      <Modal
        title="Transfer Certificate"
        open={showTransferModal}
        onCancel={() => setShowTransferModal(false)}
        footer={null}
      >
        <Form onFinish={handleTransfer}>
          <Form.Item label="Certificate" name="certificate">
            <Input value={selectedCertificate?.id} disabled />
          </Form.Item>
          <Form.Item label="To Account" name="to_account" rules={[{ required: true }]}>
            <Select>
              {accounts.map(account => (
                <Option key={account.id} value={account.id}>{account.account_name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="Amount (MWh)" name="amount" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">Transfer</Button>
          </Form.Item>
        </Form>
      </Modal>

      {/* Create Certificate Modal */}
      <Modal
        title="Create New Certificate"
        open={showCreateModal}
        onCancel={() => setShowCreateModal(false)}
        footer={null}
      >
        <Form onFinish={handleCreateCertificate}>
          <Form.Item label="Total MWh" name="total_mwh" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item label="Energy Source" name="source_type" rules={[{ required: true }]}>
            <Select>
              <Option value="solar">Solar</Option>
              <Option value="wind">Wind</Option>
              <Option value="hydro">Hydro</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Device ID" name="device_id" rules={[{ required: true }]}>
            <Select>
              {devices.map(device => (
                <Option key={device.id} value={device.id}>{device.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">Create Certificate</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;