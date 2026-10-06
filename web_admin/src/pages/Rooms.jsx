import { useState, useEffect } from 'react';
import { getRoomsConfig } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiMissing, setApiMissing] = useState(false);

  const fetchRooms = async () => {
    setLoading(true);
    setApiMissing(false);
    try {
      const data = await getRoomsConfig();
      setRooms(data);
    } catch (e) {
      if (e.message === "API_MISSING") {
        setApiMissing(true);
        setRooms([]);
      } else {
        alert("Lỗi khi tải danh sách phòng: " + e.message);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  return (
    <div className="soc-container">
      {/* TABLE */}
      <div className="soc-panel soc-feed" style={{ flex: 1 }}>
        <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>TRẠNG THÁI HIỆU CHUẨN CAMERA (ROOM CALIBRATION)</span>
          <button className="soc-btn action-btn" onClick={fetchRooms} disabled={loading} style={{ padding: '4px 8px', fontSize: 12 }}>
            {loading ? 'ĐANG TẢI...' : 'TẢI LẠI'}
          </button>
        </div>
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Mã Phòng</th>
                <th>Tổng ghế (Tập B)</th>
                <th>File JSON Tọa độ</th>
                <th>Ảnh hiệu chuẩn Camera</th>
              </tr>
            </thead>
            <tbody>
              {apiMissing ? (
                <tr>
                  <td colSpan="4" className="empty-state">
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🔌</div>
                    <div style={{ color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>CHƯA KẾT NỐI API BACKEND</div>
                    <div>Tính năng Quản lý Phòng yêu cầu API GET /api/v1/rooms.</div>
                    <div>Vui lòng yêu cầu bộ phận kỹ thuật hoàn thiện Backend.</div>
                  </td>
                </tr>
              ) : rooms.length === 0 ? (
                <tr>
                  <td colSpan="4" className="empty-state">Không tìm thấy phòng chiếu nào.</td>
                </tr>
              ) : rooms.map(room => (
                <tr key={room.room_id}>
                  <td className="mono font-bold">{room.room_id}</td>
                  <td className="mono">{room.total_seats}</td>
                  <td className="issue-cell">
                    {room.config_file 
                      ? <span style={{ color: '#14C692' }}>✅ Hợp lệ</span> 
                      : <span style={{ color: 'var(--alert-red)' }}>🔴 Thiếu file config</span>}
                  </td>
                  <td className="issue-cell">
                    {room.is_calibrated 
                      ? <span style={{ color: '#14C692' }}>✅ Sẵn sàng ({room.room_id}.jpg)</span> 
                      : <span style={{ color: 'var(--alert-red)' }}>🔴 Không tìm thấy</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
