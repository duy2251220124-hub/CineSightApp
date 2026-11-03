import { useState, useEffect } from 'react';
import { getEmployees, addEmployee, deleteEmployee, updateEmployee, getStoredUser } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Employees() {
  const [employees, setEmployees] = useState([]);
  const [empName, setEmpName] = useState('');
  const [empUsername, setEmpUsername] = useState('');
  const [empPassword, setEmpPassword] = useState('');
  const [empRole, setEmpRole] = useState('Soát vé');
  const [empShift, setEmpShift] = useState('ca_sang');
  const [empLoading, setEmpLoading] = useState(false);

  // Tài khoản đang đăng nhập
  const currentUser = getStoredUser();

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({
    username: '',
    password: '',
    name: '',
    role: 'Soát vé',
    shift: '',
    is_active: 1,
  });

  const fetchInitialData = async () => {
    try {
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (e) {
      alert('Lỗi tải dữ liệu Nhân sự: ' + (e.response?.data?.error || e.message));
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const isSelfRow = (emp) => {
    if (!currentUser || !emp) return false;
    if (currentUser.id !== undefined && emp.id === currentUser.id) return true;
    if (currentUser.username && emp.username && emp.username.toLowerCase() === currentUser.username.toLowerCase()) {
      return true;
    }
    return false;
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    if (!empName.trim() || !empUsername.trim() || !empPassword.trim()) return;
    setEmpLoading(true);
    try {
      await addEmployee(empUsername.trim(), empPassword.trim(), empName.trim(), 'Soát vé', empShift || null);
      setEmpName('');
      setEmpUsername('');
      setEmpPassword('');
      setEmpRole('Soát vé');
      setEmpShift('ca_sang');
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (err) {
      alert('Lỗi thêm nhân sự: ' + (err.response?.data?.error || 'Có thể username đã tồn tại'));
    }
    setEmpLoading(false);
  };

  const handleDeleteEmployee = async (emp) => {
    if (isSelfRow(emp)) return;
    if (!window.confirm(`Bạn có chắc chắn muốn xóa nhân viên "${emp.name}" (@${emp.username})?`)) return;
    setEmpLoading(true);
    try {
      const res = await deleteEmployee(emp.id);
      if (res && res.action === 'deactivated') {
        alert(
          res.message ||
            'Nhân viên này đã từng lập/xử lý biên bản sự cố nên được chuyển sang trạng thái "Ngưng hoạt động" để bảo toàn lịch sử dữ liệu.'
        );
      }
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (err) {
      alert('Lỗi xóa nhân sự: ' + (err.response?.data?.error || err.message));
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
      shift: emp.shift || '',
      is_active: emp.is_active === 0 || emp.is_active === false ? 0 : 1,
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
        editData.shift || null,
        editData.is_active
      );
      setEditingId(null);
      const emps = await getEmployees();
      setEmployees(emps);
    } catch (err) {
      alert('Lỗi cập nhật nhân sự: ' + (err.response?.data?.error || err.message));
    }
    setEmpLoading(false);
  };

  const getShiftBadge = (shift) => {
    if (shift === 'ca_sang') return <span style={{ color: '#2563EB', fontWeight: 600 }}>Ca sáng (08:00 - 16:00)</span>;
    if (shift === 'ca_toi') return <span style={{ color: '#7C3AED', fontWeight: 600 }}>Ca tối (16:00 - 24:00)</span>;
    return <span style={{ color: 'var(--text-dim)' }}>Chưa phân ca</span>;
  };

  const formatLastSeen = (isoStr) => {
    if (!isoStr) return 'Chưa hoạt động';
    try {
      const d = new Date(isoStr);
      if (Number.isNaN(d.getTime())) return isoStr;
      return d.toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  const renderStatusBadge = (emp) => {
    const isActive = !(emp.is_active === 0 || emp.is_active === false);
    if (!isActive) {
      return (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '3px 10px',
            borderRadius: 999,
            backgroundColor: '#FEE2E2',
            color: '#B91C1C',
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#EF4444' }} />
          Ngưng hoạt động
        </span>
      );
    }

    if (emp.is_online) {
      return (
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '3px 10px',
            borderRadius: 999,
            backgroundColor: '#DCFCE7',
            color: '#15803D',
            fontSize: 12,
            fontWeight: 600,
          }}
          title={emp.last_seen_at ? `Hoạt động gần nhất: ${formatLastSeen(emp.last_seen_at)}` : 'Đang hoạt động'}
        >
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#22C55E' }} />
          Đang trực tuyến
        </span>
      );
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 12,
            fontWeight: 600,
            color: 'var(--text-dim)',
          }}
        >
          <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#94A3B8' }} />
          Ngoại tuyến
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
          {emp.last_seen_at ? `Lần cuối: ${formatLastSeen(emp.last_seen_at)}` : 'Chưa hoạt động'}
        </span>
      </div>
    );
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
                  <th>Trạng thái</th>
                  <th className="align-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {employees.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-state">Chưa có nhân viên nào.</td>
                  </tr>
                ) : (
                  employees.map(emp => {
                    const isEditing = editingId === emp.id;
                    const isSelf = isSelfRow(emp);
                    const isInactive = emp.is_active === 0 || emp.is_active === false;
                    return (
                      <tr
                        key={emp.id}
                        style={{
                          backgroundColor: isEditing
                            ? 'rgba(37, 99, 235, 0.06)'
                            : isSelf
                            ? 'rgba(37, 99, 235, 0.03)'
                            : 'transparent',
                          opacity: isInactive && !isEditing ? 0.72 : 1,
                        }}
                      >
                        <td className="mono font-bold">#{emp.id}</td>

                        {/* Username Column */}
                        <td>
                          {isEditing ? (
                            <input
                              type="text"
                              className="soc-input"
                              value={editData.username}
                              onChange={e => setEditData({ ...editData, username: e.target.value })}
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
                              onChange={e => setEditData({ ...editData, password: e.target.value })}
                              style={{ padding: '4px 8px', minWidth: 150 }}
                            />
                          ) : (
                            <span className="mono" style={{ color: 'var(--text-dim)' }}>
                              ••••••••
                            </span>
                          )}
                        </td>

                        {/* Name Column + Badge "Bạn" */}
                        <td>
                          {isEditing ? (
                            <input
                              type="text"
                              className="soc-input"
                              value={editData.name}
                              onChange={e => setEditData({ ...editData, name: e.target.value })}
                              style={{ padding: '4px 8px', minWidth: 120 }}
                            />
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--text-main)' }}>
                              <span>{emp.name}</span>
                              {isSelf && (
                                <span
                                  style={{
                                    padding: '2px 8px',
                                    borderRadius: 999,
                                    backgroundColor: '#DBEAFE',
                                    color: '#1D4ED8',
                                    fontSize: 11,
                                    fontWeight: 700,
                                  }}
                                >
                                  Bạn
                                </span>
                              )}
                            </span>
                          )}
                        </td>

                        {/* Role Column */}
                        <td>
                          {isEditing ? (
                            isSelf ? (
                              <span
                                style={{
                                  padding: '4px 8px',
                                  borderRadius: 4,
                                  backgroundColor: 'rgba(37, 99, 235, 0.1)',
                                  fontSize: 12,
                                  fontWeight: 600,
                                  color: 'var(--brand-blue)',
                                }}
                              >
                                {emp.role}
                              </span>
                            ) : (
                              <select
                                className="soc-input"
                                value={editData.role}
                                onChange={e => setEditData({ ...editData, role: e.target.value })}
                                style={{ padding: '4px 8px' }}
                              >
                                <option value="Soát vé">Soát vé</option>
                              </select>
                            )
                          ) : (
                            <span
                              style={{
                                padding: '4px 8px',
                                borderRadius: 4,
                                backgroundColor: 'rgba(255,255,255,0.05)',
                                fontSize: 12,
                                fontWeight: emp.role === 'Quản lý' ? 700 : 500,
                                color: emp.role === 'Quản lý' ? 'var(--brand-blue)' : 'var(--text-dim)',
                              }}
                            >
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
                              onChange={e => setEditData({ ...editData, shift: e.target.value })}
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

                        {/* Status Column */}
                        <td>{renderStatusBadge(emp, isEditing, isSelf)}</td>

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
                              {!isSelf && (
                                <button
                                  className="soc-btn action-btn"
                                  style={{ color: 'var(--alert-red)', borderColor: 'rgba(255, 65, 77, 0.3)' }}
                                  onClick={() => handleDeleteEmployee(emp)}
                                  disabled={empLoading}
                                >
                                  XÓA
                                </button>
                              )}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div style={{ padding: 16, borderTop: '1px solid var(--grid-line)', backgroundColor: 'rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8, fontWeight: 600 }}>
              TẠO TÀI KHOẢN NHÂN VIÊN SOÁT VÉ MỚI
            </div>
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
