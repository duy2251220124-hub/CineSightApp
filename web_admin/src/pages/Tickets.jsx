import { useState, useEffect } from 'react';
import { getTicketsList } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiMissing, setApiMissing] = useState(false);

  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [selectedShow, setSelectedShow] = useState('2026-09-29T19:30');

  const fetchTickets = async () => {
    setLoading(true);
    setApiMissing(false);
    try {
      const data = await getTicketsList(selectedRoom, selectedShow);
      setTickets(data);
    } catch (e) {
      if (e.message === "API_MISSING") {
        setApiMissing(true);
        setTickets([]);
      } else {
        alert("Lá»—i khi táº£i danh sÃ¡ch vÃ©: " + e.message);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTickets();
  }, [selectedRoom, selectedShow]);

  return (
    <div className="soc-container">
      {/* KHUNG XÆ¯Æ NG: THANH TRÃŠN CÃ™NG */}
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <input type="text" placeholder="TÃ¬m kiáº¿m mÃ£ vÃ©..." className="soc-input" style={{ width: 250 }} />
        </div>
        <div className="soc-clock" style={{ fontSize: 16 }}>Äá»I CHIáº¾U Dá»® LIá»†U VÃ‰</div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          MOBILE APP: Sáº´N SÃ€NG
        </div>
      </header>

      {/* KHUNG XÆ¯Æ NG: Ná»¬A TRÃŠN (Chia 6.5 / 3.5) */}
      <div style={{ display: 'flex', gap: 16, height: 160 }}>
        {/* Cá»˜T TRÃI: Báº¢NG ÄIá»€U KHIá»‚N CHÃNH */}
        <div className="soc-panel" style={{ flex: 6.5, display: 'flex', flexDirection: 'column' }}>
          <div className="panel-title">Báº¢NG ÄIá»€U KHIá»‚N Äá»’NG Bá»˜</div>
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16, flex: 1 }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>PhÃ²ng chiáº¿u</label>
                <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)} className="soc-input">
                  <option value="room1">IMAX (room1)</option>
                  <option value="room2">2D (room2)</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Suáº¥t chiáº¿u</label>
                <select value={selectedShow} onChange={e => setSelectedShow(e.target.value)} className="soc-input">
                  <option value="2026-09-29T19:30">2026-09-29 19:30</option>
                  <option value="2026-10-05T19:30">2026-10-05 19:30</option>
                  <option value="2026-10-05T21:00">2026-10-05 21:00</option>
                </select>
              </div>
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: 13, lineHeight: 1.5 }}>
              Tráº¡ng thÃ¡i: <strong style={{ color: '#14C692' }}>Äang káº¿t ná»‘i nháº­n dá»¯ liá»‡u...</strong><br/>
              Láº§n Ä‘á»“ng bá»™ cuá»‘i: <em>Vá»«a xong</em>
            </div>
          </div>
        </div>

        {/* Cá»˜T PHáº¢I: LIVE FEED NOTIFICATIONS */}
        <div className="soc-panel" style={{ flex: 3.5, display: 'flex', flexDirection: 'column' }}>
          <div className="panel-title">LUá»’NG VÃ‰ Vá»ªA QUÃ‰T (LIVE FEED)</div>
          <div style={{ flex: 1, padding: '8px 12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 13, color: 'var(--text-dim)', fontStyle: 'italic', textAlign: 'center', marginTop: 32 }}>
              [ChÆ°a cÃ³ dá»¯ liá»‡u live streaming tá»« Mobile]
            </div>
          </div>
        </div>
      </div>

      {/* KHUNG XÆ¯Æ NG: HÃ€NG 4 THá»NG KÃŠ (Ã‰p vÃ o 1 Grid vuÃ´ng vá»©c chuáº©n SOC) */}
      <div className="soc-panel" style={{ display: 'flex' }}>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">Tá»”NG VÃ‰ Táº¬P A</div>
          <div className="stat-val" style={{ color: 'var(--text-main)', marginTop: 4 }}>{tickets.length}</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">VÃ‰ ÄÃƒ QUÃ‰T (Táº¬P B)</div>
          <div className="stat-val" style={{ color: '#14C692', marginTop: 4 }}>0</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">CHÆ¯A QUÃ‰T (TRá»NG)</div>
          <div className="stat-val alert-amber" style={{ marginTop: 4 }}>0</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px' }}>
          <div className="stat-label">Lá»†CH / KHÃCH Láº¬U</div>
          <div className="stat-val alert-red" style={{ marginTop: 4 }}>0</div>
        </div>
      </div>

      {/* Báº¢NG Dá»® LIá»†U CHI TIáº¾T */}
      <div className="soc-panel soc-feed">
        <div className="panel-title">DANH SÃCH CHI TIáº¾T Tá»ªNG VÃ‰</div>
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th>MÃ£ VÃ© (Ticket ID)</th>
                <th>MÃ£ Gháº¿ (Seat ID)</th>
                <th>Tráº¡ng ThÃ¡i QuÃ©t</th>
                <th>Thá»i Gian QuÃ©t (Mobile)</th>
                <th className="align-right">Tráº¡ng ThÃ¡i Chá»— Ngá»“i (AI)</th>
              </tr>
            </thead>
            <tbody>
              {apiMissing ? (
                <tr>
                  <td colSpan="5" className="empty-state">
                    <div style={{ fontSize: 32, marginBottom: 12 }}>ðŸ”Œ</div>
                    <div style={{ color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>CHÆ¯A Káº¾T Ná»I API BACKEND</div>
                    <div>TÃ­nh nÄƒng Danh sÃ¡ch VÃ© yÃªu cáº§u API GET /api/v1/tickets.</div>
                    <div>Vui lÃ²ng yÃªu cáº§u bá»™ pháº­n ká»¹ thuáº­t hoÃ n thiá»‡n Backend Ä‘á»ƒ hiá»ƒn thá»‹ danh sÃ¡ch táº¡i Ä‘Ã¢y.</div>
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan="5" className="empty-state">KhÃ´ng cÃ³ vÃ© nÃ o trong suáº¥t chiáº¿u nÃ y.</td>
                </tr>
              ) : tickets.map((t, i) => (
                <tr key={`${t.ticket_id}-${i}`}>
                  <td className="mono font-bold">{t.ticket_id}</td>
                  <td className="mono">{t.seat_id}</td>
                  <td><span style={{ color: '#14C692' }}>âœ… Há»£p lá»‡</span></td>
                  <td className="mono" style={{ color: 'var(--text-dim)' }}>--</td>
                  <td className="align-right" style={{ color: 'var(--text-dim)' }}>--</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
