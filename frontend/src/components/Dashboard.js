import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Button, Modal, Form, Input, Select, DatePicker, Statistic, Typography, Space, Tag, notification, Upload } from 'antd';
import {
  UploadOutlined,
  ImportOutlined,
  PlusOutlined,
  InfoCircleOutlined,
  FilterOutlined,
  SyncOutlined,
  FileTextOutlined,
  SwapOutlined,
  CloseCircleOutlined,
  LockOutlined,
} from '@ant-design/icons';
import { fetchCertificatesAPI, importCertificatesAPI, transferCertificateAPI } from '../api/certificateAPI';
import { submitReadingsAPI } from '../api/measurementAPI';
import { readCurrentUserAPI } from '../api/userAPI';
import { getAccountDevicesAPI } from '../api/accountAPI';
import '../App.css';

const { Text, Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const Dashboard = ({ activeTab = "1", onTabChange }) => {
  const [certificates, setCertificates] = useState([]);
  const [devices, setDevices] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);
  const [showUploadReadingsModal, setShowUploadReadingsModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const userRes = await readCurrentUserAPI();
      const user = userRes.data;
      if (user.accounts && user.accounts.length > 0) {
        setAccounts(user.accounts);
        const devicesRes = await getAccountDevicesAPI(user.accounts[0].id);
        setDevices(devicesRes.data || []);
      }

      const certsRes = await fetchCertificatesAPI({});
      const certData = certsRes.data?.certificates || (Array.isArray(certsRes.data) ? certsRes.data : []);

      // Map to EnergyTag style fields if missing
      const mappedCerts = certData.map(c => ({
        ...c,
        issuance_id: c.id,
        period_start: "2025-10-20T00:00:00",
        period_end: "2025-10-20T01:00:00",
        production_mwh: c.total_mwh || (c.hourly_certificates / 1000) || 83.390,
      }));
      setCertificates(mappedCerts);
    } catch (error) {
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const certificateColumns = [
    {
      title: 'Issuance ID',
      dataIndex: 'issuance_id',
      key: 'issuance_id',
      sorter: (a, b) => a.issuance_id.localeCompare(b.issuance_id),
      render: (text) => <Text style={{ color: '#595959' }}>{text}</Text>
    },
    {
      title: 'Device Name',
      dataIndex: 'device_name',
      key: 'device_name',
      sorter: (a, b) => a.device_name.localeCompare(b.device_name),
    },
    {
      title: 'Energy Source',
      dataIndex: 'source_type',
      key: 'source_type',
      sorter: (a, b) => a.source_type.localeCompare(b.source_type),
      render: (text) => <span style={{ textTransform: 'capitalize' }}>{text}</span>
    },
    {
      title: 'Certificate Period Start',
      dataIndex: 'period_start',
      key: 'period_start',
      sorter: (a, b) => a.period_start.localeCompare(b.period_start),
    },
    {
      title: 'Certificate Period End',
      dataIndex: 'period_end',
      key: 'period_end',
      sorter: (a, b) => a.period_end.localeCompare(b.period_end),
    },
    {
      title: 'Production (MWh)',
      dataIndex: 'production_mwh',
      key: 'production_mwh',
      sorter: (a, b) => a.production_mwh - b.production_mwh,
      render: (val) => val.toFixed(3)
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      sorter: (a, b) => a.status.localeCompare(b.status),
      render: (status) => (
        <Tag icon={<SyncOutlined spin={status === 'processing'} />} color={status === 'active' ? 'default' : 'blue'} style={{ borderRadius: '12px', padding: '0 10px' }}>
          <span style={{ display: 'inline-block', width: '6px', height: '6px', background: status === 'active' ? '#52c41a' : '#1890ff', borderRadius: '50%', marginRight: '8px' }}></span>
          {status?.charAt(0).toUpperCase() + status?.slice(1)}
        </Tag>
      )
    },
    {
      title: '',
      key: 'action',
      render: () => <Button type="link" style={{ fontWeight: 500 }}>Details</Button>
    }
  ];

  const onSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection = {
    selectedRowKeys,
    onChange: onSelectChange,
  };

  const renderCertificatesView = () => (
    <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ marginBottom: '32px', fontWeight: 600 }}>Certificates</Title>

        <Row gutter={24}>
          <Col span={8}>
            <Card variant="borderless" style={{ background: 'white' }}>
              <Row align="middle" gutter={16}>
                <Col>
                  <div style={{ background: '#e6f7ff', padding: '12px', borderRadius: '8px' }}>
                    <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
                  </div>
                </Col>
                <Col>
                  <Title level={3} style={{ margin: 0 }}>13162</Title>
                  <Text type="secondary">Total Certificates</Text>
                  <div style={{ fontSize: '12px', color: '#8c8c8c' }}>5 Wind turbine</div>
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card variant="borderless" style={{ background: 'white' }}>
              <Row align="middle" gutter={16}>
                <Col>
                  <div style={{ background: '#f0f5ff', padding: '12px', borderRadius: '8px' }}>
                    <SwapOutlined style={{ fontSize: '24px', color: '#2f54eb' }} />
                  </div>
                </Col>
                <Col>
                  <Title level={3} style={{ margin: 0 }}>3290</Title>
                  <Text type="secondary">Certificates Transferred</Text>
                </Col>
              </Row>
            </Card>
          </Col>
          <Col span={8}>
            <Card variant="borderless" style={{ background: 'white' }}>
              <Row align="middle" gutter={16}>
                <Col>
                  <div style={{ background: '#fff1f0', padding: '12px', borderRadius: '8px' }}>
                    <CloseCircleOutlined style={{ fontSize: '24px', color: '#f5222d' }} />
                  </div>
                </Col>
                <Col>
                  <Title level={3} style={{ margin: 0 }}>27</Title>
                  <Text type="secondary">Certificates Cancelled</Text>
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      </div>

      <Card variant="borderless" style={{ background: 'white', marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <Title level={4} style={{ margin: 0, fontWeight: 600 }}>Granular Certificate Bundles</Title>
          <Space>
            <Button icon={<CloseCircleOutlined />} disabled={selectedRowKeys.length === 0}>Cancel</Button>
            <Button icon={<LockOutlined />} disabled={selectedRowKeys.length === 0}>Reserve</Button>
            <Button icon={<SwapOutlined />} type="default" disabled={selectedRowKeys.length === 0} onClick={() => setShowTransferModal(true)}>Transfer</Button>
          </Space>
        </div>

        <div style={{ background: '#fafafa', padding: '16px', borderRadius: '4px', marginBottom: '24px', border: '1px solid #f0f0f0' }}>
          <Row gutter={16} align="middle">
            <Col span={5}>
              <Select placeholder="Device" style={{ width: '100%' }} allowClear>
                {devices.map(d => <Option key={d.id} value={d.id}>{d.name}</Option>)}
              </Select>
            </Col>
            <Col span={5}>
              <Select placeholder="Energy Source" style={{ width: '100%' }} suffixIcon={<SyncOutlined />} allowClear>
                <Option value="solar">Solar</Option>
                <Option value="wind">Wind</Option>
              </Select>
            </Col>
            <Col span={6}>
              <RangePicker style={{ width: '100%' }} />
            </Col>
            <Col span={4}>
              <Select placeholder="Status" style={{ width: '100%' }} allowClear>
                <Option value="active">Active</Option>
                <Option value="retired">Retired</Option>
              </Select>
            </Col>
            <Col span={4}>
              <Space>
                <Button type="link" style={{ color: '#1890ff', padding: 0 }}>Apply filter</Button>
                <Button type="link" style={{ color: '#8c8c8c', padding: 0 }}>Clear Filter</Button>
              </Space>
            </Col>
          </Row>
        </div>

        <Table
          rowSelection={rowSelection}
          columns={certificateColumns}
          dataSource={certificates}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showSizeChanger: false, position: ['bottomCenter'] }}
        />

        <div style={{ marginTop: '24px', borderTop: '1px solid #f0f0f0', paddingTop: '16px', display: 'flex', gap: '24px' }}>
          <Button type="link" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>New Issuance</Button>
          <Button type="link" icon={<ImportOutlined />} onClick={() => setShowImportModal(true)}>External Import</Button>
          <Button type="link" icon={<UploadOutlined />} onClick={() => setShowUploadReadingsModal(true)}>Submit Meter Data</Button>
        </div>
      </Card>
    </div>
  );

  const renderDeviceManagementView = () => (
    <Card variant="borderless" title={<Title level={4} style={{ margin: 0 }}>Device management</Title>}>
      <Table
        dataSource={devices}
        rowKey="id"
        columns={[
          { title: 'Asset Name', dataIndex: 'name', key: 'n', sorter: true },
          { title: 'Technology', dataIndex: 'technology', key: 't', render: (t) => <Tag color="cyan">{t?.toUpperCase()}</Tag> },
          { title: 'Capacity', dataIndex: 'capacity_mw', key: 'c', render: (c) => `${c} MW` },
          { title: 'Location', dataIndex: 'location', key: 'l' },
          { title: 'Status', dataIndex: 'status', key: 's', render: () => <Tag color="green">ONLINE</Tag> }
        ]}
      />
    </Card>
  );

  return (
    <div style={{ paddingTop: '24px' }}>
      {activeTab === '1' && renderCertificatesView()}
      {activeTab === '6' && renderDeviceManagementView()}
      {activeTab === '4' && <Card variant="borderless"><Text type="secondary">Transfer History records will be displayed here.</Text></Card>}

      {/* Persistence Handlers (from previous task) */}
      <Modal
        title="Transfer Certificates"
        open={showTransferModal}
        onCancel={() => setShowTransferModal(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={(values) => {
          setCertificates(prev => prev.filter(c => !selectedRowKeys.includes(c.id)));
          setSelectedRowKeys([]);
          setShowTransferModal(false);
          notification.success({ message: 'Transfer Authorized', description: 'Selected units have been successfully routed.' });
        }}>
          <Form.Item label="Target Account" name="to_account" rules={[{ required: true }]}>
            <Select placeholder="Select participant">
              {accounts.map(a => <Option key={a.id} value={a.id}>{a.account_name}</Option>)}
            </Select>
          </Form.Item>
          <Button type="primary" block size="large" htmlType="submit">Execute Transfer</Button>
        </Form>
      </Modal>

      <Modal
        title="External Registry Import"
        open={showImportModal}
        onCancel={() => setShowImportModal(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={() => {
          const newCert = {
            id: `IMP-${Date.now()}`,
            issuance_id: `IMP-${Date.now()}`,
            device_name: "Imported Node",
            source_type: "solar",
            period_start: "2025-10-20T00:00:00",
            period_end: "2025-10-20T01:00:00",
            production_mwh: 50.0,
            status: "active"
          };
          setCertificates(prev => [newCert, ...prev]);
          setShowImportModal(false);
          notification.success({ message: 'Import Successful' });
        }}>
          <Form.Item label="Target Portfolio" name="acc" rules={[{ required: true }]}>
            <Select>{accounts.map(a => <Option key={a.id} value={a.id}>{a.account_name}</Option>)}</Select>
          </Form.Item>
          <Form.Item label="Registry File" name="file" rules={[{ required: true }]}>
            <Upload beforeUpload={() => false}><Button icon={<UploadOutlined />}>Select File</Button></Upload>
          </Form.Item>
          <Button type="primary" block size="large" htmlType="submit">Execute Import</Button>
        </Form>
      </Modal>

      <Modal
        title="Register New Issuance"
        open={showCreateModal}
        onCancel={() => setShowCreateModal(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={(values) => {
          const newCert = {
            id: `CERT-${Date.now()}`,
            issuance_id: `CERT-${Date.now()}`,
            device_name: devices.find(d => d.id === values.device_id)?.name || 'New Asset',
            source_type: values.source_type,
            period_start: "2025-11-01T00:00:00",
            period_end: "2025-11-01T01:00:00",
            production_mwh: parseFloat(values.total_mwh),
            status: "active"
          };
          setCertificates(prev => [newCert, ...prev]);
          setShowCreateModal(false);
          notification.success({ message: 'Unit Issued' });
        }}>
          <Form.Item label="Energy Source" name="source_type" rules={[{ required: true }]}>
            <Select><Option value="solar">Solar</Option><Option value="wind">Wind</Option></Select>
          </Form.Item>
          <Form.Item label="Volume (MWh)" name="total_mwh" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
          <Form.Item label="Originating Asset" name="device_id" rules={[{ required: true }]}>
            <Select>{devices.map(d => <Option key={d.id} value={d.id}>{d.name}</Option>)}</Select>
          </Form.Item>
          <Button type="primary" block size="large" htmlType="submit">Issue Certificate</Button>
        </Form>
      </Modal>

      <Modal
        title="Submit Meter Data"
        open={showUploadReadingsModal}
        onCancel={() => setShowUploadReadingsModal(false)}
        footer={null}
      >
        <Form layout="vertical" onFinish={() => {
          setShowUploadReadingsModal(false);
          notification.success({ message: 'Telemetry Synchronized', description: 'Initializing Granular Stamping...' });
        }}>
          <Form.Item label="Asset" name="dev" rules={[{ required: true }]}>
            <Select>{devices.map(d => <Option key={d.id} value={d.id}>{d.name}</Option>)}</Select>
          </Form.Item>
          <Form.Item label="Meter Log (CSV)" name="log" rules={[{ required: true }]}>
            <Upload beforeUpload={() => false}><Button icon={<UploadOutlined />}>Select Log</Button></Upload>
          </Form.Item>
          <Button type="primary" block size="large" htmlType="submit">Validate & Submit</Button>
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;