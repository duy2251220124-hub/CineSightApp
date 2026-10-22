import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Rooms from './pages/Rooms';
import Tickets from './pages/Tickets';
import Settings from './pages/Settings';
import Employees from './pages/Employees';
import Incidents from './pages/Incidents';
import Showtimes from './pages/Showtimes';
import { getIncidents } from './api/cineSightApi';
import logoImg from './assets/logo.png';
import {
  LayoutDashboard,
  ShieldAlert,
  Bell,
  Projector,
  CalendarClock,
  Ticket,
  Users,
  Settings as SettingsIcon,
} from './components/Icons';
import './styles/dashboard.css';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Bảng điều khiển', Icon: LayoutDashboard },
  { id: 'alerts',    label: 'Cảnh báo',         Icon: ShieldAlert },
  { id: 'incidents', label: 'Thông báo',        Icon: Bell },
  { id: 'rooms',     label: 'Quản lý phòng',     Icon: Projector },
  { id: 'showtimes', label: 'Lịch chiếu',       Icon: CalendarClock },
  { id: 'tickets',   label: 'Danh sách vé',      Icon: Ticket },
  { id: 'employees', label: 'Nhân sự',          Icon: Users },
  { id: 'settings',  label: 'Cài đặt',           Icon: SettingsIcon },
];

function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [openIncidents, setOpenIncidents] = useState(0);

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const data = await getIncidents();
        const open = data.filter(i => i.status === 'open').length;
        setOpenIncidents(open);
      } catch (e) {
        // ignore
      }
    };
    
    fetchCount();
    const interval = setInterval(fetchCount, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="layout">
      {/* SIDEBAR */}
      <aside className="sidebar">
        {/* LOGO CHÍNH THỨC CỦA DỰ ÁN */}
        <div className="sidebar-logo">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <img
              src={logoImg}
              alt="CineSight Logo"
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                objectFit: 'cover',
                flexShrink: 0,
                boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
              }}
            />
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: '-0.5px' }}>
                <span style={{ color: '#0F172A' }}>Cine</span>
                <span style={{ color: 'var(--brand-blue)' }}>Sight</span>
              </span>
              <span style={{
                fontSize: 10,
                fontWeight: 700,
                color: 'var(--brand-blue)',
                background: 'var(--brand-blue-light)',
                border: '1px solid #BFDBFE',
                padding: '2px 5px',
                borderRadius: 4,
                letterSpacing: '0.5px'
              }}>
                SOC
              </span>
            </div>
          </div>
        </div>

        {/* DANH SÁCH ĐIỀU HƯỚNG */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2, flex: 1 }}>
          {NAV_ITEMS.map(item => {
            const isActive = activePage === item.id;
            return (
              <div
                key={item.id}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActivePage(item.id)}
              >
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <item.Icon size={18} />
                  <span>{item.label}</span>
                </div>
                {item.id === 'incidents' && openIncidents > 0 && (
                  <span className={`nav-badge ${isActive ? 'active-badge' : ''}`}>
                    {openIncidents}
                  </span>
                )}
              </div>
            );
          })}
        </nav>
      </aside>

      {/* NỘI DUNG CHÍNH */}
      <main className="main-content">
        {activePage === 'dashboard' && <Dashboard />}
        {activePage === 'alerts' && <Alerts />}
        {activePage === 'incidents' && <Incidents />}
        {activePage === 'rooms' && <Rooms />}
        {activePage === 'showtimes' && <Showtimes onNavigateToTickets={() => setActivePage('tickets')} />}
        {activePage === 'tickets' && <Tickets />}
        {activePage === 'employees' && <Employees />}
        {activePage === 'settings' && <Settings />}
      </main>
    </div>
  );
}

export default App;
