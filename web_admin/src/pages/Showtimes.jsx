import { useState, useEffect, useMemo } from 'react';
import { getShowtimes, getMovies } from '../api/cineSightApi';
import '../styles/dashboard.css';

// Bảng màu trực quan, rực rỡ, độ tương phản cao cho Light Mode
const MOVIE_COLOR_PALETTES = [
  { bg: 'linear-gradient(135deg, #0284c7, #0369a1)', border: '#0284c7', badge: '#075985', text: '#ffffff' }, // Sky/Blue
  { bg: 'linear-gradient(135deg, #ea580c, #c2410c)', border: '#ea580c', badge: '#9a3412', text: '#ffffff' }, // Orange
  { bg: 'linear-gradient(135deg, #16a34a, #15803d)', border: '#16a34a', badge: '#166534', text: '#ffffff' }, // Green
  { bg: 'linear-gradient(135deg, #7c3aed, #6d28d9)', border: '#7c3aed', badge: '#5b21b6', text: '#ffffff' }, // Purple
  { bg: 'linear-gradient(135deg, #e11d48, #be123c)', border: '#e11d48', badge: '#9f1239', text: '#ffffff' }, // Rose
  { bg: 'linear-gradient(135deg, #0d9488, #0f766e)', border: '#0d9488', badge: '#115e59', text: '#ffffff' }, // Teal
  { bg: 'linear-gradient(135deg, #d97706, #b45309)', border: '#d97706', badge: '#92400e', text: '#ffffff' }, // Amber
  { bg: 'linear-gradient(135deg, #4f46e5, #4338ca)', border: '#4f46e5', badge: '#3730a3', text: '#ffffff' }, // Indigo
];

function getMovieColor(movieName = '') {
  let hash = 0;
  for (let i = 0; i < movieName.length; i++) {
    hash = (hash << 5) - hash + movieName.charCodeAt(i);
    hash |= 0;
  }
  const idx = Math.abs(hash) % MOVIE_COLOR_PALETTES.length;
  return MOVIE_COLOR_PALETTES[idx];
}

// Chuyển "HH:mm" thành số phút từ 00:00
function timeToMinutes(timeStr = '') {
  if (!timeStr || !timeStr.includes(':')) return 0;
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
}

