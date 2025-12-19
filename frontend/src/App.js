import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  SwapOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons';
import Dashboard from './components/Dashboard';
import { mockUserMe } from './api/completeMockAPI';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: 'admin@registry.com', password: 'admin123' });

  useEffect(() => {
    // Check if user is logged in
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
      console.error('Failed to load user:', error);
      // Fallback to demo user
      setUser({
        id: 1,
        name: "Admin User",
        email: "admin@registry.com",
        role: 4,
        organisation: "Demo Organization"
      });
      setIsLoggedIn(true);
    }
  };

  const handleLogin = (e) => {
    e.preventDefault();

    // Direct demo login - no API calls
    localStorage.setItem('access_token', 'demo_token_12345');
    setIsLoggedIn(true);
    setUser({
      id: 1,
      name: "Admin User",
      email: "admin@registry.com",
      role: 4,
      organisation: "Demo Organization",
      accounts: [
        { id: 1, account_name: "Main Trading Account", user_ids: [1] },
        { id: 2, account_name: "Storage Account", user_ids: [1] }
      ]
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    setIsLoggedIn(false);
  };

  const [activeTab, setActiveTab] = useState('1');

  const handleMenuClick = ({ key }) => {
    const keyMap = {
      'dashboard': '1',
      'certificates': '2',
      'hourly': '3',
      'trading': '4',
      'storage': '5',
      'devices': '6'
    };
    setActiveTab(keyMap[key]);
  };

  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  const userMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<UserOutlined />}>
        Profile
      </Menu.Item>
      <Menu.Item key="settings" icon={<SettingOutlined />}>
        Settings
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogoutOutlined />} onClick={handleLogout}>
        Logout
      </Menu.Item>
    </Menu>
  );

  if (!isLoggedIn) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #a8e6cf 0%, #dcedc1 50%, #ffd3a5 100%)'
      }}>
        <div style={{
          background: 'white',
          padding: '40px',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          width: '400px'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <Title level={2} style={{ color: '#2d5016', marginBottom: '8px' }}>
              🏔️ Mt.Stonegate
            </Title>
            <p style={{ color: '#4a7c59', fontSize: '16px', fontWeight: '500' }}>
              Renewable Energy Registry
            </p>
          </div>

          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Email Address
              </label>
              <input
                type="email"
                value={loginForm.email}
                onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '16px'
                }}
                placeholder="Enter your email"
              />
            </div>

            <div style={{ marginBottom: '30px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                Password
              </label>
              <input
                type="password"
                value={loginForm.password}
                onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '6px',
                  fontSize: '16px'
                }}
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              style={{
                width: '100%',
                padding: '12px',
                background: 'linear-gradient(135deg, #2d5016 0%, #4a7c59 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              Login to Registry
            </button>
          </form>

          <div style={{ marginTop: '20px', padding: '16px', background: '#f6ffed', borderRadius: '6px' }}>
            <p style={{ margin: 0, fontSize: '14px', color: '#52c41a' }}>
              <strong>Demo Credentials:</strong><br />
              Email: admin@registry.com<br />
              Password: admin123
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f0fff0 0%, #e8f5e8 100%)' }}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{ background: 'linear-gradient(180deg, #2d5016 0%, #1a3009 100%)' }}
      >
        <div style={{
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '18px',
          fontWeight: 'bold'
        }}>
          {collapsed ? '🏔️' : '🏔️ Mt.Stonegate'}
        </div>

        <Menu theme="dark" defaultSelectedKeys={['dashboard']} mode="inline" onClick={handleMenuClick}>
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
            Dashboard
          </Menu.Item>
          <Menu.Item key="certificates" icon={<FileTextOutlined />}>
            Certificates
          </Menu.Item>
          <Menu.Item key="hourly" icon={<ClockCircleOutlined />}>
            Hourly GCs
          </Menu.Item>
          <Menu.Item key="trading" icon={<SwapOutlined />}>
            Trading
          </Menu.Item>
          <Menu.Item key="storage" icon={<ThunderboltOutlined />}>
            Storage
          </Menu.Item>
          <Menu.Item key="devices" icon={<SettingOutlined />}>
            Devices
          </Menu.Item>
        </Menu>
      </Sider>

      <Layout>
        <Header style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #f0fff0 100%)',
          padding: '0 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(45, 80, 22, 0.1)',
          borderBottom: '2px solid #e8f5e8'
        }}>
          <Title level={3} style={{ margin: 0, color: '#2d5016' }}>
            Mt.Stonegate - Renewable Energy Registry
          </Title>

          <Space>
            <span style={{ color: '#666' }}>Welcome back,</span>
            <Dropdown overlay={userMenu} placement="bottomRight">
              <Button type="text" style={{ display: 'flex', alignItems: 'center' }}>
                <Avatar icon={<UserOutlined />} style={{ marginRight: '8px' }} />
                {user?.name}
              </Button>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ margin: '0', background: 'linear-gradient(135deg, #f0fff0 0%, #e8f5e8 100%)' }}
          <Dashboard activeTab={activeTab} onTabChange={handleTabChange} />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;