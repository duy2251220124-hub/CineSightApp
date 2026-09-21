import { useState, useEffect } from 'react';
import { analyzeRoom, healthCheck } from '../api/cineSightApi';
import '../styles/dashboard.css';

// Dữ liệu mẫu cảnh báo (sẽ thay bằng API thực tế sau)
const MOCK_ALERTS = [
  { id: 1, room: 'IMAX (room1)', seat: 'C4', type: 'illegal', time: '19:02:14', show: 'Avengers 5 - 19:00' },
  { id: 2, room: '2D (room2)', seat: 'A7', type: 'missing', time: '19:05:31', show: 'Inside Out 3 - 19:00' },
  { id: 3, room: '4DX (room3)', seat: 'B2', type: 'illegal', time: '19:07:05', show: 'Moana 2 - 19:00' },
];

export default function Dashboard() {
  const [serverOnline, setServerOnline] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [imageFile, setImageFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  // Kiểm tra Server có đang chạy không
  useEffect(() => {
    const check = async () => {
      try {
        await healthCheck();
        setServerOnline(true);
      } catch {
        setServerOnline(false);
      }
    };
    check();
    const timer = setInterval(check, 10000); // Ping mỗi 10 giây
    return () => clearInterval(timer);
  }, []);

  const handleAnalyze = async () => {
    if (!imageFile) return alert('Hãy chọn một bức ảnh từ camera!');
    setIsAnalyzing(true);
    setResult(null);
    try {
      const data = await analyzeRoom(selectedRoom, imageFile);
      setResult(data);
    } catch (e) {
      setResult({ error: e.message });
    }
    setIsAnalyzing(false);
  };

  const illegalCount = MOCK_ALERTS.filter(a => a.type === 'illegal').length;
  const missingCount = MOCK_ALERTS.filter(a => a.type === 'missing').length;

  return (
    <div style={{ flex: 1 }}>
      <div className="page-title">📊 Bảng điều khiển kiểm soát rạp</div>

      {/* Trạng thái Server AI */}
      <div style={{ marginBottom: 20, fontSize: '0.85rem', color: serverOnline ? '#27ae60' : '#e74c3c' }}>
        <span className={`server-dot ${serverOnline ? 'online' : 'offline'}`}></span>
        AI Server: {serverOnline ? 'Đang chạy tại cổng 8000' : 'Ngoại tuyến – Kiểm tra uvicorn!'}
      </div>

      {/* Thẻ thống kê nhanh */}
      <div className="card-grid">
        <div className="stat-card red">
          <div className="label">🚨 Khách ngồi lậu (hôm nay)</div>
          <div className="value">{illegalCount}</div>
        </div>
        <div className="stat-card gold">
          <div className="label">⚠️ Ghế trống có vé</div>
          <div className="value">{missingCount}</div>
        </div>
        <div className="stat-card green">
          <div className="label">✅ Suất đã kiểm tra</div>
          <div className="value">8</div>
        </div>
        <div className="stat-card">
          <div className="label">🎬 Phòng chiếu đang hoạt động</div>
          <div className="value" style={{ color: '#e0e0e0' }}>3</div>
        </div>
      </div>

      {/* Panel kiểm tra AI thủ công */}
      <div className="analyze-panel">
        <h2>🔍 PHÂN TÍCH ẢNH CAMERA THỦ CÔNG</h2>
        <div className="form-row">
          <div className="form-group">
            <label>Chọn phòng chiếu</label>
            <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)}>
              <option value="room1">IMAX (room1)</option>
              <option value="room2">2D (room2)</option>
              <option value="room3">4DX (room3)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Upload ảnh từ camera CCTV</label>
            <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files[0])} />
          </div>
          <button className="btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing || !serverOnline}>
            {isAnalyzing ? 'Đang phân tích...' : '▶ Chạy AI'}
          </button>
        </div>
        {result && (
          <div className="result-box">
            {JSON.stringify(result, null, 2)}
          </div>
        )}
      </div>

      {/* Bảng cảnh báo gần nhất */}
      <div className="analyze-panel">
        <h2>🔔 LỊCH SỬ CẢNH BÁO GẦN NHẤT</h2>
        <table className="alert-table">
          <thead>
            <tr>
              <th>Thời gian</th>
              <th>Suất chiếu</th>
              <th>Phòng</th>
              <th>Ghế</th>
              <th>Loại cảnh báo</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_ALERTS.map(a => (
              <tr key={a.id}>
                <td style={{ color: '#888' }}>{a.time}</td>
                <td>{a.show}</td>
                <td>{a.room}</td>
                <td><strong>{a.seat}</strong></td>
                <td>
                  {a.type === 'illegal'
                    ? <span className="badge red">🚨 Ngồi không có vé</span>
                    : <span className="badge yellow">⚠️ Ghế trống có vé</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

