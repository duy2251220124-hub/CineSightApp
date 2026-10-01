import { useState, useEffect } from 'react';
import { analyzeRoom, healthCheck } from '../api/cineSightApi';
import '../styles/dashboard.css';

// Dá»¯ liá»‡u máº«u cáº£nh bÃ¡o (sáº½ thay báº±ng API thá»±c táº¿ sau)
const MOCK_ALERTS = [
  { id: 1, room: 'IMAX (room1)', seat: 'C4', type: 'illegal', time: '19:02:14', show: 'Avengers 5 - 19:00' },
  { id: 2, room: '2D (room2)', seat: 'A7', type: 'missing', time: '19:05:31', show: 'Inside Out 3 - 19:00' },
  { id: 3, room: '4DX (room3)', seat: 'B2', type: 'illegal', time: '19:07:05', show: 'Moana 2 - 19:00' },
];

export default function Dashboard() {
  const [serverOnline, setServerOnline] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [showId, setShowId] = useState('2026-09-29T19:30');
  const [imageFile, setImageFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);


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
    const timer = setInterval(check, 10000); //
    return () => clearInterval(timer);
  }, []);

  const handleAnalyze = async () => {
    if (!imageFile) return alert('HÃ£y chá»n má»™t bá»©c áº£nh tá»« camera!');
    setIsAnalyzing(true);
    setResult(null);
    try {
      const data = await analyzeRoom(selectedRoom, showId, imageFile);
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
      <div className="page-title">ðŸ“Š Báº£ng Ä‘iá»u khiá»ƒn kiá»ƒm soÃ¡t ráº¡p</div>

      {/* Tráº¡ng thÃ¡i Server AI */}
      <div style={{ marginBottom: 20, fontSize: '0.85rem', color: serverOnline ? '#27ae60' : '#e74c3c' }}>
        <span className={`server-dot ${serverOnline ? 'online' : 'offline'}`}></span>
        AI Server: {serverOnline ? 'Äang cháº¡y táº¡i cá»•ng 8000' : 'Ngoáº¡i tuyáº¿n â€“ Kiá»ƒm tra uvicorn!'}
      </div>

      {/* Tháº» thá»‘ng kÃª nhanh */}
      <div className="card-grid">
        <div className="stat-card red">
          <div className="label">ðŸš¨ KhÃ¡ch ngá»“i láº­u (hÃ´m nay)</div>
          <div className="value">{illegalCount}</div>
        </div>
        <div className="stat-card gold">
          <div className="label">âš ï¸ Gháº¿ trá»‘ng cÃ³ vÃ©</div>
          <div className="value">{missingCount}</div>
        </div>
        <div className="stat-card green">
          <div className="label">âœ… Suáº¥t Ä‘Ã£ kiá»ƒm tra</div>
          <div className="value">8</div>
        </div>
        <div className="stat-card">
          <div className="label">ðŸŽ¬ PhÃ²ng chiáº¿u Ä‘ang hoáº¡t Ä‘á»™ng</div>
          <div className="value" style={{ color: '#e0e0e0' }}>3</div>
        </div>
      </div>

      {/* Panel kiá»ƒm tra AI thá»§ cÃ´ng */}
      <div className="analyze-panel">
        <h2>ðŸ” PHÃ‚N TÃCH áº¢NH CAMERA THá»¦ CÃ”NG</h2>
        <div className="form-row">
          <div className="form-group">
            <label>Chá»n phÃ²ng chiáº¿u</label>
            <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)}>
              <option value="room1">IMAX (room1)</option>
              <option value="room2">2D (room2)</option>
              <option value="room3">4DX (room3)</option>
            </select>
          </div>
          <div className="form-group">
            <label>Upload áº£nh tá»« camera CCTV</label>
            <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files[0])} />
          </div>
          <button className="btn-analyze" onClick={handleAnalyze} disabled={isAnalyzing || !serverOnline}>
            {isAnalyzing ? 'Äang phÃ¢n tÃ­ch...' : 'â–¶ Cháº¡y AI'}
          </button>
        </div>
        {result && (
          <div className="result-box">
            {JSON.stringify(result, null, 2)}
          </div>
        )}
      </div>

      {/* Báº£ng cáº£nh bÃ¡o gáº§n nháº¥t */}
      <div className="analyze-panel">
        <h2>ðŸ”” Lá»ŠCH Sá»¬ Cáº¢NH BÃO Gáº¦N NHáº¤T</h2>
        <table className="alert-table">
          <thead>
            <tr>
              <th>Thá»i gian</th>
              <th>Suáº¥t chiáº¿u</th>
              <th>PhÃ²ng</th>
              <th>Gháº¿</th>
              <th>Loáº¡i cáº£nh bÃ¡o</th>
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
                    ? <span className="badge red">ðŸš¨ Ngá»“i khÃ´ng cÃ³ vÃ©</span>
                    : <span className="badge yellow">âš ï¸ Gháº¿ trá»‘ng cÃ³ vÃ©</span>
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

