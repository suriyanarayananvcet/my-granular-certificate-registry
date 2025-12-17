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
    // Mock transfer success
    setShowTransferModal(false);
    alert('Certificate transferred successfully!');
    loadData();
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
                  <Progress percent={85} status="active" />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <p>Storage Efficiency</p>
                  <Progress percent={90} strokeColor="#52c41a" />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <p>Active Devices</p>
                  <Progress percent={100} strokeColor="#1890ff" />
                </div>
                <div>
                  <p>System Health</p>
                  <Progress percent={95} strokeColor="#722ed1" />
                </div>
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
          <Card
            title="Certificate Transfer & Trading"
            extra={
              <Button
                type="primary"
                onClick={() => setShowTransferModal(true)}
                disabled={!selectedCertificate}
              >
                Transfer Certificate
              </Button>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="Account Summary" size="small">
                  {accounts.map(account => (
                    <div key={account.id} style={{ marginBottom: '12px', padding: '8px', border: '1px solid #f0f0f0', borderRadius: '4px' }}>
                      <p><strong>{account.account_name}</strong></p>
                      <p>Certificates: {account.certificates_count} | Total: {account.total_mwh} MWh</p>
                    </div>
                  ))}
                </Card>
              </Col>
              <Col span={12}>
                <Card title="Recent Transactions" size="small">
                  <div style={{ padding: '8px' }}>
                    <p>✅ CERT-2024-001 → Transferred 100 MWh</p>
                    <p>🔄 CERT-2024-002 → Converted to GCs</p>
                    <p>❌ CERT-2024-003 → Cancelled 50 MWh</p>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="🔋 Storage Management" key="5">
          <Card title="Storage Device Operations">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="Storage Charge Records (SCR)" size="small">
                  {storageRecords.filter(r => r.id?.startsWith('SCR')).map(record => (
                    <div key={record.id} style={{ marginBottom: '12px', padding: '8px', border: '1px solid #e6f7ff', borderRadius: '4px' }}>
                      <p><strong>{record.id}</strong></p>
                      <p>Energy Charged: {(record.energy_charged_kwh / 1000).toFixed(1)} MWh</p>
                      <p>Status: <span style={{ color: 'green' }}>{record.status?.toUpperCase() || 'N/A'}</span></p>
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
                    </div>
                  ))}
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane tab="⚡ Device Management" key="6">
          <Card title="Registered Devices">
            <Row gutter={[16, 16]}>
              {devices.map(device => (
                <Col span={8} key={device.id}>
                  <Card size="small" title={device.name}>
                    <p><strong>ID:</strong> {device.id}</p>
                    <p><strong>Technology:</strong> {device.technology}</p>
                    <p><strong>Capacity:</strong> {device.capacity_mw} MW</p>
                    <p><strong>Location:</strong> {device.location}</p>
                    <p><strong>Status:</strong> <span style={{ color: 'green' }}>{device.status?.toUpperCase() || 'N/A'}</span></p>
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