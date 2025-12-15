import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography } from 'antd';
import { 
  DashboardOutlined, 
  FileTextOutlined, 
  ClockCircleOutlined,
  SwapOutlined,
  BatteryOutlined,
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

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      // Always succeed with demo login
      localStorage.setItem('access_token', 'demo_token_12345');
      setIsLoggedIn(true);
      
      // Load mock user data
      const response = await mockUserMe();
      setUser(response.data);
    } catch (error) {
      console.error('Login failed:', error);
      // Even if mock fails, still login
      setIsLoggedIn(true);
      setUser({
        id: 1,
        name: "Admin User",
        email: "admin@registry.com",
        role: 4,
        organisation: "Demo Organization"
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    setIsLoggedIn(false);
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
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ 
          background: 'white', 
          padding: '40px', 
          borderRadius: '12px', 
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          width: '400px'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <Title level={2} style={{ color: '#1890ff', marginBottom: '8px' }}>
              🌱 Granular Certificate Registry
            </Title>
            <p style={{ color: '#666', fontSize: '16px' }}>
              EnergyTag 2.0 Compliant System
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
                onChange={(e) => setLoginForm({...loginForm, email: e.target.value})}
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
                onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
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
                background: '#1890ff',
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
              <strong>Demo Credentials:</strong><br/>
              Email: admin@registry.com<br/>
              Password: admin123
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        style={{ background: '#001529' }}
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
          {collapsed ? '🌱' : '🌱 GC Registry'}
        </div>
        
        <Menu theme="dark" defaultSelectedKeys={['dashboard']} mode="inline">
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
          <Menu.Item key="storage" icon={<BatteryOutlined />}>
            Storage
          </Menu.Item>
          <Menu.Item key="devices" icon={<SettingOutlined />}>
            Devices
          </Menu.Item>
        </Menu>
      </Sider>
      
      <Layout>
        <Header style={{ 
          background: 'white', 
          padding: '0 24px', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            Granular Certificate Registry System
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
        
        <Content style={{ margin: '0', background: '#f0f2f5' }}>
          <Dashboard />
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;