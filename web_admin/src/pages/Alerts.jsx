import { useState, useEffect } from 'react';
import { getAlertHistory } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Alerts() {
  const [filterRoom, setFilterRoom] = useState('ALL');
  const [filterType, setFilterType] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiMissing, setApiMissing] = useState(false);

  const fetchHistory = async () => {
    setLoading(true);
    setApiMissing(false);
    try {
      const data = await getAlertHistory(filterRoom, filterType, filterStatus);
      setAlerts(data);
    } catch (e) {
      if (e.message === "API_MISSING") {
        setApiMissing(true);
        setAlerts([]);
      } else {
        alert("Lỗi khi tải lịch sử: " + e.message);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchHistory();
  }, [filterRoom, filterType, filterStatus]);

  return (
    <div className="soc-container">
      {/* TOOLBAR */}
      <div className="soc-panel">
        <div className="panel-title">BỘ LỌC TÌM KIẾM SỰ CỐ</div>
        <div className="manual-form" style={{ padding: '12px 16px' }}>
          <label style={{ fontSize: 13, color: 'var(--text-dim)' }}>Phòng:</label>
          <select value={filterRoom} onChange={e => setFilterRoom(e.target.value)} className="soc-input">
            <option value="ALL">Tất cả phòng</option>
            <option value="room1">IMAX (room1)</option>
            <option value="room2">2D (room2)</option>
          </select>
          
          <span style={{ width: 16 }}></span>
          
          <label style={{ fontSize: 13, color: 'var(--text-dim)' }}>Loại:</label>
          <select value={filterType} onChange={e => setFilterType(e.target.value)} className="soc-input">
            <option value="ALL">Tất cả loại cảnh báo</option>
            <option value="illegal_occupant">Khách lậu (Đỏ)</option>
            <option value="missing_guest">Vắng mặt (Vàng)</option>
            <option value="over_capacity">Vượt tải (Đỏ)</option>
          </select>
          
          <span style={{ width: 16 }}></span>
          
          <label style={{ fontSize: 13, color: 'var(--text-dim)' }}>Trạng thái:</label>
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} className="soc-input">
            <option value="ALL">Tất cả trạng thái</option>
            <option value="active">⏳ Đang chờ xử lý</option>
            <option value="resolved">✅ Đã xử lý</option>
          </select>
          
          <div style={{ flex: 1 }}></div>
          
          <button className="soc-btn primary" onClick={fetchHistory} disabled={loading}>
            {loading ? 'ĐANG TẢI...' : 'LÀM MỚI'}
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="soc-panel soc-feed">
        <div className="panel-title">LỊCH SỬ CẢNH BÁO TOÀN HỆ THỐNG</div>
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Thời gian</th>
                <th>Suất chiếu</th>
                <th>Phòng</th>
                <th>Ghế</th>
                <th>Vấn đề</th>
                <th>Trạng thái</th>
                <th className="align-right">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {apiMissing ? (
                <tr>
                  <td colSpan="7" className="empty-state">
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🔌</div>
                    <div style={{ color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>CHƯA KẾT NỐI API BACKEND</div>
                    <div>Tính năng Lịch sử Cảnh báo yêu cầu API GET /api/v1/alerts/history.</div>
                    <div>Vui lòng yêu cầu bộ phận kỹ thuật hoàn thiện Backend.</div>
                  </td>
                </tr>
              ) : alerts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-state">Không có dữ liệu phù hợp với bộ lọc.</td>
                </tr>
              ) : alerts.map(a => {
                let rowClass = '';
                let icon = null;
                let label = '';
                
                if (a.alert_type === 'illegal_occupant') {
                  rowClass = 'row-critical'; 
                  label = 'Khách lậu';
                  icon = (
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                  );
                } else if (a.alert_type === 'over_capacity') {
                  rowClass = 'row-capacity'; 
                  label = 'Vượt tải';
                  icon = (
                    <svg viewBox="0 0 24 24"><path d="M11 15h2v2h-2zm0-8h2v6h-2zm.99-5C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"/></svg>
                  );
                } else {
                  rowClass = 'row-warning'; 
                  label = 'Trống ghế';
                  icon = (
                    <svg viewBox="0 0 24 24"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>
                  );
                }

                return (
                  <tr key={a.id} className={rowClass}>
                    <td className="mono">{new Date(a.timestamp).toLocaleString('vi-VN')}</td>
                    <td className="mono">{a.show_id}</td>
                    <td>{a.room_id}</td>
                    <td className="mono font-bold">{a.seat_id || 'N/A'}</td>
                    <td className="issue-cell">
                      <span className="issue-icon">{icon}</span> {label}
                    </td>
                    <td>
                      {a.resolved ? (
                        <span style={{ color: '#14C692', fontWeight: 600 }}>✅ Đã xử lý</span>
                      ) : (
                        <span style={{ color: 'var(--alert-amber)', fontWeight: 600 }}>⏳ Chờ xử lý</span>
                      )}
                    </td>
                    <td className="align-right">
                      <button className="soc-btn action-btn" disabled={a.resolved}>
                        {a.resolved ? 'Đã xong' : 'Xử lý ngay'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
