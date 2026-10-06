import { useState, useEffect } from 'react';
import { getEmployees, addEmployee, deleteEmployee } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [empName, setEmpName] = useState('');
  const [empUsername, setEmpUsername] = useState('');
  const [empPassword, setEmpPassword] = useState('');
  const [empRole, setEmpRole] = useState('Bảo vệ');
  const [empLoading, setEmpLoading] = useState(false);

  const fetchInitialData = async () => {
    try {
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (e) {
      alert("Lỗi tải dữ liệu Nhân sự: " + e.message);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    if (!empName.trim() || !empUsername.trim() || !empPassword.trim()) return;
    setEmpLoading(true);
    try {
      await addEmployee(empUsername.trim(), empPassword.trim(), empName.trim(), empRole);
      setEmpName('');
      setEmpUsername('');
      setEmpPassword('');
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (e) {
      alert('Lỗi thêm nhân sự: (Có thể username đã tồn tại)');
    }
    setEmpLoading(false);
  };

  const handleDeleteEmployee = async (id) => {
    if (!window.confirm("Bạn có chắc chắn muốn xóa nhân viên này?")) return;
    setEmpLoading(true);
    try {
      await deleteEmployee(id);
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (e) {
      alert('Lỗi xóa nhân sự: ' + e.message);
    }
    setEmpLoading(false);
  };

  return (
    <div className="soc-container">
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none' }}>
        <div className="soc-brand">QUẢN LÝ NHÂN SỰ</div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          DATABASE: SẴN SÀNG
        </div>
      </header>

      <div className="soc-controls-row" style={{ height: 'auto', flex: 1, alignItems: 'flex-start' }}>
        <div className="soc-panel soc-feed" style={{ flex: 1, minHeight: 400 }}>
          <div className="panel-title">DANH SÁCH TÀI KHOẢN VẬN HÀNH</div>
          <div className="table-wrapper" style={{ maxHeight: 600 }}>
            <table className="soc-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Tài khoản</th>
                  <th>Họ Tên</th>
                  <th>Vai trò</th>
                  <th className="align-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {employees.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty-state">Chưa có nhân viên nào.</td>
                  </tr>
                ) : employees.map(emp => (
                  <tr key={emp.id}>
                    <td className="mono font-bold">#{emp.id}</td>
                    <td className="mono" style={{ color: 'var(--brand-blue)' }}>{emp.username}</td>
                    <td style={{ color: 'var(--text-main)' }}>{emp.name}</td>
                    <td>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: 4, 
                        backgroundColor: 'rgba(255,255,255,0.05)',
                        fontSize: 12,
                        color: emp.role === 'Quản lý' ? 'var(--brand-blue)' : 'var(--text-dim)'
                      }}>
                        {emp.role}
                      </span>
                    </td>
                    <td className="align-right">
                      <button 
                        className="soc-btn action-btn" 
                        style={{ color: 'var(--alert-red)', borderColor: 'rgba(255, 65, 77, 0.3)' }}
                        onClick={() => handleDeleteEmployee(emp.id)}
                        disabled={empLoading}
                      >
                        XÓA
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div style={{ padding: 16, borderTop: '1px solid var(--grid-line)', backgroundColor: 'rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8, fontWeight: 600 }}>TẠO TÀI KHOẢN MỚI</div>
            <form onSubmit={handleAddEmployee} className="manual-form" style={{ padding: 0, flexWrap: 'wrap' }}>
              <input 
                type="text" 
                placeholder="Tài khoản đăng nhập..." 
                className="soc-input" 
                style={{ flex: 1, minWidth: 150 }}
                value={empUsername}
                onChange={e => setEmpUsername(e.target.value)}
                required
              />
              <input 
                type="password" 
                placeholder="Mật khẩu..." 
                className="soc-input" 
                style={{ flex: 1, minWidth: 150 }}
                value={empPassword}
                onChange={e => setEmpPassword(e.target.value)}
                required
              />
              <input 
                type="text" 
                placeholder="Họ Tên nhân viên..." 
                className="soc-input" 
                style={{ flex: 1, minWidth: 150 }}
                value={empName}
                onChange={e => setEmpName(e.target.value)}
                required
              />
              <select 
                className="soc-input" 
                style={{ flex: 1, minWidth: 120 }}
                value={empRole}
                onChange={e => setEmpRole(e.target.value)}
              >
                <option value="Dọn rạp">Dọn rạp</option>
                <option value="Soát vé">Soát vé</option>
              </select>
              <button 
                type="submit" 
                className="soc-btn primary" 
                style={{ flexBasis: '100%', marginTop: 8 }}
                disabled={empLoading || !empName.trim() || !empUsername.trim() || !empPassword.trim()}
              >
                TẠO TÀI KHOẢN
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
