import { useState, useEffect } from 'react';
import { getRoomsConfig, getRoomSeats, getShowtimes, getTicketsList, getIncidents, analyzeRoom, triggerPreShowScan, API_BASE } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Rooms() {
  const [rooms, setRooms] = useState([]);
  const [todayShows, setTodayShows] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Interactive Modals
  const [inspectRoom, setInspectRoom] = useState(null); // Phòng đang xem sơ đồ ghế
  const [loadingSeats, setLoadingSeats] = useState(false);
  const [calibrationModal, setCalibrationModal] = useState(null); // Modal xem góc camera hiệu chuẩn
  // Modal Chạy AI Camera thực tế của phòng
  const [aiRunModal, setAiRunModal] = useState(null);
  const [aiModalShows, setAiModalShows] = useState([]);
  const [aiSelectedShowId, setAiSelectedShowId] = useState('');
  const [aiImageFile, setAiImageFile] = useState(null);
  const [aiImagePreview, setAiImagePreview] = useState(null);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState(null);
  const [aiError, setAiError] = useState(null);

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

  const renderSeatBtn = (seatId, customWidth) => {
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
          width: customWidth || 32,
          height: 24,
          background: bg,
          border: `1px solid ${border}`,
          color: text,
          borderRadius: 4,
          fontSize: customWidth ? 8 : 9.5,
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

  const subtractMinutesFromHHMM = (hhmm, mins) => {
    if (!hhmm || !hhmm.includes(':')) return '--:--';
    const [h, m] = hhmm.split(':').map(Number);
    if (Number.isNaN(h) || Number.isNaN(m)) return hhmm;
    const total = (h * 60 + m - mins + 1440) % 1440;
    const nh = String(Math.floor(total / 60)).padStart(2, '0');
    const nm = String(total % 60).padStart(2, '0');
    return `${nh}:${nm}`;
  };

  const getRoomNextCaptureInfo = (roomId) => {
    const roomShows = todayShows.filter(s => s.room_id === roomId);
    if (!roomShows.length) {
      return {
        hasShow: false,
        showId: '',
        startTime: '--:--',
        tMinus5: '--:--',
        tMinus3: '--:--',
        movieName: 'Chưa có lịch hôm nay',
      };
    }
    const now = new Date();
    const nowMin = now.getHours() * 60 + now.getMinutes();
    const upcoming =
      roomShows.find(s => {
        const st = s.start_time || (s.show_id?.includes('T') ? s.show_id.split('T')[1] : '');
        if (!st || !st.includes(':')) return false;
        const [sh, sm] = st.split(':').map(Number);
        return sh * 60 + sm >= nowMin - 5;
      }) || roomShows[0];

    const startTime = upcoming.start_time || (upcoming.show_id?.includes('T') ? upcoming.show_id.split('T')[1] : '19:30');
    return {
      hasShow: true,
      showId: upcoming.show_id,
      startTime,
      tMinus5: subtractMinutesFromHHMM(startTime, 5),
      tMinus3: subtractMinutesFromHHMM(startTime, 3),
      movieName: upcoming.movie_name || upcoming.title_vi || 'Suất chiếu',
    };
  };

  // Mở modal Chạy AI cho một phòng cụ thể (có thể tự động chạy giả lập T-3 ngay nếu truyền autoOffset)
  const handleOpenAiModal = async (roomId, roomDisplayName, autoOffset = null) => {
    setAiRunModal({ roomId, name: roomDisplayName });
    setAiAnalysisResult(null);
    setAiError(null);
    setAiImageFile(null);
    setAiImagePreview(null);
    try {
      const today = new Date().toISOString().slice(0, 10);
      let shows = await getShowtimes(roomId, today).catch(() => []);
      if (!shows || shows.length === 0) {
        shows = await getShowtimes(roomId).catch(() => []);
      }
      const list = shows || [];
      setAiModalShows(list);
      let chosenShowId = '';
      if (list.length > 0) {
        const nextInfo = getRoomNextCaptureInfo(roomId);
        const matched = list.find(s => s.show_id === nextInfo.showId) || list[0];
        chosenShowId = matched.show_id;
        setAiSelectedShowId(chosenShowId);
      } else {
        setAiSelectedShowId('');
      }
      if (autoOffset !== null && chosenShowId) {
        await handleTriggerTimeWarp(roomId, chosenShowId, autoOffset);
      }
    } catch (e) {
      console.error('Lỗi tải danh sách suất chiếu cho AI modal:', e);
    }
  };

  // Chế độ 2: Giả lập tua đồng hồ đến mốc T-5 hoặc T-3 phút trước giờ chiếu
  const handleTriggerTimeWarp = async (roomIdOverride = null, showIdOverride = null, offsetMinutes = -3) => {
    const targetRoom = roomIdOverride || aiRunModal?.roomId;
    const targetShow = showIdOverride || aiSelectedShowId;
    if (!targetRoom) return;
    if (!targetShow) {
      setAiError('Vui lòng chọn suất chiếu trước khi kích hoạt mốc T-3 / T-5.');
      return;
    }
    setAiAnalyzing(true);
    setAiError(null);
    try {
      const res = await triggerPreShowScan(targetRoom, targetShow, offsetMinutes);
      setAiAnalysisResult(res);
    } catch (e) {
      setAiError(e.response?.data?.error || e.message || 'Lỗi khi kích hoạt bộ lập lịch AI.');
    } finally {
      setAiAnalyzing(false);
    }
  };

  // Chế độ 3: Thực thi phân tích ảnh camera thủ công (Manual Override)
  const handleExecuteAi = async () => {
    if (!aiRunModal) return;
    if (!aiSelectedShowId) {
      setAiError('Vui lòng chọn suất chiếu trước khi chạy phân tích AI.');
      return;
    }
    if (!aiImageFile) {
      setAiError('Vui lòng chọn file ảnh snapshot từ camera CCTV phòng chiếu.');
      return;
    }
    setAiAnalyzing(true);
    setAiError(null);
    try {
      const res = await analyzeRoom(aiRunModal.roomId, aiSelectedShowId, aiImageFile, 'MANUAL_OVERRIDE');
      setAiAnalysisResult(res);
    } catch (e) {
      setAiError(e.response?.data?.error || e.message || 'Lỗi khi gọi AI phân tích.');
    } finally {
      setAiAnalyzing(false);
    }
  };

  const getRoomDisplayName = (roomId) => {
    switch (roomId) {
      case 'room1': return 'Phòng chiếu số 1';
      case 'room2': return 'Phòng chiếu số 2';
      case 'room3': return 'Phòng chiếu số 3';
      case 'room4': return 'Phòng chiếu số 4';
      default: return 'Phòng chiếu số 1';
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
              {/* PHẦN THÔNG TIN THỰC TẾ CỦA PHÒNG */}
              <div>
                {/* Tiêu đề phòng & Trạng thái hoạt động */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 800, color: '#0F172A', letterSpacing: '-0.3px' }}>
                      {roomDisplayName}
                    </div>
                    <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>
                      {roomObj.total_seats || 136} ghế • {roomObj.rows ? `${roomObj.rows.length} hàng (${roomObj.rows[0]} - ${roomObj.rows[roomObj.rows.length - 1]})` : (rid === 'room3' ? '10 hàng (A - J)' : '12 hàng (A - L)')}
                    </div>
                  </div>

                  <span style={{
                    fontSize: 11.5,
                    fontWeight: 700,
                    padding: '3px 10px',
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

                {/* Thông tin thật: Lịch chiếu trong ngày & Cấu hình AI */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: '10px 16px',
                  padding: '12px 14px',
                  background: '#F8FAFC',
                  borderRadius: 6,
                  border: '1px solid #E2E8F0',
                  marginBottom: 14
                }}>
                  <div>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
                      Lịch chiếu hôm nay
                    </span>
                    <strong style={{ fontSize: 13, color: '#0F172A' }}>
                      {todayShows.filter(s => s.room_id === rid).length} suất chiếu
                    </strong>
                  </div>

                  <div>
                    <span style={{ fontSize: 11, color: '#64748B', fontWeight: 600, textTransform: 'uppercase', display: 'block', marginBottom: 2 }}>
                      Dữ liệu ghế AI
                    </span>
                    <strong style={{ fontSize: 13, color: roomObj.is_calibrated ? '#15803D' : '#D97706' }}>
                      {roomObj.is_calibrated ? 'Đã hiệu chuẩn' : 'Chưa có dữ liệu'}
                    </strong>
                  </div>
                </div>
              </div>

              {/* Các thao tác (3 nút gọn gàng, rõ ràng) */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => handleOpenSeatmap({ room_id: rid, name: roomDisplayName, total_seats: roomObj.total_seats || 136 })}
                  style={{
                    flex: 1,
                    height: 34,
                    background: '#FFFFFF',
                    border: '1px solid #CBD5E1',
                    color: '#0F172A',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F1F5F9'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#FFFFFF'; }}
                >
                  Sơ đồ ghế 2D
                </button>

                <button
                  onClick={() => setCalibrationModal({ roomId: rid, name: roomDisplayName })}
                  style={{
                    flex: 1,
                    height: 34,
                    background: '#FFFFFF',
                    border: '1px solid #CBD5E1',
                    color: '#0F172A',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#F1F5F9'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = '#FFFFFF'; }}
                >
                  Ảnh Camera
                </button>

                <button
                  onClick={() => handleOpenAiModal(rid, roomDisplayName, null)}
                  style={{
                    flex: 1.1,
                    height: 34,
                    background: 'var(--brand-blue)',
                    border: '1px solid #1D4ED8',
                    color: '#FFFFFF',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                  onMouseEnter={e => { e.currentTarget.style.backgroundColor = '#1D4ED8'; }}
                  onMouseLeave={e => { e.currentTarget.style.backgroundColor = 'var(--brand-blue)'; }}
                >
                  Đối soát AI
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
                  SƠ ĐỒ GHẾ 2D: {inspectRoom.name} ({inspectRoom.total_seats || (inspectRoom.room_id?.includes('3') ? 132 : 136)} GHẾ)
                </div>
                <div style={{ fontSize: 11, color: '#475569', marginTop: 1 }}>
                  {inspectRoom.room_id?.includes('3') ? 'Hàng A - J (132 ghế chuẩn đối chiếu camera an ninh)' : 'Hàng A - L (136 ghế chuẩn đối chiếu camera an ninh)'} • Nhấn vào ghế để đổi trạng thái
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
            <div style={{ padding: '10px 16px 14px', textAlign: 'center', overflow: 'hidden' }}>
              {/* CHÚ THÍCH MÀU SẮC GHẾ SOC SẮC NÉT Ở TRÊN ĐẦU */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: 16,
                marginBottom: 10,
                padding: '6px 12px',
                background: '#F8FAFC',
                borderRadius: 6,
                border: '1px solid #E2E8F0',
                fontSize: 11.5,
                fontWeight: 600,
                color: '#334155'
              }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 11, height: 11, background: '#1E293B', border: '1px solid #334155', borderRadius: 2 }} />
                  Trống
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 11, height: 11, background: '#2563EB', border: '1px solid #1D4ED8', borderRadius: 2 }} />
                  Đã có người ({occupiedSeats.size})
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 11, height: 11, background: '#F59E0B', border: '1px solid #D97706', borderRadius: 2 }} />
                  Trục trặc ({brokenSeats.size})
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 11, height: 11, background: '#EF4444', border: '1px solid #DC2626', borderRadius: 2 }} />
                  Cảnh báo AI ({warningSeats.size})
                </span>
              </div>

              {/* THANH MÀN HÌNH CHIẾU TINH TẾ, KHÔNG GLOW LÒE LOẸT */}
              <div style={{
                height: 4,
                background: 'var(--brand-blue)',
                borderRadius: 2,
                width: '60%',
                margin: '0 auto 6px auto',
                opacity: 0.9
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

                  {inspectRoom.room_id?.includes('3') ? (
                    <>
                      {/* HÀNG A: 10 ghế (A10 - A1) */}
                      <div style={{ display: 'flex', gap: 3, alignItems: 'center', width: 620, justifyContent: 'center' }}>
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                        <span style={{ width: 28 * 4 }} />
                        {Array.from({ length: 10 }, (_, idx) => renderSeatBtn(`A${10 - idx}`, 28))}
                        <span style={{ width: 28 * 4 }} />
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                      </div>

                      {/* CÁC HÀNG B ĐẾN I: 13 ghế mỗi hàng (B13-B1 ... I13-I1) */}
                      {['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I'].map(r => (
                        <div key={r} style={{ display: 'flex', gap: 3, alignItems: 'center', width: 620, justifyContent: 'center' }}>
                          <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                          <span style={{ width: 28 * 2 }} />
                          {Array.from({ length: 13 }, (_, idx) => renderSeatBtn(`${r}${13 - idx}`, 28))}
                          <span style={{ width: 28 * 3 }} />
                          <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                        </div>
                      ))}

                      {/* HÀNG J: 18 ghế liền mạch J18 - J1 */}
                      <div style={{ display: 'flex', gap: 3, alignItems: 'center', width: 620, justifyContent: 'center' }}>
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>J</span>
                        {Array.from({ length: 18 }, (_, idx) => renderSeatBtn(`J${18 - idx}`, 28))}
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>J</span>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* HÀNG A: 8 ghế (A8 - A1) căn thẳng trên B10 - B3 */}
                      <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        {Array.from({ length: 8 }, (_, idx) => renderSeatBtn(`A${8 - idx}`))}
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>A</span>
                      </div>

                      {/* CÁC HÀNG B ĐẾN J: 11 ghế mỗi hàng (B11-B1 ... J11-J1) */}
                      {['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'].map(r => (
                        <div key={r} style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                          <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                          <span style={{ width: 32 }} />
                          {Array.from({ length: 11 }, (_, idx) => renderSeatBtn(`${r}${11 - idx}`))}
                          <span style={{ width: 32 }} />
                          <span style={{ width: 32 }} />
                          <span style={{ width: 32 }} />
                          <span style={{ width: 32 }} />
                          <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>{r}</span>
                        </div>
                      ))}

                      {/* HÀNG K: K13 - K3, 2 ô trống thẳng hàng L4-L3 (BỎ LỐI ĐI), K2, K1 */}
                      <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>K</span>
                        <span style={{ width: 32 }} />
                        {Array.from({ length: 11 }, (_, idx) => renderSeatBtn(`K${13 - idx}`))}
                        <span style={{ width: 32 }} />
                        <span style={{ width: 32 }} />
                        {renderSeatBtn('K2')}
                        {renderSeatBtn('K1')}
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>K</span>
                      </div>

                      {/* HÀNG L: 16 ghế liền mạch L16 - L1 */}
                      <div style={{ display: 'flex', gap: 4, alignItems: 'center', width: 620 }}>
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>L</span>
                        {Array.from({ length: 16 }, (_, idx) => renderSeatBtn(`L${16 - idx}`))}
                        <span style={{ width: 20, fontSize: 10.5, fontWeight: 700, color: '#64748B', textAlign: 'center' }}>L</span>
                      </div>
                    </>
                  )}
                </div>
              )}


            </div>

            {/* Footer Modal */}
            <div style={{ padding: '10px 18px', background: '#F8FAFC', borderTop: '1px solid #CBD5E1', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
              <button
                onClick={() => setInspectRoom(null)}
                style={{ background: 'var(--brand-blue)', color: '#FFFFFF', border: 'none', padding: '6px 18px', borderRadius: 6, fontWeight: 700, fontSize: 12.5, cursor: 'pointer' }}
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
            <div style={{ padding: '12px 18px', background: '#F8FAFC', borderBottom: '1px solid #CBD5E1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, color: '#0F172A' }}>
                  ẢNH HIỆU CHUẨN CAMERA: {calibrationModal.name}
                </div>
                <div style={{ fontSize: 11.5, color: '#64748B', marginTop: 2 }}>
                  Ảnh mẫu góc nhìn camera dùng để định vị tọa độ ghế của phòng
                </div>
              </div>
              <button
                onClick={() => setCalibrationModal(null)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', fontWeight: 700 }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: 16, textAlign: 'center' }}>
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
                        <div style="font-weight: 700; color: #FFFFFF; font-size: 14px;">Chưa có ảnh hiệu chuẩn</div>
                        <div style="margin-top: 6px;">Không tìm thấy tệp ảnh hiệu chuẩn của ${calibrationModal.name} trên máy chủ.</div>
                      </div>
                    `;
                  }}
                />
              </div>

              <div style={{ marginTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: '#475569' }}>
                <span>Phòng chiếu: <strong style={{ color: '#0F172A' }}>{calibrationModal.name}</strong></span>
                <span>Mã phòng: <strong style={{ color: '#0F172A' }}>{calibrationModal.roomId}</strong></span>
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

      {/* 5. MODAL CHẠY PHÂN TÍCH CAMERA AI THẬT */}
      {aiRunModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.5)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 20
          }}
          onClick={() => setAiRunModal(null)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              border: '1px solid #CBD5E1',
              width: 580,
              maxWidth: '96vw',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.15)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header Modal */}
            <div style={{ padding: '12px 20px', background: '#F8FAFC', borderBottom: '1px solid #CBD5E1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, color: '#0F172A' }}>
                  ĐỐI SOÁT CAMERA AI: {aiRunModal.name}
                </div>
                <div style={{ fontSize: 11.5, color: '#64748B', marginTop: 2 }}>
                  So khớp vị trí người ngồi từ camera với danh sách vé đã quét
                </div>
              </div>
              <button
                onClick={() => setAiRunModal(null)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer', fontWeight: 700 }}
              >
                ✕
              </button>
            </div>

            {/* Thân Modal */}
            <div style={{ padding: '16px 20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Chọn Suất Chiếu */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 6 }}>
                  1. CHỌN SUẤT CHIẾU ĐỐI SOÁT
                </label>
                <select
                  value={aiSelectedShowId}
                  onChange={e => setAiSelectedShowId(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 6,
                    border: '1px solid #CBD5E1',
                    background: '#FFFFFF',
                    fontSize: 13,
                    fontWeight: 600,
                    color: '#0F172A',
                    outline: 'none'
                  }}
                >
                  {aiModalShows.length === 0 ? (
                    <option value="">Không có suất chiếu hôm nay</option>
                  ) : (
                    aiModalShows.map(s => (
                      <option key={s.show_id} value={s.show_id}>
                        {s.start_time || s.show_id.split('T').pop()} - {s.movie_name || s.title_vi || 'Phim'} ({s.show_id})
                      </option>
                    ))
                  )}
                </select>
              </div>

              {/* Kích hoạt đối soát theo mốc T-5 / T-3 */}
              <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '12px 14px' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#0F172A', marginBottom: 4 }}>
                  2A. QUÉT THEO MỐC LỊCH CHIẾU
                </div>
                <div style={{ fontSize: 11.5, color: '#64748B', marginBottom: 8 }}>
                  Kích hoạt trích xuất camera và đối soát theo mốc trước giờ chiếu:
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="button"
                    disabled={aiAnalyzing || !aiSelectedShowId}
                    onClick={() => handleTriggerTimeWarp(aiRunModal.roomId, aiSelectedShowId, -5)}
                    style={{
                      flex: 1,
                      padding: '8px 10px',
                      background: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      color: '#0F172A',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: aiAnalyzing || !aiSelectedShowId ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Mốc T-5 phút
                  </button>
                  <button
                    type="button"
                    disabled={aiAnalyzing || !aiSelectedShowId}
                    onClick={() => handleTriggerTimeWarp(aiRunModal.roomId, aiSelectedShowId, -3)}
                    style={{
                      flex: 1,
                      padding: '8px 10px',
                      background: '#16A34A',
                      border: '1px solid #15803D',
                      color: '#FFFFFF',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: aiAnalyzing || !aiSelectedShowId ? 'not-allowed' : 'pointer',
                    }}
                  >
                    Mốc T-3 phút
                  </button>
                </div>
              </div>

              {/* Nạp ảnh CCTV snapshot (Chế độ 3: Manual Override) */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 6 }}>
                  2B. HOẶC TẢI LÊN ẢNH CHỤP CAMERA THỦ CÔNG
                </label>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <label
                    style={{
                      background: '#EFF6FF',
                      border: '1px solid #BFDBFE',
                      color: '#2563EB',
                      padding: '8px 16px',
                      borderRadius: 6,
                      fontSize: 12.5,
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      whiteSpace: 'nowrap'
                    }}
                  >
                    📁 Chọn ảnh từ máy...
                    <input
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={e => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setAiImageFile(file);
                          setAiImagePreview(URL.createObjectURL(file));
                          setAiAnalysisResult(null);
                          setAiError(null);
                        }
                      }}
                    />
                  </label>
                  <span style={{ fontSize: 12, color: aiImageFile ? '#0F172A' : '#94A3B8', fontWeight: aiImageFile ? 600 : 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {aiImageFile ? aiImageFile.name : 'Chưa chọn tệp ảnh (VD: CCTV_ROOM4_TEST_FRAME.jpg)'}
                  </span>
                </div>

                {/* Preview ảnh nhỏ */}
                {aiImagePreview && (
                  <div style={{ marginTop: 10, height: 160, background: '#0F172A', borderRadius: 6, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #CBD5E1' }}>
                    <img src={aiImagePreview} alt="Preview" style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }} />
                  </div>
                )}
              </div>

              {/* Thông báo lỗi nếu có */}
              {aiError && (
                <div style={{ padding: '8px 12px', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 6, color: '#DC2626', fontSize: 12, fontWeight: 600 }}>
                  ⚠️ {aiError}
                </div>
              )}

              {/* Nút thực hiện chạy AI */}
              <button
                onClick={handleExecuteAi}
                disabled={aiAnalyzing || !aiImageFile}
                style={{
                  width: '100%',
                  padding: '10px 0',
                  background: aiAnalyzing || !aiImageFile ? '#94A3B8' : '#2563EB',
                  border: 'none',
                  borderRadius: 6,
                  color: '#FFFFFF',
                  fontSize: 13,
                  fontWeight: 800,
                  cursor: aiAnalyzing || !aiImageFile ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  boxShadow: '0 2px 4px rgba(37, 99, 235, 0.2)'
                }}
              >
                {aiAnalyzing ? 'Đang phân tích hình ảnh...' : 'Bắt đầu phân tích AI'}
              </button>

              {/* KẾT QUẢ PHÂN TÍCH */}
              {aiAnalysisResult && (
                <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <div style={{ fontSize: 13, fontWeight: 800, color: '#0F172A', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 6 }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>KẾT QUẢ ĐỐI SOÁT AI:</span>
                      <span style={{
                        fontSize: 11,
                        padding: '2px 8px',
                        borderRadius: 999,
                        background: aiAnalysisResult.summary?.trigger_source?.startsWith('AUTO_') ? '#DCFCE7' : '#DBEAFE',
                        color: aiAnalysisResult.summary?.trigger_source?.startsWith('AUTO_') ? '#15803D' : '#1D4ED8',
                        fontWeight: 700,
                      }}>
                        {aiAnalysisResult.summary?.trigger_source || 'MANUAL'}
                      </span>
                    </span>
                    <span style={{ color: '#2563EB' }}>Phát hiện {aiAnalysisResult.summary?.total_detected_people || 0} người</span>
                  </div>
                  {aiAnalysisResult.scheduler_simulation?.simulated_clock && (
                    <div style={{ fontSize: 11.5, color: '#15803D', fontWeight: 600 }}>
                      ⏱️ Đồng hồ mô phỏng: {aiAnalysisResult.scheduler_simulation.simulated_clock} • Nguồn ảnh: {aiAnalysisResult.scheduler_simulation.snapshot_file}
                    </div>
                  )}
                  {aiAnalysisResult.summary?.auto_resolved_alerts > 0 && (
                    <div style={{ fontSize: 11.5, color: '#0F766E', background: '#F0FDFA', border: '1px solid #99F6E4', padding: '6px 10px', borderRadius: 6, fontWeight: 600 }}>
                      🔄 Đã tự động gỡ {aiAnalysisResult.summary.auto_resolved_alerts} cảnh báo cũ của lần chụp trước (khách đã vào ngồi đúng ghế).
                    </div>
                  )}

                  {(aiAnalysisResult.summary?.no_tickets_warning === true || !aiAnalysisResult.summary?.tap_A_from_app?.length) && (
                    <div style={{ fontSize: 11.5, color: '#9A3412', background: '#FFF7ED', border: '1px solid #FDBA74', padding: '8px 10px', borderRadius: 6, fontWeight: 600, lineHeight: 1.45 }}>
                      ⚠️ Lưu ý: Suất chiếu này chưa có vé nào được quét từ App (Tập A = 0). Để kiểm tra tính năng phát hiện 'Vắng khách / Ghế trống có vé' (Missing Guest), vui lòng quét vé QR cho suất chiếu này trước khi chạy AI.
                    </div>
                  )}

                  {/* Tập A & Tập B */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                    <div style={{ background: '#FFFFFF', padding: '8px 10px', borderRadius: 6, border: '1px solid #E2E8F0' }}>
                      <div style={{ color: '#64748B', fontWeight: 600, marginBottom: 2 }}>Tập A (Vé đã soát):</div>
                      <div style={{ fontWeight: 700, color: '#16A34A' }}>
                        {aiAnalysisResult.summary?.tap_A_from_app?.length > 0
                          ? aiAnalysisResult.summary.tap_A_from_app.join(', ')
                          : 'Chưa có vé nào'}
                      </div>
                    </div>
                    <div style={{ background: '#FFFFFF', padding: '8px 10px', borderRadius: 6, border: '1px solid #E2E8F0' }}>
                      <div style={{ color: '#64748B', fontWeight: 600, marginBottom: 2 }}>Tập B (Camera thấy ngồi):</div>
                      <div style={{ fontWeight: 700, color: '#2563EB' }}>
                        {aiAnalysisResult.summary?.tap_B_from_camera?.length > 0
                          ? aiAnalysisResult.summary.tap_B_from_camera.join(', ')
                          : 'Không phát hiện người'}
                      </div>
                    </div>
                  </div>

                  {/* Chi tiết cảnh báo vi phạm */}
                  {aiAnalysisResult.alerts?.illegal_occupants?.length > 0 && (
                    <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
                      <strong style={{ color: '#DC2626' }}>Ngồi sai ghế / Chưa có vé: </strong>
                      <span style={{ color: '#991B1B', fontWeight: 700 }}>
                        {aiAnalysisResult.alerts.illegal_occupants.join(', ')}
                      </span>
                    </div>
                  )}

                  {aiAnalysisResult.alerts?.missing_guests?.length > 0 && (
                    <div style={{ background: '#FEFCE8', border: '1px solid #FEF08A', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
                      <strong style={{ color: '#CA8A04' }}>Vé đã soát nhưng chưa thấy khách ngồi: </strong>
                      <span style={{ color: '#854D0E', fontWeight: 700 }}>
                        {aiAnalysisResult.alerts.missing_guests.join(', ')}
                      </span>
                    </div>
                  )}

                  {(!aiAnalysisResult.alerts?.illegal_occupants?.length && !aiAnalysisResult.alerts?.missing_guests?.length) && (
                    <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: 6, padding: '8px 12px', color: '#16A34A', fontSize: 12, fontWeight: 700 }}>
                      ✅ TẤT CẢ KHỚP 100%! Vị trí người ngồi khớp chính xác với vé đã soát.
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer Modal */}
            <div style={{ padding: '10px 20px', background: '#F8FAFC', borderTop: '1px solid #CBD5E1', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setAiRunModal(null)}
                style={{ background: '#FFFFFF', border: '1px solid #CBD5E1', color: '#0F172A', padding: '6px 16px', borderRadius: 6, fontWeight: 700, fontSize: 12.5, cursor: 'pointer' }}
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
