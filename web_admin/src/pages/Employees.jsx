import { useState, useEffect } from 'react';
import { getEmployees, addEmployee, deleteEmployee, updateEmployee } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [empName, setEmpName] = useState('');
  const [empUsername, setEmpUsername] = useState('');
  const [empPassword, setEmpPassword] = useState('');
  const [empRole, setEmpRole] = useState('Dọn rạp');
  const [empShift, setEmpShift] = useState('ca_sang');
  const [empLoading, setEmpLoading] = useState(false);
  
  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({ username: '', password: '', name: '', role: '', shift: '' });

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
      await addEmployee(empUsername.trim(), empPassword.trim(), empName.trim(), empRole, empShift || null);
      setEmpName('');
      setEmpUsername('');
      setEmpPassword('');
      setEmpShift('ca_sang');
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

  const handleStartEdit = (emp) => {
    setEditingId(emp.id);
    setEditData({
      username: emp.username,
      password: '',
      name: emp.name,
      role: emp.role,
      shift: emp.shift || ''
    });
  };

  const handleSaveEdit = async () => {
    if (!editData.username.trim() || !editData.name.trim()) return;
    setEmpLoading(true);
    try {
      await updateEmployee(
        editingId, 
        editData.username.trim(), 
        editData.password.trim(), 
        editData.name.trim(), 
        editData.role,
        editData.shift || null
      );
      setEditingId(null);
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (e) {
      alert('Lỗi cập nhật nhân sự: ' + e.message);
    }
    setEmpLoading(false);
  };

  const getShiftBadge = (shift) => {
    if (shift === 'ca_sang') return <span style={{ color: '#2563EB', fontWeight: 600 }}>Ca sáng (08:00 - 16:00)</span>;
    if (shift === 'ca_toi') return <span style={{ color: '#7C3AED', fontWeight: 600 }}>Ca tối (16:00 - 24:00)</span>;
    return <span style={{ color: 'var(--text-dim)' }}>Chưa phân ca</span>;
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
                  <th>Mật khẩu</th>
                  <th>Họ Tên</th>
                  <th>Vai trò</th>
                  <th>Ca trực</th>
                  <th className="align-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {employees.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="empty-state">Chưa có nhân viên nào.</td>
                  </tr>
                ) : employees.map(emp => {
                  const isEditing = editingId === emp.id;
                  return (
                  <tr key={emp.id} style={{ backgroundColor: isEditing ? 'rgba(0, 255, 255, 0.05)' : 'transparent' }}>
                    <td className="mono font-bold">#{emp.id}</td>
                    
                    {/* Username Column */}
                    <td>
                      {isEditing ? (
                        <input 
                          type="text" 
                          className="soc-input"
                          value={editData.username}
                          onChange={e => setEditData({...editData, username: e.target.value})}
                          style={{ padding: '4px 8px', minWidth: 100 }}
                        />
                      ) : (
                        <span className="mono" style={{ color: 'var(--brand-blue)' }}>{emp.username}</span>
                      )}
                    </td>

                    {/* Password Column */}
                    <td>
                      {isEditing ? (
                        <input 
                          type="password" 
                          className="soc-input mono"
                          placeholder="(Để trống nếu không đổi)"
                          value={editData.password}
                          onChange={e => setEditData({...editData, password: e.target.value})}
                          style={{ padding: '4px 8px', minWidth: 150 }}
                        />
                      ) : (
                        <span className="mono" style={{ color: 'var(--text-dim)' }}>
                          ••••••••
                        </span>
                      )}
                    </td>

                    {/* Name Column */}
                    <td>
                      {isEditing ? (
                        <input 
                          type="text" 
                          className="soc-input"
                          value={editData.name}
                          onChange={e => setEditData({...editData, name: e.target.value})}
                          style={{ padding: '4px 8px', minWidth: 120 }}
                        />
                      ) : (
                        <span style={{ color: 'var(--text-main)' }}>{emp.name}</span>
                      )}
                    </td>

                    {/* Role Column */}
                    <td>
                      {isEditing ? (
                        <select 
                          className="soc-input" 
                          value={editData.role}
                          onChange={e => setEditData({...editData, role: e.target.value})}
                          style={{ padding: '4px 8px' }}
                        >
                          <option value="Dọn rạp">Dọn rạp</option>
                          <option value="Soát vé">Soát vé</option>
                        </select>
                      ) : (
                        <span style={{ 
                          padding: '4px 8px', 
                          borderRadius: 4, 
                          backgroundColor: 'rgba(255,255,255,0.05)',
                          fontSize: 12,
                          color: emp.role === 'Quản lý' ? 'var(--brand-blue)' : 'var(--text-dim)'
                        }}>
                          {emp.role}
                        </span>
                      )}
                    </td>

                    {/* Shift Column */}
                    <td>
                      {isEditing ? (
                        <select 
                          className="soc-input" 
                          value={editData.shift}
                          onChange={e => setEditData({...editData, shift: e.target.value})}
                          style={{ padding: '4px 8px' }}
                        >
                          <option value="">Chưa phân ca</option>
                          <option value="ca_sang">Ca sáng (08:00 - 16:00)</option>
                          <option value="ca_toi">Ca tối (16:00 - 24:00)</option>
                        </select>
                      ) : (
                        getShiftBadge(emp.shift)
                      )}
                    </td>

                    {/* Actions Column */}
                    <td className="align-right">
                      {isEditing ? (
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <button 
                            className="soc-btn action-btn" 
                            onClick={handleSaveEdit}
                            disabled={empLoading}
                          >
                            LƯU
                          </button>
                          <button 
                            className="soc-btn action-btn" 
                            style={{ borderColor: 'var(--text-dim)', color: 'var(--text-dim)' }}
                            onClick={() => setEditingId(null)}
                            disabled={empLoading}
                          >
                            HỦY
                          </button>
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          <button 
                            className="soc-btn action-btn" 
                            style={{ color: 'var(--brand-blue)', borderColor: 'rgba(0, 243, 255, 0.3)' }}
                            onClick={() => handleStartEdit(emp)}
                            disabled={empLoading}
                          >
                            SỬA
                          </button>
                          <button 
                            className="soc-btn action-btn" 
                            style={{ color: 'var(--alert-red)', borderColor: 'rgba(255, 65, 77, 0.3)' }}
                            onClick={() => handleDeleteEmployee(emp.id)}
                            disabled={empLoading}
                          >
                            XÓA
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                )})}
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
              <select 
                className="soc-input" 
                style={{ flex: 1, minWidth: 160 }}
                value={empShift}
                onChange={e => setEmpShift(e.target.value)}
              >
                <option value="ca_sang">Ca sáng (08:00 - 16:00)</option>
                <option value="ca_toi">Ca tối (16:00 - 24:00)</option>
                <option value="">Chưa phân ca</option>
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
