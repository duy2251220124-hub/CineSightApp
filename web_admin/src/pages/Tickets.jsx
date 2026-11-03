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
    <div className="soc-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column', gap: 10 }}>
      {/* 1. COMPACT UNIFIED SOC HEADER & METRIC STRIP */}
      <header className="soc-header" style={{ paddingBottom: 10, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="soc-brand" style={{ color: 'var(--brand-blue)' }}>DANH SÁCH VÉ</div>
          <span style={{
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--text-dim)',
            background: 'var(--surface)',
            border: '1px solid var(--grid-line)',
            padding: '2px 8px',
            borderRadius: 4,
            letterSpacing: '0.5px'
          }}>
            QUẢN LÝ VÉ ĐỒNG BỘ
          </span>
        </div>

        {/* METRIC STRIP NGANG GỌN GÀNG */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'var(--surface)',
            border: '1px solid var(--grid-line)',
            borderRadius: 6,
            padding: '4px 12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--text-dim)', fontWeight: 600 }}>ĐÃ QUÉT:</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 15, fontWeight: 800, color: '#14C692' }}>
                {tickets.length}
              </span>
            </div>
            <span style={{ width: 1, height: 14, background: 'var(--grid-line)' }} />
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
              <span style={{ fontSize: 11, color: 'var(--text-dim)', fontWeight: 600 }}>HIỂN THỊ:</span>
              <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 14, fontWeight: 700, color: 'var(--text-main)' }}>
                {filteredTickets.length}
              </span>
            </div>
            <span style={{ width: 1, height: 14, background: 'var(--grid-line)' }} />
            <div className="soc-status" style={{ fontSize: 11.5, gap: 6 }}>
              <span className="status-indicator online" style={{ width: 7, height: 7 }} />
              <span style={{ color: 'var(--text-dim)' }}>MOBILE:</span>
              <span style={{ color: '#14C692', fontWeight: 700 }}>SẴN SÀNG</span>
            </div>
          </div>

          <button
            onClick={fetchTickets}
            disabled={loading}
            className="soc-btn"
            style={{ padding: '6px 12px', fontSize: 12, height: 32 }}
          >
            {loading ? 'Đang tải...' : 'Làm mới'}
          </button>
        </div>
      </header>

      {/* 2. THANH CÔNG CỤ TÌM KIẾM & BỘ LỌC NGANG TINH GỌN (1 DÒNG DUY NHẤT) */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        flexShrink: 0,
        background: 'var(--surface)',
        border: '1px solid var(--grid-line)',
        borderRadius: 6,
        padding: '8px 12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>Phòng:</span>
          <select
            value={selectedRoom}
            onChange={e => setSelectedRoom(e.target.value)}
            className="soc-input"
            style={{ width: 130, height: 32, padding: '4px 8px', fontSize: 12 }}
          >
            <option value="room1">Phòng 1</option>
            <option value="room2">Phòng 2</option>
            <option value="room3">Phòng 3</option>
            <option value="room4">Phòng 4</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 220, maxWidth: 380 }}>
          <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>Suất:</span>
          <select
            value={selectedShow}
            onChange={e => setSelectedShow(e.target.value)}
            className="soc-input"
            style={{ width: '100%', height: 32, padding: '4px 8px', fontSize: 12 }}
          >
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

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>Lọc AI:</span>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="soc-input"
            style={{ width: 110, height: 32, padding: '4px 8px', fontSize: 12 }}
          >
            <option value="all">Tất cả</option>
            <option value="valid">Hợp lệ</option>
            <option value="alert">Có cảnh báo</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 180 }}>
          <input
            type="text"
            placeholder="Tìm mã vé hoặc số ghế (VD: G05)..."
            className="soc-input"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ width: '100%', height: 32, padding: '4px 10px', fontSize: 12 }}
          />
        </div>
      </div>

      {/* 3. BẢNG CHI TIẾT TỪNG VÉ (MỞ RỘNG TỐI ĐA KHÔNG GIAN) */}
      <div className="soc-panel soc-feed" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 }}>
        <div className="panel-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0, padding: '8px 14px' }}>
          <span style={{ fontSize: 12, fontWeight: 800 }}>CHI TIẾT VÉ TRONG SUẤT CHIẾU</span>
          <span style={{ fontSize: 11.5, color: 'var(--text-dim)', fontWeight: 600, textTransform: 'none' }}>
            Hiển thị {filteredTickets.length} / {tickets.length} vé
          </span>
        </div>

        {loading ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: 13 }}>
            Đang tải dữ liệu vé...
          </div>
        ) : apiMissing ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
            <div style={{ color: 'var(--text-main)', fontWeight: 700, marginBottom: 4 }}>CHƯA KẾT NỐI API BACKEND</div>
            <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>Tính năng Danh sách Vé yêu cầu API GET /api/v1/tickets.</div>
          </div>
        ) : (
          <div className="table-wrapper" style={{ flex: 1, overflowY: 'auto' }}>
            <table className="soc-table">
              <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--surface)', zIndex: 1, boxShadow: '0 1px 0 var(--grid-line)' }}>
                <tr>
                  <th style={{ width: 180 }}>Mã Vé (Ticket ID)</th>
                  <th style={{ width: 120 }}>Mã Ghế</th>
                  <th style={{ width: 140 }}>Trạng Thái Quét</th>
                  <th className="align-right">Thời Gian Quét (Mobile)</th>
                  <th className="align-right" style={{ width: 140 }}>Đối Soát AI</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="empty-state" style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--text-dim)' }}>
                      {tickets.length === 0 ? "Chưa có vé nào được đồng bộ cho suất này. Quét vé trên mobile app rồi kiểm tra lại." : "Không tìm thấy vé nào phù hợp với bộ lọc."}
                    </td>
                  </tr>
                ) : filteredTickets.map((t, i) => (
                  <tr key={`${t.ticket_id}-${i}`}>
                    <td className="mono font-bold" style={{ whiteSpace: 'nowrap', color: 'var(--brand-blue)' }}>
                      {t.ticket_id}
                    </td>
                    <td className="mono font-bold" style={{ whiteSpace: 'nowrap', color: '#0F172A' }}>
                      <span style={{ background: 'var(--bg-dark)', padding: '2px 6px', borderRadius: 4, border: '1px solid var(--grid-line)' }}>
                        {t.seat_id}
                      </span>
                    </td>
                    <td>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: 4,
                        backgroundColor: 'rgba(20, 198, 146, 0.1)',
                        color: '#14C692',
                        fontSize: 11.5,
                        fontWeight: 700,
                        border: '1px solid rgba(20, 198, 146, 0.25)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4
                      }}>
                        <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#14C692' }} />
                        Đã quét
                      </span>
                    </td>
                    <td className="mono align-right" style={{ color: 'var(--text-dim)', whiteSpace: 'nowrap', fontSize: 12 }}>
                      {t.scanned_at || '--'}
                    </td>
                    <td className="align-right" style={{ whiteSpace: 'nowrap' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: '#EFF6FF',
                        color: '#2563EB',
                        fontSize: 11,
                        fontWeight: 600,
                        border: '1px solid #BFDBFE'
                      }}>
                        Khớp CCTV
                      </span>
                    </td>
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
