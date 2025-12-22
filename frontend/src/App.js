import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, Breadcrumb, Form, Input } from 'antd';
import {
  DashboardOutlined,
  FileProtectOutlined,
  SwapOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import Dashboard from './components/Dashboard';
import { mockUserMe } from './api/completeMockAPI';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: 'admin@registry.com', password: 'admin123' });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      loadUser();
    }
  }, []);

  const loadUser = async () => {
    try {
      const response = await mockUserMe();
      setUser(response.data);
      setIsLoggedIn(true);
    } catch (error) {
      setUser({
        id: 1,
        name: "Admin Director",
        email: "admin@registry.com",
        role: 4,
        organisation: "Mt. Stonegate Environmental"
      });
      setIsLoggedIn(true);
    }
  };

  const handleLogin = (values) => {
    // Check demo credentials
    if (values.email === 'admin@registry.com' && values.password === 'admin123') {
      localStorage.setItem('access_token', 'demo_token_12345');
      setIsLoggedIn(true);
      setUser({
        id: 1,
        name: "Admin Director",
        email: "admin@registry.com",
        role: 4,
        organisation: "Mt. Stonegate Environmental",
        accounts: [
          { id: 1, account_name: "Asset Portfolio A", user_ids: [1] },
          { id: 2, account_name: "Strategic Reserve", user_ids: [1] }
        ]
      });
    } else {
      alert('Invalid credentials. Use admin@registry.com / admin123');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    setIsLoggedIn(false);
  };

  const [activeTab, setActiveTab] = useState('1'); // Match EnergyTag: Certificates is key 1

  const handleMenuClick = ({ key }) => {
    setActiveTab(key);
  };

  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: 'User Profile' },
    { type: 'divider' },
    { key: 'logout', icon: <LogoutOutlined />, label: 'Sign Out', onClick: handleLogout },
  ];

  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <div className="login-form-side">
          <div className="login-content-box">
            <div style={{ marginBottom: '40px' }}>
              <Title level={2} style={{ margin: 0, fontWeight: 600 }}>Login to Account</Title>
              <Text type="secondary">Please enter your email and password to continue</Text>
            </div>

            <Form layout="vertical" onFinish={handleLogin}>
              <Form.Item label="Email" name="email" initialValue={loginForm.email}>
                <Input size="large" />
              </Form.Item>
              <Form.Item
                label={
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                    <span>Password</span>
                    <a href="#forgot" style={{ fontSize: '12px' }}>Forgot password</a>
                  </div>
                }
                name="password"
                initialValue={loginForm.password}
              >
                <Input.Password size="large" />
              </Form.Item>

              <Button type="primary" size="large" block htmlType="submit" style={{ height: '48px', marginTop: '12px' }}>
                Login
              </Button>
            </Form>

            <div style={{ marginTop: '32px', textAlign: 'center' }}>
              <Text type="secondary">Don't have an account? <a href="#request">Request account</a></Text>
            </div>

            <div style={{ marginTop: '80px', fontSize: '11px', color: '#8c8c8c' }}>
              Made by Future Energy Associates Ltd. in partnership with: Private Energy Partners, Google and EnergyTag.
            </div>
          </div>
        </div>
        <div className="login-visual-side">
          <div style={{ position: 'absolute', top: '40px', right: '40px', textAlign: 'right', color: 'white' }}>
            <Title level={3} style={{ color: 'white', margin: 0, letterSpacing: '1px' }}>Granular CertOS</Title>
          </div>
          {/* Visual abstract blobs handled in CSS via radial gradients */}
        </div>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={240}
        theme="light"
      >
        <div style={{
          height: '80px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 24px',
          color: '#1890ff',
        }}>
          {!collapsed && <span style={{ fontWeight: 700, fontSize: '18px' }}>Granular CertOS</span>}
          {collapsed && <span style={{ fontWeight: 700, fontSize: '14px' }}>GC</span>}
        </div>

        <Menu
          theme="light"
          selectedKeys={[activeTab]}
          mode="inline"
          onClick={handleMenuClick}
          items={[
            { key: '6', icon: <SettingOutlined />, label: 'Device management' },
            { key: '1', icon: <FileProtectOutlined />, label: 'Certificates' },
            { key: '4', icon: <SwapOutlined />, label: 'Transfer History', disabled: true },
          ]}
        />
      </Sider>

      <Layout style={{ background: '#f5f7fa' }}>
        <Header style={{
          background: 'transparent',
          padding: '0 40px',
          display: 'flex',
          justifyContent: 'flex-end',
          alignItems: 'center',
          height: '64px'
        }}>
          <Space size="large">
            <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', lineHeight: '1' }}>
              <Text strong style={{ fontSize: '13px' }}>{user?.name}</Text>
              <Text type="secondary" style={{ fontSize: '11px' }}>{user?.organisation}</Text>
            </div>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar
                icon={<UserOutlined />}
                style={{ backgroundColor: '#f0f0f0', color: '#8c8c8c', cursor: 'pointer' }}
              />
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ padding: '0 40px 40px 40px' }}>
          <Dashboard activeTab={activeTab} onTabChange={handleTabChange} />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;