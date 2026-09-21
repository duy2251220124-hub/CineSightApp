import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import '../src/styles/dashboard.css';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Bảng điều khiển', icon: '📊' },
  { id: 'alerts',    label: 'Cảnh báo',         icon: '🚨' },
  { id: 'rooms',     label: 'Quản lý phòng',     icon: '🎬' },
  { id: 'tickets',   label: 'Danh sách vé',      icon: '🎫' },
  { id: 'settings',  label: 'Cài đặt',           icon: '⚙️' },
];

function App() {
  const [activePage, setActivePage] = useState('dashboard');

  return (
    <div className="layout">
      {/* SIDEBAR */}
      <div className="sidebar">
        <div className="sidebar-logo">
          Cine<span>Sight</span>
        </div>
        {NAV_ITEMS.map(item => (
          <div
            key={item.id}
            className={`nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => setActivePage(item.id)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      {/* NỘI DUNG CHÍNH */}
      <div className="main-content">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage !== 'dashboard' && (
          <div style={{ color: '#555', marginTop: 80, textAlign: 'center', fontSize: '1rem' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🚧</div>
            <div>Trang <strong style={{ color: '#e0e0e0' }}>"{NAV_ITEMS.find(n => n.id === activePage)?.label}"</strong> đang được xây dựng...</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
