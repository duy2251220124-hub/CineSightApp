import sys

content = '''import { useState, useEffect } from 'react';
import { analyzeRoom, healthCheck, getActiveAlerts, resolveAlert } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [serverOnline, setServerOnline] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [showId, setShowId] = useState('2026-10-05T19:30');
  const [imageFile, setImageFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  
  // New alert animation tracking
  const [prevAlertIds, setPrevAlertIds] = useState(new Set());
  const [newAlertId, setNewAlertId] = useState(null);

  // Ä á»“ng há»“ SOC
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Kiá»ƒm tra Server Health
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
    const timer = setInterval(check, 10000);
    return () => clearInterval(timer);
  }, []);

  // Fetch Alerts vÃ  phÃ¡t hiá»‡n cáº£nh bÃ¡o má»›i
  const getAlerts = async () => {
    try {
      const data = await getActiveAlerts();
      setAlerts(data);
      
      const currentIds = new Set(data.map(a => a.id));
      // TÃ¬m alert má»›i nháº¥t (náº¿u cÃ³)
      const newIds = data.filter(a => !prevAlertIds.has(a.id)).map(a => a.id);
      if (newIds.length > 0 && prevAlertIds.size > 0) {
        setNewAlertId(newIds[0]); // Chá»‰ highligh 1 dÃ²ng má»›i nháº¥t
        setTimeout(() => setNewAlertId(null), 3000); // Táº¯t hiá»‡u á»©ng sau 3s
      }
      setPrevAlertIds(currentIds);
    } catch (e) {
      console.error('Lá»—i fetch:', e);
    }
  };

  useEffect(() => {
    getAlerts();
    const alertTimer = setInterval(getAlerts, 5000);
    return () => clearInterval(alertTimer);
  }, [prevAlertIds]);

  const handleAnalyze = async () => {
    if (!imageFile) return alert('YÃªu cáº§u chá» n áº£nh snapshot.');
    setIsAnalyzing(true);
    try {
      await analyzeRoom(selectedRoom, showId, imageFile);
      await getAlerts(); // Cáº­p nháº­t tÃ¬nh trConfiguration ngay
    } catch (e) {
      alert('Lá»—i AI: ' + e.message);
    }
    setIsAnalyzing(false);
  };

  const handleResolve = async (id) => {
    try {
      await resolveAlert(id);
      await getAlerts(); // Cáº­p nháº­t láº¡i lÆ°á»›i
    } catch (e) {
      alert('KhÃ´ng thá»ƒ giáº£i quyáº¿t: ' + e.message);
    }
  };

  const illegalCount = alerts.filter(a => a.alert_type === 'illegal_occupant').length;
  const missingCount = alerts.filter(a => a.alert_type === 'missing_guest').length;
  const overCapCount = alerts.filter(a => a.alert_type === 'over_capacity').length;
  const totalCount = alerts.length;

  return (
    <div className="soc-container">
      {/* HEADER ROW */}
      <header className="soc-header">
        <div className="soc-brand">CINESIGHT SOC</div>
        <div className="soc-status">
          <span className={status-indicator }></span>
          API: {serverOnline ? 'ONLINE' : 'OFFLINE'}
        </div>
        <div className="soc-clock">{currentTime.toLocaleTimeString('vi-VN', { hour12: false })}</div>
      </header>

      {/* QUICK STATS & MANUAL SCAN (2 COLUMNS) */}
      <div className="soc-controls-row">
        <div className="soc-panel soc-stats">
          <div className="panel-title">Tá»”NG QUAN HÃ”M NAY</div>
          <div className="stats-bar">
            <span className="stat-item"><span className="stat-label">Tá»”NG Cáº¢NH BÃ O:</span> <span className="stat-val">{totalCount}</span></span>
            <span className="stat-item"><span className="stat-label">KHÃ CH Láº¬U (Ä á»Ž):</span> <span className="stat-val alert-red">{illegalCount}</span></span>
            <span className="stat-item"><span className="stat-label">VÃ€NG Máº¶T (VÃ€NG):</span> <span className="stat-val alert-amber">{missingCount}</span></span>
            <span className="stat-item"><span className="stat-label">VÆ¯á»¢T Táº¢I (Ä á»Ž):</span> <span className="stat-val alert-red">{overCapCount}</span></span>
          </div>
        </div>

        <div className="soc-panel soc-manual">
          <div className="panel-title">KIá»‚M TRA THá»¦ CÃ”NG</div>
          <div className="manual-form">
            <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)} className="soc-input">
              <option value="room1">IMAX (room1)</option>
              <option value="room2">2D (room2)</option>
            </select>
            <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files[0])} className="soc-input file-input" />
            <button className="soc-btn primary" onClick={handleAnalyze} disabled={isAnalyzing || !serverOnline}>
              {isAnalyzing ? 'Ä ANG Xá»¬ LÃ ...' : 'CHáº Y AI'}
            </button>
          </div>
        </div>
      </div>

      {/* LIVE ALERTS FEED */}
      <div className="soc-panel soc-feed">
        <div className="panel-title">Cáº¢NH BÃ O CHá»œ Xá»¬ LÃ  (LIVE)</div>
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Thá» i gian</th>
                <th>Suáº¥t chiáº¿u</th>
                <th>PhÃ²ng</th>
                <th>Gháº¿</th>
                <th>Váº¥n Ä‘á» </th>
                <th className="align-right">Thao tÃ¡c</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-state">KhÃ´ng cÃ³ cáº£nh bÃ¡o nÃ o cáº§n xá»­ lÃ½.</td>
                </tr>
              ) : alerts.map(a => {
                let rowClass = '';
                let icon = '';
                let label = '';
                
                if (a.alert_type === 'illegal_occupant') {
                  rowClass = 'row-critical'; icon = 'â—¼ï¸ '; label = 'KhÃ¡ch láº­u';
                } else if (a.alert_type === 'over_capacity') {
                  rowClass = 'row-critical'; icon = 'â—¼ï¸ '; label = 'VÆ°á»£t táº£i';
                } else {
                  rowClass = 'row-warning'; icon = 'â–´ï¸ '; label = 'Trá»‘ng gháº¿';
                }

                if (a.id === newAlertId) {
                  rowClass += ' new-alert-flash';
                }

                return (
                  <tr key={a.id} className={rowClass}>
                    <td className="mono">{new Date(a.timestamp).toLocaleTimeString('vi-VN', { hour12: false })}</td>
                    <td className="mono">{a.show_id}</td>
                    <td>{a.room_id}</td>
                    <td className="mono font-bold">{a.seat_id || 'N/A'}</td>
                    <td className="issue-cell">
                      <span className="issue-icon">{icon}</span> {label}
                    </td>
                    <td className="align-right">
                      <button className="soc-btn action-btn" onClick={() => handleResolve(a.id)}>
                        Ä Ã¡nh dáº¥u Ä‘Ã£ xá»­ lÃ½
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
'''

with open(r'c:\CineSightApp\web_admin\src\pages\Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
