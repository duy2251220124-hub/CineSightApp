import { useState, useEffect } from 'react';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import Rooms from './pages/Rooms';
import Tickets from './pages/Tickets';
import Settings from './pages/Settings';
import Employees from './pages/Employees';
import Incidents from './pages/Incidents';
import Showtimes from './pages/Showtimes';
import { getIncidents, loginUser, logoutUser, getStoredUser } from './api/cineSightApi';
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
  const [currentUser, setCurrentUser] = useState(() => getStoredUser());
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      const res = await loginUser(loginUsername, loginPassword);
      if (res && res.user) {
        setCurrentUser(res.user);
        setLoginUsername('');
        setLoginPassword('');
      }
    } catch (err) {
      const msg = err?.response?.data?.error || 'Tài khoản hoặc mật khẩu không chính xác';
      setLoginError(msg);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    setCurrentUser(null);
  };

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

  if (!currentUser) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#F8FAFC',
        padding: 20,
      }}>
        <div style={{
          width: '100%',
          maxWidth: 400,
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: 12,
          padding: '32px 28px',
          boxShadow: '0 10px 25px rgba(15, 23, 42, 0.06)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <img
              src={logoImg}
              alt="CineSight Logo"
              style={{ width: 42, height: 42, borderRadius: 10, objectFit: 'cover' }}
            />
            <div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#0F172A' }}>
                Cine<span style={{ color: 'var(--brand-blue)' }}>Sight</span> SOC
              </div>
              <div style={{ fontSize: 12, color: '#64748B' }}>
                Đăng nhập hệ thống quản trị & giám sát
              </div>
            </div>
          </div>

          {loginError && (
            <div style={{
              background: '#FEF2F2',
              border: '1px solid #FECACA',
              color: '#DC2626',
              padding: '10px 12px',
              borderRadius: 8,
              fontSize: 13,
              marginBottom: 16,
            }}>
              {loginError}
            </div>
          )}

          <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>
                TÀI KHOẢN
              </label>
              <input
                type="text"
                className="soc-input"
                placeholder="Nhập username (VD: admin, duy)..."
                value={loginUsername}
                onChange={(e) => setLoginUsername(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box' }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 6 }}>
                MẬT KHẨU
              </label>
              <input
                type="password"
                className="soc-input"
                placeholder="Nhập mật khẩu..."
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                style={{ width: '100%', boxSizing: 'border-box' }}
                required
              />
            </div>
            <button
              type="submit"
              className="soc-btn primary"
              disabled={loginLoading}
              style={{ marginTop: 6, padding: '10px 16px', fontWeight: 700 }}
            >
              {loginLoading ? 'ĐANG XÁC THỰC...' : 'ĐĂNG NHẬP'}
            </button>
          </form>
        </div>
      </div>
    );
  }

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

        {/* THÔNG TIN NGƯỜI DÙNG ĐĂNG NHẬP */}
        <div style={{
          padding: '12px 14px',
          borderTop: '1px solid var(--border-color, #E2E8F0)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
          background: '#F8FAFC',
          borderRadius: 8,
          marginTop: 8,
        }}>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#0F172A', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {currentUser.name}
            </div>
            <div style={{ fontSize: 11, color: '#64748B' }}>
              {currentUser.role} {currentUser.shift_label ? `• ${currentUser.shift_label}` : ''}
            </div>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="soc-btn"
            style={{ padding: '4px 8px', fontSize: 11, flexShrink: 0 }}
            title="Đăng xuất"
          >
            Thoát
          </button>
        </div>
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