// Chuyển phút thành "HH:mm"
function minutesToTime(totalMinutes) {
  const norm = ((totalMinutes % 1440) + 1440) % 1440;
  const h = Math.floor(norm / 60);
  const m = norm % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

// Lấy ngày hiện tại chuẩn ISO (yyyy-MM-dd) theo múi giờ địa phương
function getTodayIso(now = new Date()) {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// Xác định trạng thái của suất chiếu: 'past' (đã chiếu), 'ongoing' (đang chiếu), 'upcoming' (sắp chiếu)
function getShowStatus(show, selectedDate, now = new Date()) {
  const todayIso = getTodayIso(now);

  if (selectedDate < todayIso) return 'past';
  if (selectedDate > todayIso) return 'upcoming';

  const currentMin = now.getHours() * 60 + now.getMinutes();
  const startMin = timeToMinutes(show.start_time);
  const duration = Number(show.duration_minutes) || 100;
  const endMin = startMin + duration;

  if (currentMin > endMin) return 'past';
  if (currentMin >= startMin && currentMin <= endMin) return 'ongoing';
  return 'upcoming';
}

export default function Showtimes({ onNavigateToTickets }) {
  // Đồng hồ thời gian thực tự động cập nhật
  const [currentTime, setCurrentTime] = useState(() => new Date());
  const todayIso = useMemo(() => getTodayIso(currentTime), [currentTime]);
  
  // Ngày được chọn mặc định luôn là ngày hiện tại (Realtime)
  const [selectedDate, setSelectedDate] = useState(getTodayIso);
  const isToday = selectedDate === todayIso;

  const [viewMode, setViewMode] = useState('timeline'); // 'timeline' hoặc 'catalog'
  const [showtimes, setShowtimes] = useState([]);
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Tự động cập nhật đồng hồ mỗi 30 giây để cập nhật trạng thái suất chiếu realtime
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 30000);
    return () => clearInterval(timer);
  }, []);

  // Quản lý Modal & Dialog
  const [showInfoDialog, setShowInfoDialog] = useState(false); // Dialog nhỏ thông số vận hành
  const [editingShow, setEditingShow] = useState(null);       // Modal điều chỉnh suất chiếu
  
  // Drag & Drop State
  const [draggedShow, setDraggedShow] = useState(null);
  const [dragOverRoom, setDragOverRoom] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  // Form State khi chỉnh sửa suất chiếu trong modal
  const [editForm, setEditForm] = useState({
    room_id: 'room1',
    start_time: '08:30',
    duration_minutes: 100,
    reason: 'Rút gọn outro / credits kết thúc phim',
  });

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Danh sách 7 ngày linh hoạt tự động tính theo ngày hiện tại
  const quickDates = useMemo(() => {
    const list = [];
    const today = new Date(currentTime);
    // Bắt đầu từ 2 ngày trước hôm nay (-2) đến 4 ngày sau (+4) tạo dải 7 ngày cân đối quanh hôm nay
    for (let i = -2; i < 5; i++) {
      const dt = new Date(today);
      dt.setDate(today.getDate() + i);
      const year = dt.getFullYear();
      const month = String(dt.getMonth() + 1).padStart(2, '0');
      const day = String(dt.getDate()).padStart(2, '0');
      const iso = `${year}-${month}-${day}`;
      let prefix = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'][dt.getDay()];
      if (i === 0) prefix = 'Hôm nay';
      else if (i === -1) prefix = 'Hôm qua';
      list.push({ date: iso, label: `${prefix} (${day}/${month})`, isToday: i === 0 });
    }
    return list;
  }, [currentTime]);



  // Tải dữ liệu từ backend
  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      try {
        const [showsData, moviesData] = await Promise.all([
          getShowtimes(null, selectedDate),
          getMovies(true),
        ]);
        if (isMounted) {
          setShowtimes(showsData);
          setMovies(moviesData);
        }
      } catch (err) {
        console.error('Lỗi tải dữ liệu lịch chiếu:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, [selectedDate]);

  // Phân nhóm suất chiếu theo 4 phòng
  const showsByRoom = useMemo(() => {
    const map = {
      room1: { label: 'Phòng chiếu 1', shows: [] },
      room2: { label: 'Phòng chiếu 2', shows: [] },
      room3: { label: 'Phòng chiếu 3', shows: [] },
      room4: { label: 'Phòng chiếu 4', shows: [] },
    };

    showtimes.forEach(s => {
      const rid = s.room_id || 'room1';
      if (!map[rid]) {
        map[rid] = { label: s.room_name || rid, shows: [] };
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const mName = (s.movie_name || s.movie_title || '').toLowerCase();
        if (!mName.includes(q)) return;
      }
      map[rid].shows.push(s);
    });

    Object.keys(map).forEach(rid => {
      map[rid].shows.sort((a, b) => timeToMinutes(a.start_time) - timeToMinutes(b.start_time));
    });

    return map;
  }, [showtimes, searchQuery]);

  // Thống kê nhanh
  const stats = useMemo(() => {
    const totalShows = showtimes.length;
    const uniqueMovies = new Set(showtimes.map(s => s.movie_id)).size;
    return { totalShows, uniqueMovies };
  }, [showtimes]);

  // Cấu hình Timeline (08:00 đến 24:00 = 16 tiếng = 960 phút)
  const TIMELINE_START_HOUR = 8;
  const TIMELINE_END_HOUR = 24;
  const TIMELINE_TOTAL_MINUTES = (TIMELINE_END_HOUR - TIMELINE_START_HOUR) * 60; // 960 phút
  const hoursArray = Array.from({ length: TIMELINE_END_HOUR - TIMELINE_START_HOUR + 1 }, (_, i) => TIMELINE_START_HOUR + i);

  // Số phút hiện tại trong ngày và chuỗi hiển thị giờ thực tế
  const nowMin = currentTime.getHours() * 60 + currentTime.getMinutes();
  const currentTimeStr = `${String(currentTime.getHours()).padStart(2, '0')}:${String(currentTime.getMinutes()).padStart(2, '0')}`;

  // Mở modal chỉnh sửa suất chiếu
  const handleOpenEditModal = (show) => {
    setEditingShow(show);
    setEditForm({
      room_id: show.room_id || 'room1',
      start_time: show.start_time || '08:30',
      duration_minutes: show.duration_minutes || 100,
      reason: 'Rút gọn outro / credits kết thúc phim',
    });
  };

  // Tính giờ kết thúc dự kiến theo giờ bắt đầu và thời lượng
  const calculatedEndTime = useMemo(() => {
    const startMin = timeToMinutes(editForm.start_time);
    const endMin = startMin + Number(editForm.duration_minutes || 0);
    return minutesToTime(endMin);
  }, [editForm.start_time, editForm.duration_minutes]);

  // Lưu chỉnh sửa suất chiếu
  const handleSaveShowEdit = (e) => {
    e.preventDefault();
    if (!editingShow) return;

    const newStartMin = timeToMinutes(editForm.start_time);
    const duration = Number(editForm.duration_minutes);
    const newEndMin = newStartMin + duration;
    const newEndTime = minutesToTime(newEndMin);

    setShowtimes(prev => prev.map(s => {
      if (s.show_id === editingShow.show_id) {
        return {
          ...s,
          room_id: editForm.room_id,
          start_time: editForm.start_time,
          duration_minutes: duration,
          end_time: newEndTime,
          edited_reason: editForm.reason,
          is_manually_edited: true,
        };
      }
      return s;
    }));

    const roomLabel = editForm.room_id === 'room1' ? 'Phòng chiếu 1' : editForm.room_id === 'room2' ? 'Phòng chiếu 2' : editForm.room_id === 'room3' ? 'Phòng chiếu 3' : 'Phòng chiếu 4';
    showToast(`Đã cập nhật suất "${editingShow.movie_name}": ${editForm.start_time} - ${newEndTime} (${duration}p) tại ${roomLabel}`);
    setEditingShow(null);
  };

  // Xóa suất chiếu khỏi ngày
  const handleDeleteShow = (showId) => {
    if (window.confirm('Bạn có chắc chắn muốn huỷ suất chiếu này không?')) {
      setShowtimes(prev => prev.filter(s => s.show_id !== showId));
      showToast('Đã huỷ suất chiếu thành công');
      setEditingShow(null);
    }
  };

  // ===================== DRAG & DROP LOGIC =====================
  const handleDragStart = (e, show) => {
    setDraggedShow(show);
    e.dataTransfer.setData('text/plain', show.show_id);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOverTrack = (e, roomId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (dragOverRoom !== roomId) {
      setDragOverRoom(roomId);
    }
  };

  const handleDragLeaveTrack = (e, roomId) => {
    if (dragOverRoom === roomId) {
      setDragOverRoom(null);
    }
  };

  const handleDropOnTrack = (e, targetRoomId) => {
    e.preventDefault();
    setDragOverRoom(null);
    if (!draggedShow) return;

    const trackElement = e.currentTarget;
    const rect = trackElement.getBoundingClientRect();
    const offsetX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const ratio = offsetX / rect.width;

    // Tính số phút tương ứng và làm tròn theo bội số 5 phút
    const rawMinutes = TIMELINE_START_HOUR * 60 + ratio * TIMELINE_TOTAL_MINUTES;
    const snappedMinutes = Math.max(
      TIMELINE_START_HOUR * 60,
      Math.min(TIMELINE_END_HOUR * 60 - 30, Math.round(rawMinutes / 5) * 5)
    );

    const newStartTime = minutesToTime(snappedMinutes);
    const duration = draggedShow.duration_minutes || 100;
    const newEndTime = minutesToTime(snappedMinutes + duration);

    setShowtimes(prev => prev.map(s => {
      if (s.show_id === draggedShow.show_id) {
        return {
          ...s,
          room_id: targetRoomId,
          start_time: newStartTime,
          end_time: newEndTime,
          is_manually_edited: true,
        };
      }
      return s;
    }));

    const roomName = targetRoomId === 'room1' ? 'Phòng chiếu 1' : targetRoomId === 'room2' ? 'Phòng chiếu 2' : targetRoomId === 'room3' ? 'Phòng chiếu 3' : 'Phòng chiếu 4';
    showToast(`Đã chuyển suất "${draggedShow.movie_name}" sang ${roomName} lúc ${newStartTime}`);
    setDraggedShow(null);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      padding: '12px 16px',
      boxSizing: 'border-box',
      gap: 10,
      background: 'var(--bg-dark)',
      color: 'var(--text-main)',
      overflow: 'hidden' // Khóa cuộn trang chính để toàn bộ 4 phòng nằm trọn trong viewport
    }}>
      {/* TOAST THÔNG BÁO TÁC VỤ KÉO THẢ & CHỈNH SỬA */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          top: 20,
          right: 24,
          background: '#0F172A',
          color: '#FFFFFF',
          padding: '10px 18px',
          borderRadius: 8,
          fontSize: 13,
          fontWeight: 600,
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
          zIndex: 10000,
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          border: '1px solid #334155',
          animation: 'flash-bg 0.3s ease'
        }}>
          {toastMessage}
        </div>
      )}

      {/* 1. HEADER TINH GỌN (COMPACT BAR) */}
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        background: '#FFFFFF',
        padding: '8px 16px',
        borderRadius: 8,
        border: '1px solid #E2E8F0',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--brand-blue)', letterSpacing: '0.5px' }}>
            ĐIỀU ĐỘ LỊCH CHIẾU PHIM (CINESIGHT TMS)
          </div>
          <span style={{ fontSize: 12, color: '#64748B', background: '#F1F5F9', padding: '3px 8px', borderRadius: 6 }}>
            Light Mode • Trực quan 4 Phòng chiếu
          </span>
        </div>

        {/* CỤM CHỈ SỐ NHANH THAY THẾ CHO 4 WIDGET TO CỒNG KỀNH */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: '#F1F5F9',
            padding: '5px 14px',
            borderRadius: 6,
            fontSize: 12,
            fontWeight: 600,
            border: '1px solid #E2E8F0'
          }}>
            <span style={{ color: '#0369A1' }}><strong>{stats.totalShows}</strong> suất</span>
            <span style={{ color: '#CBD5E1' }}>|</span>
            <span style={{ color: '#15803D' }}><strong>{stats.uniqueMovies}</strong> phim</span>
            <span style={{ color: '#CBD5E1' }}>|</span>
            <span style={{ color: '#B45309' }}>Khung giờ: <strong>08:30 – 00:05</strong></span>
            <span style={{ color: '#CBD5E1' }}>|</span>
            <span style={{ color: '#6D28D9' }}>Nghỉ: <strong>15 phút</strong></span>
          </div>

          {/* Nút bấm mở Dialog nhỏ chi tiết thông số vận hành */}
          <button
            onClick={() => setShowInfoDialog(true)}
            style={{
              background: '#FFFFFF',
              border: '1px solid #CBD5E1',
              color: '#475569',
              padding: '5px 12px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 5
            }}
            title="Xem chi tiết các quy chuẩn vận hành rạp"
          >
            Quy chuẩn rạp
          </button>
        </div>
      </header>

      {/* 2. THANH ĐIỀU KHIỂN & CHỌN NGÀY (COMPACT CONTROLS) */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: 8,
        background: '#FFFFFF',
        padding: '8px 14px',
        borderRadius: 8,
        border: '1px solid #E2E8F0',
        flexShrink: 0
      }}>
        {/* Nút chuyển đổi View Mode */}
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            onClick={() => setViewMode('timeline')}
            style={{
              background: viewMode === 'timeline' ? 'var(--brand-blue)' : '#F1F5F9',
              color: viewMode === 'timeline' ? '#FFFFFF' : '#475569',
              border: '1px solid ' + (viewMode === 'timeline' ? 'var(--brand-blue)' : '#CBD5E1'),
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            Bảng dòng thời gian (Timeline)
          </button>
          <button
            onClick={() => setViewMode('catalog')}
            style={{
              background: viewMode === 'catalog' ? 'var(--brand-blue)' : '#F1F5F9',
              color: viewMode === 'catalog' ? '#FFFFFF' : '#475569',
              border: '1px solid ' + (viewMode === 'catalog' ? 'var(--brand-blue)' : '#CBD5E1'),
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: 12,
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}
          >
            Kho phim ({movies.length} phim)
          </button>
        </div>

        {/* Thanh chọn ngày */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, color: '#64748B', fontWeight: 700 }}>NGÀY:</span>
          {quickDates.map(item => {
            const isSelected = selectedDate === item.date;
            return (
              <button
                key={item.date}
                onClick={() => setSelectedDate(item.date)}
                style={{
                  background: isSelected 
                    ? 'rgba(37, 99, 235, 0.12)' 
                    : item.isToday 
                      ? '#F0FDF4' 
                      : '#FFFFFF',
                  color: isSelected 
                    ? 'var(--brand-blue)' 
                    : item.isToday 
                      ? '#166534' 
                      : '#475569',
                  border: isSelected 
                    ? '1.5px solid var(--brand-blue)' 
                    : item.isToday 
                      ? '1px solid #86EFAC' 
                      : '1px solid #CBD5E1',
                  padding: '4px 8px',
                  borderRadius: 5,
                  fontSize: 11,
                  cursor: 'pointer',
                  fontWeight: isSelected || item.isToday ? 700 : 500,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 3,
                  transition: 'all 0.15s ease'
                }}
              >
                {item.isToday && (
                  <span style={{
                    width: 5,
                    height: 5,
                    borderRadius: '50%',
                    background: '#22C55E',
                    display: 'inline-block'
                  }} />
                )}
                {item.label}
              </button>
            );
          })}
          <input
            type="date"
            value={selectedDate}
            onChange={e => setSelectedDate(e.target.value)}
            className="soc-input"
            style={{ width: 120, padding: '3px 6px', fontSize: 11 }}
          />
          {!isToday && (
            <button
              onClick={() => setSelectedDate(todayIso)}
              style={{
                background: 'rgba(37, 99, 235, 0.08)',
                color: 'var(--brand-blue)',
                border: '1px solid rgba(37, 99, 235, 0.25)',
                padding: '3px 8px',
                borderRadius: 5,
                fontSize: 11,
                fontWeight: 600,
                cursor: 'pointer'
              }}
              title="Nhảy về ngày hôm nay"
            >
              Về hôm nay
            </button>
          )}
        </div>

        {/* Ô tìm kiếm phim */}
        <div style={{ width: 200 }}>
          <input
            type="text"
            placeholder="Lọc tên phim..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="soc-input"
            style={{ width: '100%', boxSizing: 'border-box', fontSize: 11, padding: '4px 8px' }}
          />
        </div>
      </div>

      {/* 3. BẢNG DÒNG THỜI GIAN TIMELINE 4 PHÒNG - ZERO VERTICAL SCROLL */}
      {viewMode === 'timeline' && (
        <div style={{
          flex: 1,
          minHeight: 0,
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #E2E8F0',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Header Bảng Timeline */}
          <div style={{
            padding: '6px 14px',
            background: '#F8FAFC',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#334155' }}>
                LỊCH CHIẾU {isToday ? 'HÔM NAY' : 'NGÀY'}: <span style={{ color: 'var(--brand-blue)' }}>{selectedDate}</span> (4 PHÒNG CHIẾU TƯƠNG TÁC)
              </div>
              {/* Chú thích màu sắc (UX Legend) */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 10, color: '#64748B' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: '#DC2626', display: 'inline-block' }}></span>
                  <strong style={{ color: '#0F172A' }}>Đang chiếu</strong> (đậm nét)
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: 'var(--brand-blue)', display: 'inline-block' }}></span>
                  <span>Sắp chiếu</span>
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: '#94A3B8', opacity: 0.55, display: 'inline-block' }}></span>
                  <span>Đã chiếu</span> (màu nhạt)
                </span>
              </div>
            </div>
            <div style={{ fontSize: 11, color: '#64748B', display: 'flex', gap: 14 }}>
              <span><strong>Kéo & thả</strong> để dời giờ / chuyển phòng</span>
              <span><strong>Nhấn</strong> để điều chỉnh thời lượng / rút ngắn outro</span>
            </div>
          </div>


          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#64748B' }}>Đang tải lịch chiếu...</div>
          ) : showtimes.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: '#64748B' }}>
              Chưa có lịch chiếu cho ngày {selectedDate}. Vui lòng chọn ngày khác.
            </div>
          ) : (
            <div style={{
              flex: 1,
              minHeight: 0,
              display: 'flex',
              flexDirection: 'column',
              overflowX: 'auto',
              overflowY: 'hidden', // Khóa cuộn dọc tuyệt đối
              padding: '6px 12px 10px 12px'
            }}>
              <div style={{
                minWidth: 1100,
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                height: '100%'
              }}>
                {/* DÒNG THƯỚC GIỜ (TIME RULER) */}
                <div style={{
                  display: 'flex',
                  borderBottom: '2px solid #E2E8F0',
                  paddingBottom: 4,
                  marginBottom: 6,
                  height: 22,
                  flexShrink: 0
                }}>
                  <div style={{ width: 130, flexShrink: 0, fontSize: 11, fontWeight: 700, color: '#64748B' }}>
                    PHÒNG CHIẾU
                  </div>
                  <div style={{ flex: 1, position: 'relative' }}>
                    {hoursArray.map(h => {
                      const leftPct = ((h - TIMELINE_START_HOUR) / (TIMELINE_END_HOUR - TIMELINE_START_HOUR)) * 100;
                      return (
                        <div
                          key={h}
                          style={{
                            position: 'absolute',
                            left: `${leftPct}%`,
                            transform: 'translateX(-50%)',
                            fontSize: 11,
                            fontWeight: 700,
                            fontFamily: 'JetBrains Mono, monospace',
                            color: '#64748B'
                          }}
                        >
                          {String(h).padStart(2, '0')}:00
                        </div>
                      );
                    })}
                    {/* Thẻ chỉ giờ hiện tại trên thước */}
                    {isToday && nowMin >= TIMELINE_START_HOUR * 60 && nowMin <= TIMELINE_END_HOUR * 60 && (
                      <div
                        style={{
                          position: 'absolute',
                          left: `${Math.max(0, Math.min(100, ((nowMin - TIMELINE_START_HOUR * 60) / TIMELINE_TOTAL_MINUTES) * 100))}%`,
                          transform: 'translateX(-50%)',
                          top: -3,
                          background: '#EF4444',
                          color: '#FFFFFF',
                          fontSize: 9,
                          fontWeight: 800,
                          padding: '1px 5px',
                          borderRadius: 4,
                          fontFamily: 'JetBrains Mono, monospace',
                          zIndex: 20,
                          boxShadow: '0 2px 4px rgba(239, 68, 68, 0.4)',
                          pointerEvents: 'none',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {currentTimeStr}
                      </div>
                    )}
                  </div>
                </div>

                {/* 4 HÀNG PHÒNG CHIẾU - TỰ ĐỘNG CHIA ĐỀU CHIỀU CAO VỪA KHÍT MÀN HÌNH */}
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  minHeight: 0
                }}>
                  {Object.entries(showsByRoom).map(([roomId, roomData], rIndex) => {
                    const isDragTarget = dragOverRoom === roomId;

                    return (
                      <div
                        key={roomId}
                        style={{
                          flex: 1,
                          minHeight: 70,
                          maxHeight: 110,
                          display: 'flex',
                          alignItems: 'center',
                          padding: '4px 0',
                          borderBottom: rIndex < 3 ? '1px dashed #E2E8F0' : 'none',
                          background: isDragTarget ? 'rgba(37, 99, 235, 0.05)' : 'transparent',
                          transition: 'background 0.15s ease'
                        }}
                      >
                        {/* Cột Tên Phòng bên trái */}
                        <div style={{ width: 130, flexShrink: 0, paddingRight: 8 }}>
                          <div style={{ fontWeight: 700, fontSize: 13, color: '#0F172A' }}>
                            {roomData.label}
                          </div>
                          <div style={{ fontSize: 11, color: '#64748B', marginTop: 3, fontWeight: 500 }}>
                            {roomData.shows.length} suất • 136 ghế
                          </div>
                        </div>

                        {/* VÙNG TRACK THỜI GIAN NHẬN KÉO THẢ */}
                        <div
                          onDragOver={(e) => handleDragOverTrack(e, roomId)}
                          onDragLeave={(e) => handleDragLeaveTrack(e, roomId)}
                          onDrop={(e) => handleDropOnTrack(e, roomId)}
                          style={{
                            flex: 1,
                            position: 'relative',
                            height: '100%',
                            minHeight: 64,
                            background: isDragTarget ? '#EFF6FF' : '#F8FAFC',
                            borderRadius: 6,
                            border: isDragTarget ? '2px dashed var(--brand-blue)' : '1px solid #E2E8F0',
                            transition: 'all 0.15s ease'
                          }}
                        >
                          {/* Lưới vạch dọc giờ */}
                          {hoursArray.map(h => {
                            const leftPct = ((h - TIMELINE_START_HOUR) / (TIMELINE_END_HOUR - TIMELINE_START_HOUR)) * 100;
                            return (
                              <div
                                key={h}
                                style={{
                                  position: 'absolute',
                                  left: `${leftPct}%`,
                                  top: 0,
                                  bottom: 0,
                                  width: 1,
                                  background: '#E2E8F0',
                                  pointerEvents: 'none'
                                }}
                              />
                            );
                          })}

                          {/* Vạch đỏ chỉ giờ thực tế chạy xuyên suốt */}
                          {isToday && nowMin >= TIMELINE_START_HOUR * 60 && nowMin <= TIMELINE_END_HOUR * 60 && (
                            <div
                              style={{
                                position: 'absolute',
                                left: `${Math.max(0, Math.min(100, ((nowMin - TIMELINE_START_HOUR * 60) / TIMELINE_TOTAL_MINUTES) * 100))}%`,
                                top: 0,
                                bottom: 0,
                                width: 2,
                                background: '#EF4444',
                                zIndex: 12,
                                pointerEvents: 'none',
                                boxShadow: '0 0 6px rgba(239, 68, 68, 0.7)'
                              }}
                            />
                          )}

                          {/* CÁC KHỐI SUẤT CHIẾU (SHOWTIME CARDS) */}
                          {roomData.shows.map((s, idx) => {
                            const startMin = timeToMinutes(s.start_time);
                            const duration = s.duration_minutes || 100;
                            const leftPct = Math.max(0, ((startMin - TIMELINE_START_HOUR * 60) / TIMELINE_TOTAL_MINUTES) * 100);
                            const widthPct = Math.max(4.2, (duration / TIMELINE_TOTAL_MINUTES) * 100);

                            const movieName = s.movie_name || s.movie_title || 'Suất chiếu';
                            const palette = getMovieColor(movieName);
                            const mockOccupancy = ((s.movie_id * 7 + idx * 13) % 32 + 10).toFixed(0);

                            const status = getShowStatus(s, selectedDate, currentTime);
                            const isPast = status === 'past';
                            const isOngoing = status === 'ongoing';

                            return (
                              <div
                                key={s.show_id}
                                draggable={true}
                                onDragStart={(e) => handleDragStart(e, s)}
                                onClick={() => handleOpenEditModal(s)}
                                title={`${movieName}\nKhung giờ: ${s.start_time} - ${s.end_time} (${duration} phút)\nTrạng thái: ${isPast ? 'Đã chiếu xong' : isOngoing ? 'Đang chiếu (Trực tiếp)' : 'Sắp chiếu'}\nKéo để đổi giờ/phòng • Nhấn để chỉnh sửa`}
                                style={{
                                  position: 'absolute',
                                  left: `${leftPct}%`,
                                  width: `${widthPct}%`,
                                  top: 3,
                                  bottom: 3,
                                  background: palette.bg,
                                  border: isOngoing 
                                    ? '2px solid #FFFFFF' 
                                    : isPast 
                                      ? '1px dashed rgba(148, 163, 184, 0.7)' 
                                      : `1px solid ${palette.border}`,
                                  borderRadius: 5,
                                  padding: '3px 6px',
                                  boxSizing: 'border-box',
                                  cursor: 'grab',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  justifyContent: 'space-between',
                                  overflow: 'hidden',
                                  opacity: isPast ? 0.52 : 1,
                                  filter: isPast ? 'grayscale(25%)' : 'none',
                                  boxShadow: isOngoing 
                                    ? '0 0 0 2.5px #22C55E, 0 4px 14px rgba(34, 197, 94, 0.45)' 
                                    : isPast 
                                      ? 'none' 
                                      : '0 2px 5px rgba(0,0,0,0.15)',
                                  transition: 'transform 0.15s, box-shadow 0.15s, opacity 0.15s',
                                  zIndex: isOngoing ? 8 : isPast ? 1 : 2,
                                  userSelect: 'none'
                                }}
                                onMouseEnter={e => {
                                  e.currentTarget.style.transform = 'translateY(-2px) scale(1.015)';
                                  e.currentTarget.style.zIndex = '15';
                                  if (isPast) {
                                    e.currentTarget.style.opacity = '0.9';
                                    e.currentTarget.style.filter = 'none';
                                    e.currentTarget.style.boxShadow = '0 4px 10px rgba(0,0,0,0.2)';
                                  } else if (isOngoing) {
                                    e.currentTarget.style.boxShadow = '0 0 0 3px #22C55E, 0 8px 18px rgba(34, 197, 94, 0.55)';
                                  } else {
                                    e.currentTarget.style.boxShadow = '0 6px 12px rgba(0,0,0,0.25)';
                                  }
                                }}
                                onMouseLeave={e => {
                                  e.currentTarget.style.transform = 'translateY(0) scale(1)';
                                  if (isPast) {
                                    e.currentTarget.style.opacity = '0.52';
                                    e.currentTarget.style.filter = 'grayscale(25%)';
                                    e.currentTarget.style.zIndex = '1';
                                    e.currentTarget.style.boxShadow = 'none';
                                  } else if (isOngoing) {
                                    e.currentTarget.style.zIndex = '8';
                                    e.currentTarget.style.boxShadow = '0 0 0 2.5px #22C55E, 0 4px 14px rgba(34, 197, 94, 0.45)';
                                  } else {
                                    e.currentTarget.style.zIndex = '2';
                                    e.currentTarget.style.boxShadow = '0 2px 5px rgba(0,0,0,0.15)';
                                  }
                                }}
                              >
                                {/* Dòng 1: Giờ bắt đầu & Badge trạng thái */}
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <span style={{ 
                                    fontSize: 10, 
                                    fontWeight: isOngoing ? 800 : 700, 
                                    fontFamily: 'JetBrains Mono, monospace', 
                                    color: isPast ? 'rgba(255,255,255,0.85)' : palette.text 
                                  }}>
                                    {s.start_time}~
                                  </span>
                                  {s.is_manually_edited && (
                                    <span style={{
                                      fontSize: 8,
                                      background: '#F59E0B',
                                      color: '#FFFFFF',
                                      padding: '1px 3px',
                                      borderRadius: 2,
                                      fontWeight: 700
                                    }}>
                                      ĐÃ ĐỔI
                                    </span>
                                  )}
                                  {isOngoing ? (
                                    <span style={{
                                      fontSize: 8,
                                      background: '#DC2626',
                                      color: '#FFFFFF',
                                      padding: '1px 5px',
                                      borderRadius: 3,
                                      fontWeight: 800,
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 3,
                                      boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                                      letterSpacing: '0.3px'
                                    }}>
                                      <span style={{
                                        width: 5,
                                        height: 5,
                                        borderRadius: '50%',
                                        background: '#FFFFFF',
                                        display: 'inline-block'
                                      }} />
                                      ĐANG CHIẾU
                                    </span>
                                  ) : isPast ? (
                                    <span style={{
                                      fontSize: 8,
                                      background: 'rgba(100, 116, 139, 0.85)',
                                      color: '#F1F5F9',
                                      padding: '1px 4px',
                                      borderRadius: 3,
                                      fontWeight: 600
                                    }}>
                                      ĐÃ CHIẾU
                                    </span>
                                  ) : (
                                    <span style={{
                                      fontSize: 9,
                                      background: palette.badge,
                                      color: '#FFFFFF',
                                      padding: '0 4px',
                                      borderRadius: 3,
                                      fontWeight: 700
                                    }}>
                                      #{idx + 1}
                                    </span>
                                  )}
                                </div>

                                {/* Dòng 2: Tên Phim */}
                                <div style={{
                                  fontSize: 11,
                                  fontWeight: isOngoing ? 800 : 700,
                                  color: isPast ? 'rgba(255,255,255,0.85)' : palette.text,
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                                  margin: '1px 0',
                                  lineHeight: 1.2
                                }}>
                                  {movieName}
                                </div>

                                {/* Dòng 3: Thời lượng & Lấp đầy */}
                                <div style={{
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center',
                                  fontSize: 9,
                                  color: isPast ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.92)',
                                  fontWeight: isOngoing ? 700 : 600
                                }}>
                                  <span>{duration}p</span>
                                  <span>{mockOccupancy}% vé</span>
                                </div>
                              </div>
                            );
                          })}

                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. CHẾ ĐỘ VIEW 2: KHO PHIM ĐÃ CHUẨN BỊ (MOVIES CATALOG) */}
      {viewMode === 'catalog' && (
        <div style={{
          flex: 1,
          minHeight: 0,
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #E2E8F0',
          padding: 16,
          overflowY: 'auto'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#0F172A' }}>
                KHO PHIM SẴN SÀNG CHO LỊCH CHIẾU
              </div>
              <div style={{ fontSize: 12, color: '#64748B' }}>
                Bao gồm 8 phim TMDB và các phim chiếu rạp có dữ liệu thời lượng chuẩn
              </div>
            </div>
            <span style={{ background: '#F1F5F9', padding: '4px 10px', borderRadius: 6, fontSize: 12, color: 'var(--brand-blue)', fontWeight: 600 }}>
              Tổng cộng: <strong>{movies.length}</strong> phim
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 14 }}>
            {movies.map(m => {
              const posterUrl = m.poster_path 
                ? `https://image.tmdb.org/t/p/w342${m.poster_path}`
                : null;
              const isTmdb = m.source === 'tmdb';

              return (
                <div
                  key={m.id}
                  style={{
                    background: '#FFFFFF',
                    borderRadius: 8,
                    border: '1px solid #E2E8F0',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                  }}
                >
                  <div style={{ height: 240, background: '#F1F5F9', position: 'relative', overflow: 'hidden' }}>
                    {posterUrl ? (
                      <img
                        src={posterUrl}
                        alt={m.title_vi}
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        onError={e => { e.currentTarget.style.display = 'none'; }}
                      />
                    ) : (
                      <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94A3B8', fontSize: 12 }}>
                        Không có poster
                      </div>
                    )}
                    <div style={{
                      position: 'absolute',
                      top: 8,
                      right: 8,
                      background: isTmdb ? '#0284C7' : '#D97706',
                      color: '#FFFFFF',
                      fontSize: 10,
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 4
                    }}>
                      {isTmdb ? 'TMDB Official' : 'Manual'}
                    </div>
                    <div style={{
                      position: 'absolute',
                      bottom: 8,
                      left: 8,
                      background: 'rgba(15, 23, 42, 0.8)',
                      color: '#FFFFFF',
                      fontSize: 10,
                      padding: '2px 6px',
                      borderRadius: 4,
                      fontFamily: 'JetBrains Mono, monospace'
                    }}>
                      {m.runtime_min || 0} phút
                    </div>
                  </div>

                  <div style={{ padding: 10, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: 13, color: '#0F172A', marginBottom: 2 }}>
                        {m.title_vi || m.title_original}
                      </div>
                      {m.title_original && m.title_original !== m.title_vi && (
                        <div style={{ fontSize: 11, color: '#64748B', fontStyle: 'italic', marginBottom: 6 }}>
                          {m.title_original}
                        </div>
                      )}
                    </div>
                    <div style={{ borderTop: '1px solid #F1F5F9', paddingTop: 6, fontSize: 11, color: '#64748B', display: 'flex', justifyContent: 'space-between' }}>
                      <span>Khởi chiếu: <strong>{m.release_date || 'N/A'}</strong></span>
                      <span style={{ color: m.is_active ? '#15803D' : '#EF4444', fontWeight: 600 }}>
                        {m.is_active ? '● Active' : '○ Tạm dừng'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. DIALOG NHỎ: THÔNG SỐ VẬN HÀNH RẠP (THAY THẾ 4 KHỐI WIDGET TO CỒNG KỀNH) */}
      {showInfoDialog && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.4)',
            backdropFilter: 'blur(2px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
            padding: 16
          }}
          onClick={() => setShowInfoDialog(false)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              border: '1px solid #E2E8F0',
              width: 440,
              maxWidth: '100%',
              padding: '20px 24px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 15, color: '#0F172A' }}>
                THÔNG SỐ QUY CHUẨN VẬN HÀNH RẠP
              </div>
              <button
                onClick={() => setShowInfoDialog(false)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#F8FAFC', borderRadius: 6 }}>
                <span style={{ color: '#64748B' }}>Tổng suất chiếu ngày {selectedDate}:</span>
                <strong style={{ color: '#0284C7' }}>{stats.totalShows} suất (đều 4 phòng)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#F8FAFC', borderRadius: 6 }}>
                <span style={{ color: '#64748B' }}>Số lượng phim phát hành:</span>
                <strong style={{ color: '#16A34A' }}>{stats.uniqueMovies} phim đã duyệt</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#F8FAFC', borderRadius: 6 }}>
                <span style={{ color: '#64748B' }}>Khung giờ mở cửa & đón khách:</span>
                <strong style={{ color: '#D97706' }}>08:30 đến 00:05 sáng hôm sau</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#F8FAFC', borderRadius: 6 }}>
                <span style={{ color: '#64748B' }}>Khoảng nghỉ dọn phòng (Turnover):</span>
                <strong style={{ color: '#7C3AED' }}>15 phút (Lưới bắt đầu chia hết cho 5)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: '#F8FAFC', borderRadius: 6 }}>
                <span style={{ color: '#64748B' }}>Quy tắc xếp phim liên tiếp:</span>
                <strong style={{ color: '#0F172A' }}>Không chiếu 2 suất cùng 1 phim liên tiếp</strong>
              </div>
            </div>

            <div style={{ marginTop: 18, display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowInfoDialog(false)}
                style={{
                  background: 'var(--brand-blue)',
                  color: '#FFFFFF',
                  border: 'none',
                  padding: '7px 16px',
                  borderRadius: 6,
                  fontWeight: 600,
                  fontSize: 12,
                  cursor: 'pointer'
                }}
              >
                Đã hiểu
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. MODAL ĐIỀU CHỈNH SUẤT CHIẾU (CHỈNH GIỜ, RÚT GỌN OUTRO, ĐỔI PHÒNG) */}
      {editingShow && (
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
            padding: 16
          }}
          onClick={() => setEditingShow(null)}
        >
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 12,
              border: '1px solid #CBD5E1',
              width: 520,
              maxWidth: '100%',
              overflow: 'hidden',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
            }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header Modal */}
            <div style={{
              background: '#F8FAFC',
              padding: '12px 20px',
              borderBottom: '1px solid #E2E8F0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, color: '#0F172A' }}>
                  ĐIỀU CHỈNH THÔNG SỐ SUẤT CHIẾU
                </div>
                <div style={{ fontSize: 11, color: '#64748B' }}>
                  Hỗ trợ rút gọn outro, đổi phòng hoặc dời giờ theo tình hình rạp thực tế
                </div>
              </div>
              <button
                onClick={() => setEditingShow(null)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', fontSize: 18, cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            {/* Form Nội Dung */}
            <form onSubmit={handleSaveShowEdit} style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Thông tin phim */}
              <div style={{ padding: '10px 14px', background: '#F1F5F9', borderRadius: 8 }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#0F172A' }}>
                  {editingShow.movie_name || editingShow.movie_title}
                </div>
                <div style={{ fontSize: 11, color: '#64748B', marginTop: 2 }}>
                  Mã suất: <code>{editingShow.show_id}</code> • Gốc: {editingShow.start_time} - {editingShow.end_time}
                </div>
              </div>

              {/* Hàng 1: Chọn Phòng & Giờ bắt đầu */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Phòng chiếu:
                  </label>
                  <select
                    value={editForm.room_id}
                    onChange={e => setEditForm({ ...editForm, room_id: e.target.value })}
                    className="soc-input"
                    style={{ width: '100%', boxSizing: 'border-box' }}
                  >
                    <option value="room1">Phòng chiếu 1</option>
                    <option value="room2">Phòng chiếu 2</option>
                    <option value="room3">Phòng chiếu 3</option>
                    <option value="room4">Phòng chiếu 4</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Giờ bắt đầu chiếu:
                  </label>
                  <input
                    type="time"
                    step="300"
                    value={editForm.start_time}
                    onChange={e => setEditForm({ ...editForm, start_time: e.target.value })}
                    className="soc-input"
                    style={{ width: '100%', boxSizing: 'border-box', fontFamily: 'JetBrains Mono, monospace' }}
                    required
                  />
                </div>
              </div>

              {/* Hàng 2: Thời lượng & Rút ngắn Outro */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <label style={{ fontSize: 12, fontWeight: 700, color: '#334155' }}>
                    Thời lượng suất chiếu (Phút):
                  </label>
                  <span style={{ fontSize: 11, color: 'var(--brand-blue)', fontWeight: 600 }}>
                    Kết thúc lúc: <strong>{calculatedEndTime}</strong>
                  </span>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="number"
                    min="30"
                    max="240"
                    value={editForm.duration_minutes}
                    onChange={e => setEditForm({ ...editForm, duration_minutes: Number(e.target.value) })}
                    className="soc-input"
                    style={{ width: 100, boxSizing: 'border-box', fontFamily: 'JetBrains Mono, monospace', fontWeight: 700 }}
                    required
                  />
                  {/* Phím tắt nhanh cho quản lý rạp */}
                  <div style={{ display: 'flex', gap: 6, flex: 1, flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => setEditForm({ ...editForm, duration_minutes: Math.max(30, (editingShow.duration_minutes || 100) - 10) })}
                      style={{ background: '#FEF3C7', border: '1px solid #FCD34D', color: '#92400E', padding: '4px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, cursor: 'pointer' }}
                      title="Cắt 10 phút outro/credits cuối phim"
                    >
                      Rút ngắn 10p (Outro)
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditForm({ ...editForm, duration_minutes: Math.max(30, (editingShow.duration_minutes || 100) - 5) })}
                      style={{ background: '#FEF3C7', border: '1px solid #FCD34D', color: '#92400E', padding: '4px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, cursor: 'pointer' }}
                      title="Cắt 5 phút credits"
                    >
                      Rút ngắn 5p
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditForm({ ...editForm, duration_minutes: editingShow.duration_minutes || 100 })}
                      style={{ background: '#F1F5F9', border: '1px solid #CBD5E1', color: '#475569', padding: '4px 8px', borderRadius: 4, fontSize: 11, cursor: 'pointer' }}
                    >
                      Về gốc ({editingShow.duration_minutes}p)
                    </button>
                  </div>
                </div>
              </div>

              {/* Hàng 3: Lý do điều chỉnh */}
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                  Lý do điều chỉnh (Ghi nhận vận hành):
                </label>
                <select
                  value={editForm.reason}
                  onChange={e => setEditForm({ ...editForm, reason: e.target.value })}
                  className="soc-input"
                  style={{ width: '100%', boxSizing: 'border-box' }}
                >
                  <option value="Rút gọn outro / credits kết thúc phim">Rút gọn outro / credits kết thúc phim</option>
                  <option value="Khán giả vào rạp trễ do sự cố soát vé">Khán giả vào rạp trễ do sự cố soát vé</option>
                  <option value="Bảo trì máy chiếu / hệ thống âm thanh">Bảo trì máy chiếu / hệ thống âm thanh</option>
                  <option value="Đổi phòng chiếu theo nhu cầu lượng vé">Đổi phòng chiếu theo nhu cầu lượng vé</option>
                  <option value="Khác">Lý do khác</option>
                </select>
              </div>

              {/* Nút hành động */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                borderTop: '1px solid #E2E8F0',
                paddingTop: 14,
                marginTop: 4
              }}>
                <button
                  type="button"
                  onClick={() => handleDeleteShow(editingShow.show_id)}
                  style={{
                    background: '#FEE2E2',
                    border: '1px solid #FCA5A5',
                    color: '#991B1B',
                    padding: '7px 12px',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Huỷ suất này
                </button>

                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    type="button"
                    onClick={() => setEditingShow(null)}
                    style={{
                      background: '#F1F5F9',
                      border: '1px solid #CBD5E1',
                      color: '#475569',
                      padding: '7px 14px',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Đóng
                  </button>
                  {onNavigateToTickets && (
                    <button
                      type="button"
                      onClick={() => {
                        const s = editingShow;
                        setEditingShow(null);
                        onNavigateToTickets(s.room_id, s.show_id);
                      }}
                      style={{
                        background: '#0284C7',
                        border: 'none',
                        color: '#FFFFFF',
                        padding: '7px 14px',
                        borderRadius: 6,
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      Xem vé
                    </button>
                  )}
                  <button
                    type="submit"
                    style={{
                      background: 'var(--brand-blue)',
                      border: 'none',
                      color: '#FFFFFF',
                      padding: '7px 18px',
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: 'pointer'
                    }}
                  >
                    Lưu cập nhật
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
