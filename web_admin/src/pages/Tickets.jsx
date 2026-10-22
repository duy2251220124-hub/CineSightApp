import { useState, useEffect, useMemo } from 'react';
import { getTicketsList, getShowtimes } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [showtimes, setShowtimes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [apiMissing, setApiMissing] = useState(false);

  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [selectedShow, setSelectedShow] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const loadShows = async () => {
      try {
        const list = await getShowtimes(selectedRoom);
        setShowtimes(list);
        if (list.length > 0) {
          setSelectedShow(list[0].show_id);
        }
      } catch {
        setShowtimes([]);
      }
    };
    loadShows();
  }, [selectedRoom]);

  const fetchTickets = async () => {
    if (!selectedShow) return;
    setLoading(true);
    setApiMissing(false);
    try {
      const data = await getTicketsList(selectedRoom, selectedShow);
      setTickets(data);
    } catch (e) {
      if (e.message === "API_MISSING" || (e.response && e.response.status === 404)) {
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

  const filteredTickets = useMemo(() => {
    return tickets.filter(t => {
      const matchesSearch = (t.ticket_id && t.ticket_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
                            (t.seat_id && t.seat_id.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStatus = statusFilter === 'all' || statusFilter === 'valid';
      return matchesSearch && matchesStatus;
    });
  }, [tickets, searchQuery, statusFilter]);

  return (
    <div className="soc-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div className="soc-brand" style={{ color: 'var(--brand-blue)' }}>DANH SÁCH VÉ</div>
        </div>
        <div className="soc-clock" style={{ fontSize: 16 }}>QUẢN LÝ VÉ ĐỒNG BỘ</div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          MOBILE APP: SẴN SÀNG
        </div>
      </header>

      {/* THANH CÔNG CỤ (TÌM KIẾM, LỌC) */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexShrink: 0, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Phòng chiếu</label>
          <select value={selectedRoom} onChange={e => setSelectedRoom(e.target.value)} className="soc-input" style={{ width: 170 }}>
            <option value="room1">Phòng chiếu 1</option>
            <option value="room2">Phòng chiếu 2</option>
            <option value="room3">Phòng chiếu 3</option>
            <option value="room4">Phòng chiếu 4</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Suất chiếu</label>
          <select value={selectedShow} onChange={e => setSelectedShow(e.target.value)} className="soc-input" style={{ width: 320 }}>
            {showtimes.length === 0 ? (
              <option value="2026-10-17T08:30">08:30 - 10:15 | 2DDUB Crayon Shinchan</option>
            ) : (
              showtimes.map(s => (
                <option key={s.show_id} value={s.show_id}>
                  {s.start_time} - {s.end_time} ({s.duration_minutes}p) | {s.movie_name}
                </option>
              ))
            )}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Trạng thái AI</label>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="soc-input" style={{ width: 150 }}>
            <option value="all">Tất cả</option>
            <option value="valid">Hợp lệ</option>
            <option value="alert">Có cảnh báo</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 200 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Tìm kiếm vé/ghế</label>
          <input 
            type="text" 
            placeholder="Nhập mã vé hoặc mã ghế..." 
            className="soc-input" 
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* THANH CHỈ SỐ GỌN NGÀNG */}
      <div className="soc-panel" style={{ display: 'flex', flexWrap: 'wrap', flexShrink: 0, marginBottom: 16 }}>
        <div style={{ flex: '1 1 200px', padding: '12px 16px', borderRight: '1px solid var(--grid-line)' }}>
          <div className="stat-label">VÉ ĐÃ ĐỒNG BỘ (ĐÃ QUÉT)</div>
          <div className="stat-val" style={{ color: '#14C692', marginTop: 4, fontFamily: "'JetBrains Mono', monospace" }}>{tickets.length}</div>
        </div>
        <div style={{ flex: '1 1 200px', padding: '12px 16px' }}>
          <div className="stat-label">LỆCH SO VỚI CAMERA</div>
          <div className="stat-val" style={{ color: 'var(--text-dim)', marginTop: 4, fontFamily: "'JetBrains Mono', monospace" }}>-</div>
        </div>
      </div>

      <div className="soc-panel soc-feed" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
        <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <span>DANH SÁCH CHI TIẾT TỪNG VÉ</span>
          <span style={{ fontSize: 12, color: 'var(--text-dim)', fontWeight: 'normal', textTransform: 'none' }}>
            Hiển thị {filteredTickets.length} / {tickets.length} vé
          </span>
        </div>
        
        {loading ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
            Đang tải dữ liệu...
          </div>
        ) : apiMissing ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
            <div style={{ color: 'var(--text-main)', fontWeight: 600, marginBottom: 4 }}>CHƯA KẾT NỐI API BACKEND</div>
            <div style={{ color: 'var(--text-dim)' }}>Tính năng Danh sách Vé yêu cầu API GET /api/v1/tickets.</div>
          </div>
        ) : (
          <div className="table-wrapper" style={{ flex: 1, overflowY: 'auto' }}>
            <table className="soc-table">
              <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--surface)', zIndex: 1, boxShadow: '0 1px 0 var(--grid-line)' }}>
                <tr>
                  <th>Mã Vé (Ticket ID)</th>
                  <th>Mã Ghế (Seat ID)</th>
                  <th>Trạng Thái Quét</th>
                  <th className="align-right">Thời Gian Quét (Mobile)</th>
                  <th className="align-right">Trạng Thái AI</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty-state" style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-dim)' }}>
                      {tickets.length === 0 ? "Chưa có vé nào được đồng bộ cho suất này. Quét vé trên app rồi quay lại." : "Không tìm thấy vé nào phù hợp với bộ lọc."}
                    </td>
                  </tr>
                ) : filteredTickets.map((t, i) => (
                  <tr key={`${t.ticket_id}-${i}`}>
                    <td className="mono font-bold" style={{ whiteSpace: 'nowrap' }}>{t.ticket_id}</td>
                    <td className="mono" style={{ whiteSpace: 'nowrap' }}>{t.seat_id}</td>
                    <td>
                      <span style={{ 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        backgroundColor: 'rgba(20, 198, 146, 0.1)', 
                        color: '#14C692',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        Đã quét
                      </span>
                    </td>
                    <td className="mono align-right" style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>--</td>
                    <td className="align-right" style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>--</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
