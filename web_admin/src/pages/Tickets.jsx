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
        alert("Lỗi khi tải danh sách vé: " + e.message);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTickets();
  }, [selectedRoom, selectedShow]);

  return (
    <div className="soc-container">
      {/* KHUNG XƯƠNG: THANH TRÊN CÙNG */}
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <input type="text" placeholder="Tìm kiếm mã vé..." className="soc-input" style={{ width: 250 }} />
        </div>
        <div className="soc-clock" style={{ fontSize: 16 }}>ĐỐI CHIẾU DỮ LIỆU VÉ</div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          MOBILE APP: SẴN SÀNG
        </div>
      </header>

      {/* KHUNG XƯƠNG: NỬA TRÊN (Chia 6.5 / 3.5) */}
      <div style={{ display: 'flex', gap: 16, height: 160 }}>
        {/* CỘT TRÁI: BẢNG ĐIỀU KHIỂN CHÍNH */}
        <div className="soc-panel" style={{ flex: 6.5, display: 'flex', flexDirection: 'column' }}>
          <div className="panel-title">BẢNG ĐIỀU KHIỂN ĐỒNG BỘ</div>
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 16, flex: 1 }}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Phòng chiếu</label>
                <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)} className="soc-input">
                  <option value="room1">IMAX (room1)</option>
                  <option value="room2">2D (room2)</option>
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Suất chiếu</label>
                <select value={selectedShow} onChange={e => setSelectedShow(e.target.value)} className="soc-input">
                  <option value="2026-09-29T19:30">2026-09-29 19:30</option>
                  <option value="2026-10-05T19:30">2026-10-05 19:30</option>
                  <option value="2026-10-05T21:00">2026-10-05 21:00</option>
                </select>
              </div>
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: 13, lineHeight: 1.5 }}>
              Trạng thái: <strong style={{ color: '#14C692' }}>Đang kết nối nhận dữ liệu...</strong><br/>
              Lần đồng bộ cuối: <em>Vừa xong</em>
            </div>
          </div>
        </div>

        {/* CỘT PHẢI: LIVE FEED NOTIFICATIONS */}
        <div className="soc-panel" style={{ flex: 3.5, display: 'flex', flexDirection: 'column' }}>
          <div className="panel-title">LUỒNG VÉ VỪA QUÉT (LIVE FEED)</div>
          <div style={{ flex: 1, padding: '8px 12px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 13, color: 'var(--text-dim)', fontStyle: 'italic', textAlign: 'center', marginTop: 32 }}>
              [Chưa có dữ liệu live streaming từ Mobile]
            </div>
          </div>
        </div>
      </div>

      {/* KHUNG XƯƠNG: HÀNG 4 THỐNG KÊ */}
      <div className="soc-panel" style={{ display: 'flex' }}>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">TỔNG VÉ TẬP A</div>
          <div className="stat-val" style={{ color: 'var(--text-main)', marginTop: 4 }}>{tickets.length}</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">VÉ ĐÃ QUÉT (TẬP B)</div>
          <div className="stat-val" style={{ color: '#14C692', marginTop: 4 }}>0</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">CHƯA QUÉT (TRỐNG)</div>
          <div className="stat-val alert-amber" style={{ marginTop: 4 }}>0</div>
        </div>
        <div style={{ flex: 1, padding: '12px 16px' }}>
          <div className="stat-label">LỆCH / KHÁCH LẬU</div>
          <div className="stat-val alert-red" style={{ marginTop: 4 }}>0</div>
        </div>
      </div>

      {/* BẢNG DỮ LIỆU CHI TIẾT */}
      <div className="soc-panel soc-feed">
        <div className="panel-title">DANH SÁCH CHI TIẾT TỪNG VÉ</div>
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th>Mã Vé (Ticket ID)</th>
                <th>Mã Ghế (Seat ID)</th>
                <th>Trạng Thái Quét</th>
                <th>Thời Gian Quét (Mobile)</th>
                <th className="align-right">Trạng Thái Chỗ Ngồi (AI)</th>
              </tr>
            </thead>
            <tbody>
              {apiMissing ? (
                <tr>
                  <td colSpan="5" className="empty-state">
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🔌</div>
                    <div style={{ color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>CHƯA KẾT NỐI API BACKEND</div>
                    <div>Tính năng Danh sách Vé yêu cầu API GET /api/v1/tickets.</div>
                    <div>Vui lòng yêu cầu bộ phận kỹ thuật hoàn thiện Backend để hiển thị danh sách tại đây.</div>
                  </td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan="5" className="empty-state">Không có vé nào trong suất chiếu này.</td>
                </tr>
              ) : tickets.map((t, i) => (
                <tr key={`${t.ticket_id}-${i}`}>
                  <td className="mono font-bold">{t.ticket_id}</td>
                  <td className="mono">{t.seat_id}</td>
                  <td>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      backgroundColor: 'rgba(20, 198, 146, 0.1)', 
                      color: '#14C692',
                      fontSize: '12px',
                      fontWeight: '600'
                    }}>
                      Hợp lệ
                    </span>
                  </td>
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

