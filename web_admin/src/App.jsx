import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Rooms from './pages/Rooms';
import Tickets from './pages/Tickets';
import Settings from './pages/Settings';
import Employees from './pages/Employees';
import '../src/styles/dashboard.css';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Bảng điều khiển', icon: '📊' },
  { id: 'alerts',    label: 'Cảnh báo',         icon: '🚨' },
  { id: 'rooms',     label: 'Quản lý phòng',     icon: '🎬' },
  { id: 'tickets',   label: 'Danh sách vé',      icon: '🎫' },
  { id: 'employees', label: 'Nhân sự',          icon: '👥' },
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
        {activePage === 'alerts' && <Alerts />}
        {activePage === 'rooms' && <Rooms />}
        {activePage === 'tickets' && <Tickets />}
        {activePage === 'employees' && <Employees />}
        {activePage === 'settings' && <Settings />}
      </div>
    </div>
  );
}

export default App;
