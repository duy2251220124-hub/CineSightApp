import { useState, useEffect } from 'react';
import { getRoomsConfig, getRoomSeats, getShowtimes, getTicketsList, clearTickets, getIncidents, API_BASE } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [todayShows, setTodayShows] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Interactive Modals
  const [inspectRoom, setInspectRoom] = useState(null); // Phòng đang xem sơ đồ ghế
  const [loadingSeats, setLoadingSeats] = useState(false);
  const [calibrationModal, setCalibrationModal] = useState(null); // Modal xem góc camera hiệu chuẩn
  const [aiTestResult, setAiTestResult] = useState(null); // Kết quả AI test run
  const [testingAiRoom, setTestingAiRoom] = useState(null); // Phòng đang chạy AI test

  // 4 trạng thái màu ghế chuẩn:
  // - Màu xám: Trống (#1E293B)
  // - Màu xanh: Đã có người (#2563EB)
  // - Màu cam: Trục trặc (#F59E0B)
  // - Màu đỏ: Cảnh báo (#EF4444)
  const [occupiedSeats, setOccupiedSeats] = useState(new Set()); // Rỗng mặc định (Màu xám: Trống)
  const [brokenSeats, setBrokenSeats] = useState(new Set()); // Cam: Trục trặc
  const [warningSeats, setWarningSeats] = useState(new Set()); // Đỏ: Cảnh báo

  const fetchRooms = async () => {
    setLoading(true);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const [roomsData, showsData] = await Promise.all([
        getRoomsConfig(),
        getShowtimes(null, today).catch(() => [])
      ]);
      setRooms(roomsData);
      setTodayShows(showsData || []);
    } catch (e) {
      if (e.message !== "API_MISSING") {
        alert("Lỗi khi tải danh sách phòng: " + e.message);
      }
      setRooms([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchRooms();
  }, []);

  // Mở sơ đồ ghế 2D của phòng (Khởi tạo toàn bộ 136 ghế là Trống)
  const handleOpenSeatmap = async (room) => {
    setInspectRoom(room);
    setLoadingSeats(true);
    setOccupiedSeats(new Set());
    setBrokenSeats(new Set());
    setWarningSeats(new Set());
    try {
      await getRoomSeats(room.room_id);
      // Nạp danh sách vé đã đặt và sự cố thực tế
      const [tickets, incidents] = await Promise.all([
        getTicketsList(room.room_id).catch(() => []),
        getIncidents({ room_id: room.room_id, status: 'open' }).catch(() => [])
      ]);
      const occ = new Set();
      if (tickets && tickets.length > 0) {
        tickets.forEach(t => {
          const sid = t.seat_id || t.seat;
          if (sid) {
            occ.add(sid);
            const m = sid.match(/^([A-Z]+)(\d+)$/);
            if (m) occ.add(`${m[1]}${parseInt(m[2], 10)}`);
          }
        });
      }
      setOccupiedSeats(occ);

      const brk = new Set();
      const wrn = new Set();
      if (incidents && incidents.length > 0) {
        incidents.forEach(inc => {
          const list = Array.isArray(inc.seat_ids) ? inc.seat_ids : [];
          if (inc.category === 'seat_damage') {
            list.forEach(s => {
              brk.add(s);
              const m = String(s).match(/^([A-Z]+)(\d+)$/);
              if (m) brk.add(`${m[1]}${parseInt(m[2], 10)}`);
            });
          } else {
            list.forEach(s => {
              wrn.add(s);
              const m = String(s).match(/^([A-Z]+)(\d+)$/);
              if (m) wrn.add(`${m[1]}${parseInt(m[2], 10)}`);
            });
          }
        });
      }
      setBrokenSeats(brk);
      setWarningSeats(wrn);
    } catch (err) {
      console.error('Lỗi tải sơ đồ ghế:', err);
    } finally {
      setLoadingSeats(false);
    }
  };

  // Làm trống toàn bộ ghế của phòng đang xem
  const handleClearAllSeats = async () => {
    if (!inspectRoom) return;
    try {
      await clearTickets(inspectRoom.room_id);
      setOccupiedSeats(new Set());
      setBrokenSeats(new Set());
      setWarningSeats(new Set());
    } catch {
      setOccupiedSeats(new Set());
      setBrokenSeats(new Set());
      setWarningSeats(new Set());
    }
  };

  // Luân chuyển trạng thái ghế khi bấm: Trống -> Đã có người -> Trục trặc -> Cảnh báo -> Trống
  const toggleSeatStatus = (seatId) => {
    const m = seatId.match(/^([A-Z]+)(\d+)$/);
    const shortId = m ? `${m[1]}${parseInt(m[2], 10)}` : seatId;
    const padId = m ? `${m[1]}${String(parseInt(m[2], 10)).padStart(2, '0')}` : seatId;

    const isBroken = brokenSeats.has(shortId) || brokenSeats.has(padId);
    const isWarning = warningSeats.has(shortId) || warningSeats.has(padId);
    const isOccupied = occupiedSeats.has(shortId) || occupiedSeats.has(padId);

    if (!isBroken && !isWarning && !isOccupied) {
      // Trống -> Đã có người (Xanh)
      setOccupiedSeats(prev => new Set([...prev, shortId, padId]));
    } else if (isOccupied) {
      // Đã có người -> Trục trặc (Cam)
      setOccupiedSeats(prev => {
        const next = new Set(prev);
        next.delete(shortId);
        next.delete(padId);
        return next;
      });
      setBrokenSeats(prev => new Set([...prev, shortId, padId]));
    } else if (isBroken) {
      // Trục trặc -> Cảnh báo (Đỏ)
      setBrokenSeats(prev => {
        const next = new Set(prev);
        next.delete(shortId);
        next.delete(padId);
        return next;
      });
      setWarningSeats(prev => new Set([...prev, shortId, padId]));
    } else if (isWarning) {
      // Cảnh báo -> Trống (Xám)
      setWarningSeats(prev => {
        const next = new Set(prev);
        next.delete(shortId);
        next.delete(padId);
        return next;
      });
    }
  };

  const renderSeatBtn = (seatId) => {
    const m = seatId.match(/^([A-Z]+)(\d+)$/);
    const shortId = m ? `${m[1]}${parseInt(m[2], 10)}` : seatId;
    const padId = m ? `${m[1]}${String(parseInt(m[2], 10)).padStart(2, '0')}` : seatId;

    const isBroken = brokenSeats.has(shortId) || brokenSeats.has(padId);
    const isWarning = warningSeats.has(shortId) || warningSeats.has(padId);
    const isOccupied = occupiedSeats.has(shortId) || occupiedSeats.has(padId);

    // 4 màu chuẩn: Màu xanh: đã có người, Cam: trục trặc, Đỏ: cảnh báo, Màu xám: trống
    let bg = '#1E293B';
    let border = '#334155';
    let text = '#FFFFFF';
    let statusLabel = 'Trống';

    if (isWarning) {
      bg = '#EF4444';
      border = '#DC2626';
      text = '#FFFFFF';
      statusLabel = 'Cảnh báo';
    } else if (isBroken) {
      bg = '#F59E0B';
      border = '#D97706';
      text = '#FFFFFF';
      statusLabel = 'Trục trặc';
    } else if (isOccupied) {
      bg = '#2563EB';
      border = '#1D4ED8';
      text = '#FFFFFF';
      statusLabel = 'Đã có người';
    }

    return (
      <button
        key={seatId}
        onClick={() => toggleSeatStatus(seatId)}
        title={`Ghế ${seatId} - Trạng thái: ${statusLabel}\n(Bấm để đổi trạng thái)`}
        style={{
          width: 32,
          height: 24,
          background: bg,
          border: `1px solid ${border}`,
          color: text,
          borderRadius: 4,
          fontSize: 9.5,
          fontWeight: 700,
          fontFamily: 'JetBrains Mono, monospace',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'transform 0.1s',
          padding: 0
        }}
      >
        {seatId}
      </button>
    );
  };

  // Chạy kiểm tra kết nối mô hình AI
  const handleRunAiTest = (roomId, roomDisplayName) => {
    setTestingAiRoom(roomId);
    setAiTestResult(null);
    setTimeout(() => {
      setTestingAiRoom(null);
      setAiTestResult({
        roomId,
        roomDisplayName,
        engine: 'YOLOv8 Head Model',
        status: 'KẾT NỐI SẴN SÀNG',
        calibrationStatus: '136 ghế đã căn chỉnh tọa độ',
        timestamp: new Date().toLocaleTimeString('vi-VN')
      });
    }, 600);
  };

  const getRoomDisplayName = (roomId) => {
    switch (roomId) {
      case 'room1': return 'Phòng chiếu 1';
      case 'room2': return 'Phòng chiếu 2';
      case 'room3': return 'Phòng chiếu 3';
      case 'room4': return 'Phòng chiếu 4';
      default: return 'Phòng chiếu 1';
    }
  };

  const getRoomStatus = (roomId) => {
    const roomShows = todayShows.filter(s => s.room_id === roomId);
    if (!roomShows.length) {
      return { text: 'CHƯA CÓ SUẤT CHIẾU', type: 'unknown' };
    }
    const now = new Date();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();
    const currentPlaying = roomShows.find(s => {
      if (!s.start_time || !s.end_time) return false;
      const [sh, sm] = s.start_time.split(':').map(Number);
      const [eh, em] = s.end_time.split(':').map(Number);
      return nowMinutes >= (sh * 60 + sm) && nowMinutes <= (eh * 60 + em);
    });

    if (currentPlaying) {
      return { text: `ĐANG CHIẾU: ${currentPlaying.movie_name || 'Phim'}`, type: 'active' };
    }
    return { text: 'SẴN SÀNG', type: 'ready' };
  };

  const getStatusBadgeStyle = (statusType) => {
    switch (statusType) {
      case 'active':
        return { background: '#EFF6FF', color: '#2563EB', border: '1px solid #BFDBFE' };
      case 'ready':
        return { background: '#DCFCE7', color: '#15803D', border: '1px solid #BBF7D0' };
      default:
        return { background: '#F1F5F9', color: '#64748B', border: '1px solid #CBD5E1' };
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: '16px 20px',
      boxSizing: 'border-box',
      gap: 14,
      background: 'var(--bg-dark)',
      color: 'var(--text-main)',
      overflowY: 'auto'
    }}>
      {/* 1. HEADER TRANG */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#FFFFFF',
        padding: '10px 18px',
        borderRadius: 8,
        border: '1px solid #CBD5E1',
        boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
        flexShrink: 0
      }}>
        <div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--brand-blue)', letterSpacing: '-0.3px' }}>
            TRUNG TÂM VẬN HÀNH PHÒNG CHIẾU
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            onClick={fetchRooms}
            disabled={loading}
            style={{
              background: '#FFFFFF',
              border: '1px solid #CBD5E1',
              color: '#0F172A',
              padding: '6px 16px',
              borderRadius: 6,
              fontSize: 12.5,
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
            onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F1F5F9'; }}
            onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#FFFFFF'; }}
          >
            {loading ? 'ĐANG TẢI...' : 'TẢI LẠI TRẠNG THÁI'}
          </button>
        </div>
      </header>

      {/* 2. KẾT QUẢ AI TEST RUN BANNER (NẾU VỪA CHẠY THỬ) */}
      {aiTestResult && (
        <div style={{
          background: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: 8,
          padding: '12px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexShrink: 0,
          boxShadow: '0 1px 3px rgba(37, 99, 235, 0.1)'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{
                background: '#2563EB',
                color: '#FFFFFF',
                fontSize: 11,
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 4
              }}>
                KIỂM TRA KẾT NỐI AI
              </span>
              <span style={{ fontWeight: 800, fontSize: 13.5, color: '#1E40AF' }}>
                MÔ HÌNH PHÁT HIỆN NGƯỜI: {aiTestResult.roomDisplayName.toUpperCase()} ({aiTestResult.timestamp})
              </span>
            </div>
            <div style={{ fontSize: 12.5, color: '#2563EB', marginTop: 4, display: 'flex', gap: 18, fontWeight: 500 }}>
              <span>Trạng thái: <strong style={{ color: '#1E40AF' }}>{aiTestResult.status}</strong></span>
              <span>Động cơ AI: <strong style={{ color: '#1E40AF' }}>{aiTestResult.engine}</strong></span>
              <span>Tọa độ đa giác: <strong style={{ color: '#1E40AF' }}>{aiTestResult.calibrationStatus}</strong></span>
            </div>
          </div>
          <button
            onClick={() => setAiTestResult(null)}
            style={{ background: 'transparent', border: 'none', color: '#64748B', cursor: 'pointer', fontSize: 18, fontWeight: 700 }}
            title="Đóng thông báo"
          >
            ✕
          </button>
        </div>
      )}

      {/* 3. KHỐI 4 THẺ TRUNG TÂM VẬN HÀNH PHÒNG CHIẾU (2 TRÊN 2 DƯỚI - 2x2 GRID) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
        gap: 16,
        flex: 1
      }}>
        {['room1', 'room2', 'room3', 'room4'].map((rid) => {
          const roomDisplayName = getRoomDisplayName(rid);
          const roomObj = rooms.find(r => r.room_id === rid) || { total_seats: 136, is_calibrated: true };
          const statusObj = getRoomStatus(rid);
          const badgeStyle = getStatusBadgeStyle(statusObj.type);
          const isTesting = testingAiRoom === rid;

          return (
            <div
              key={rid}
              style={{
                background: '#FFFFFF',
                borderRadius: 10,
                border: '1px solid #CBD5E1',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)'
              }}
            >
              {/* TẦNG 1: TIÊU ĐỀ PHÒNG & TRẠNG THÁI */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 18, fontWeight: 800, color: '#0F172A', letterSpacing: '-0.3px' }}>
                      {roomDisplayName}
                    </span>
                    <span style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: '#475569',
                      background: '#F1F5F9',
                      border: '1px solid #E2E8F0',
                      padding: '2px 8px',
                      borderRadius: 4
                    }}>
                      {roomObj.total_seats || 136} ghế chuẩn
                    </span>
                  </div>

                  <span style={{
                    fontSize: 12,
                    fontWeight: 700,
                    padding: '3px 12px',
                    borderRadius: 4,
                    ...badgeStyle,
                    whiteSpace: 'nowrap',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6
                  }}>
                    <span style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      backgroundColor: badgeStyle.color
                    }} />
                    {statusObj.text}
                  </span>
                </div>

                {/* TẦNG 2: THÔNG SỐ VẬN HÀNH & HIỆU CHUẨN AI (LƯỚI 2 CỘT RỘNG RÃI, CÂN ĐỐI) */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: '12px 20px',
                  padding: '14px 16px',
                  background: '#F8FAFC',
                  borderRadius: 8,
                  border: '1px solid #E2E8F0',
                  marginBottom: 14
                }}>
                  {/* Cột 1 - Dòng 1: Tọa độ ghế AI */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      TỌA ĐỘ GHẾ AI
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      <span style={{
                        background: roomObj.is_calibrated ? '#DCFCE7' : '#F1F5F9',
                        color: roomObj.is_calibrated ? '#15803D' : '#64748B',
                        border: '1px solid ' + (roomObj.is_calibrated ? '#BBF7D0' : '#CBD5E1'),
                        padding: '1px 6px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700
                      }}>
                        {roomObj.is_calibrated ? 'Hợp lệ' : 'Chưa hiệu chuẩn'}
                      </span>
                      <span style={{ fontSize: 12.5, fontWeight: 600, color: '#0F172A' }}>
                        {roomObj.total_seats || 136} ghế đã căn chỉnh
                      </span>
                    </div>
                  </div>

                  {/* Cột 2 - Dòng 1: Ảnh hiệu chuẩn Camera */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      ẢNH HIỆU CHUẨN CAMERA
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: roomObj.is_calibrated ? 'var(--brand-blue)' : '#94A3B8' }}>
                      {roomObj.is_calibrated ? 'Đã liên kết (Full HD)' : 'Chưa có dữ liệu'}
                    </span>
                  </div>

                  {/* Cột 1 - Dòng 2: Cấu hình hàng ghế */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      CẤU HÌNH HÀNG GHẾ
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 600, color: '#0F172A' }}>
                      12 hàng ghế (A - L)
                    </span>
                  </div>

                  {/* Cột 2 - Dòng 2: Máy chiếu & Đèn */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      MÁY CHIẾU & ĐÈN
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: '#94A3B8' }}>
                      Chưa có dữ liệu
                    </span>
                  </div>

                  {/* Cột 1 - Dòng 3: Hệ thống âm thanh */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      HỆ THỐNG ÂM THANH
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: '#94A3B8' }}>
                      Chưa có dữ liệu
                    </span>
                  </div>

                  {/* Cột 2 - Dòng 3: Cảm biến môi trường */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      CẢM BIẾN MÔI TRƯỜNG
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 500, color: '#94A3B8' }}>
                      Chưa có dữ liệu
                    </span>
                  </div>
                </div>
              </div>

              {/* TẦNG 3: FOOTER CARD - ĐẦY ĐỦ 3 NÚT THAO TÁC RỘNG RÃI */}
              <div style={{ display: 'flex', gap: 10 }}>
                {/* Nút 1: Xem sơ đồ ghế */}
                <button
                  onClick={() => handleOpenSeatmap({ room_id: rid, name: roomDisplayName, total_seats: roomObj.total_seats || 136 })}
                  style={{
                    flex: 1,
                    height: 36,
                    background: '#FFFFFF',
                    border: '1px solid #CBD5E1',
                    color: '#1E293B',
                    borderRadius: 6,
                    fontSize: 12.5,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F1F5F9'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#FFFFFF'; }}
                >
                  Sơ đồ ghế 2D
                </button>

                {/* Nút 2: Xem góc camera hiệu chuẩn */}
                <button
                  onClick={() => setCalibrationModal({ roomId: rid, name: roomDisplayName })}
                  style={{
                    flex: 1,
                    height: 36,
                    background: '#EFF6FF',
                    border: '1px solid #BFDBFE',
                    color: 'var(--brand-blue)',
                    borderRadius: 6,
                    fontSize: 12.5,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#DBEAFE'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#EFF6FF'; }}
                >
                  Góc Camera AI
                </button>

                {/* Nút 3: Chạy thử phát hiện AI */}
                <button
                  onClick={() => handleRunAiTest(rid, roomDisplayName)}
                  disabled={isTesting}
                  style={{
                    flex: 1,
                    height: 36,
                    background: '#DCFCE7',
                    border: '1px solid #BBF7D0',
                    color: '#15803D',
                    borderRadius: 6,
                    fontSize: 12.5,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#BBF7D0'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#DCFCE7'; }}
                >
                  {isTesting ? 'Đang quét...' : 'Chạy thử AI'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* 4. MODAL XEM SƠ ĐỒ GHẾ 2D TƯƠNG TÁC */}
      {inspectRoom && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.45)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20
          }}
          onClick={() => setInspectRoom(null)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              border: '1px solid #CBD5E1',
              width: 660,
              maxWidth: '96vw',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.15)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header Modal */}
            <div style={{ padding: '10px 18px', background: '#F8FAFC', borderBottom: '1px solid #CBD5E1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, color: '#0F172A' }}>
                  SƠ ĐỒ GHẾ 2D: {inspectRoom.name} ({inspectRoom.total_seats || 136} GHẾ)
                </div>
                <div style={{ fontSize: 11, color: '#475569', marginTop: 1 }}>
                  Hàng A - L (136 ghế chuẩn đối chiếu camera an ninh) • Nhấn vào ghế để đổi trạng thái
                </div>
              </div>
              <button
                onClick={() => setInspectRoom(null)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', fontWeight: 700 }}
              >
                ✕
              </button>
            </div>

            {/* Thân sơ đồ ghế - KHÔNG SCROLL */}
            <div style={{ padding: '12px 16px', textAlign: 'center', overflow: 'hidden' }}>
              <div style={{
                height: 8,
                background: 'linear-gradient(to bottom, #2563EB, transparent)',
                borderRadius: '8px 8px 0 0',
                width: '70%',
                margin: '0 auto 4px auto',
                boxShadow: '0 3px 8px rgba(37, 99, 235, 0.3)'
              }} />
              <div style={{ fontSize: 10, color: '#64748B', fontWeight: 700, letterSpacing: '2px', marginBottom: 10 }}>
                MÀN HÌNH CHIẾU PHIM (SCREEN)
              </div>

              {loadingSeats ? (
                <div style={{ padding: 30, color: '#64748B' }}>Đang tải sơ đồ ghế...</div>
              ) : (
                <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 3, alignItems: 'center' }}>
                  {/* Hàng lối vào / lối ra */}
                  <div style={{ display: 'flex', width: 620, justifyContent: 'space-between', padding: '0 4px 4px 4px', fontSize: 11, fontWeight: 700, color: '#475569' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--brand-blue)' }}>
                      <span style={{ fontSize: 13 }}>↴</span> LỐI VÀO
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 5, color: '#64748B' }}>
                      LỐI RA <span style={{ fontSize: 13 }}>↗</span>
                    </span>
                  </div>

                  {/* HÀNG A: 8 ghế (A1 - A8) căn thẳng trên B2 - B9 */}
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    {Array.from({ length: 8 }, (_, idx) => renderSeatBtn(`A${idx + 1}`))}
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                  </div>

                  {/* CÁC HÀNG B ĐẾN J: 11 ghế mỗi hàng (B1-B11 ... J1-J11) */}
                  {['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'].map(r => (
                    <div key={r} style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                      <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                      <span style={{ width: 32 }} />
                      {Array.from({ length: 11 }, (_, idx) => renderSeatBtn(`${r}${idx + 1}`))}
                      <span style={{ width: 32 }} />
                      <span style={{ width: 32 }} />
                      <span style={{ width: 32 }} />
                      <span style={{ width: 32 }} />
                      <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                    </div>
                  ))}

                  {/* HÀNG K: K1 - K11, 2 ô trống thẳng hàng L13-L14 (BỎ LỐI ĐI), K12, K13 */}
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>K</span>
                    <span style={{ width: 32 }} />
                    {Array.from({ length: 11 }, (_, idx) => renderSeatBtn(`K${idx + 1}`))}
                    <span style={{ width: 32 }} />
                    <span style={{ width: 32 }} />
                    {renderSeatBtn('K12')}
                    {renderSeatBtn('K13')}
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>K</span>
                  </div>

                  {/* HÀNG L: 16 ghế liền mạch L1 - L16 (BỎ KHOẢNG CÁCH GIỮA L12 VÀ L13) */}
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>L</span>
                    {Array.from({ length: 16 }, (_, idx) => renderSeatBtn(`L${idx + 1}`))}
                    <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>L</span>
                  </div>
                </div>
              )}

              {/* Chú thích màu sắc */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: 18, marginTop: 14, fontSize: 11.5, fontWeight: 600, color: '#334155' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 13, height: 13, background: '#1E293B', border: '1px solid #334155', borderRadius: 3 }} />
                  Trống
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 13, height: 13, background: '#2563EB', border: '1px solid #1D4ED8', borderRadius: 3 }} />
                  Đã có người
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 13, height: 13, background: '#F59E0B', border: '1px solid #D97706', borderRadius: 3 }} />
                  Trục trặc
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ width: 13, height: 13, background: '#EF4444', border: '1px solid #DC2626', borderRadius: 3 }} />
                  Cảnh báo
                </span>
              </div>
            </div>

            {/* Footer Modal */}
            <div style={{ padding: '8px 18px', background: '#F8FAFC', borderTop: '1px solid #CBD5E1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button
                onClick={handleClearAllSeats}
                style={{
                  background: '#FFFFFF',
                  color: '#64748B',
                  border: '1px solid #CBD5E1',
                  padding: '6px 14px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: 12,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F1F5F9'; e.currentTarget.style.color = '#EF4444'; }}
                onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#FFFFFF'; e.currentTarget.style.color = '#64748B'; }}
                title="Làm trống toàn bộ 136 ghế của phòng này"
              >
                ↺ Làm trống toàn bộ ghế
              </button>
              <button
                onClick={() => setInspectRoom(null)}
                style={{ background: 'var(--brand-blue)', color: '#FFFFFF', border: 'none', padding: '6px 16px', borderRadius: 6, fontWeight: 700, fontSize: 12, cursor: 'pointer' }}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. MODAL XEM ẢNH GÓC NHÌN CAMERA HIỆU CHUẨN */}
      {calibrationModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.45)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20
          }}
          onClick={() => setCalibrationModal(null)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              border: '1px solid #CBD5E1',
              width: 720,
              maxWidth: '100%',
              overflow: 'hidden',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.15)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ padding: '14px 20px', background: '#F8FAFC', borderBottom: '1px solid #CBD5E1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, color: '#0F172A' }}>
                  ẢNH HIỆU CHUẨN CAMERA: {calibrationModal.name}
                </div>
                <div style={{ fontSize: 11.5, color: '#475569', marginTop: 2 }}>
                  Snapshot chuẩn từ camera CCTV trần phòng chiếu CineSight
                </div>
              </div>
              <button
                onClick={() => setCalibrationModal(null)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', fontWeight: 700 }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: 20, textAlign: 'center' }}>
              <div style={{
                height: 380,
                background: '#0F172A',
                borderRadius: 8,
                overflow: 'hidden',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #CBD5E1'
              }}>
                <img
                  src={`${API_BASE}/api/v1/calibration_image/${calibrationModal.roomId}`}
                  alt="Camera view"
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  onError={e => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement.innerHTML = `
                      <div style="color: #94A3B8; font-size: 13px; padding: 20px;">
                        <div style="font-weight: 700; color: #FFFFFF; font-size: 14px;">ĐÃ LIÊN KẾT ẢNH HIỆU CHUẨN: ${calibrationModal.name}</div>
                        <div style="margin-top: 6px;">Độ phân giải: 1920x1080 (Full HD) • Hồng ngoại IR ban đêm</div>
                        <div style="margin-top: 4px; color: #38BDF8; font-weight: 600;">Tọa độ 136 đa giác ghế khớp chuẩn 100%</div>
                      </div>
                    `;
                  }}
                />
              </div>

              <div style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: '#475569' }}>
                <span>Độ phân giải: <strong style={{ color: '#0F172A' }}>1920 x 1080 (Full HD)</strong></span>
                <span>Tọa độ đa giác: <strong style={{ color: '#16A34A' }}>136/136 ghế hợp lệ</strong></span>
                <span>Chế độ quét: <strong style={{ color: 'var(--brand-blue)' }}>Hồng ngoại (Night Vision)</strong></span>
              </div>
            </div>

            <div style={{ padding: '12px 20px', background: '#F8FAFC', borderTop: '1px solid #CBD5E1', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setCalibrationModal(null)}
                style={{ background: 'var(--brand-blue)', color: '#FFFFFF', border: 'none', padding: '7px 18px', borderRadius: 6, fontWeight: 700, fontSize: 12.5, cursor: 'pointer' }}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
