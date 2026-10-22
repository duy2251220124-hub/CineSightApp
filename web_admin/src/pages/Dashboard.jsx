import { useState, useEffect, useMemo } from 'react';
import { analyzeRoom, healthCheck, getActiveAlerts, resolveAlert, getShowtimes } from '../api/cineSightApi';
import {
  ShieldAlert,
  ShieldCheck,
  UserX,
  UserMinus,
  Users,
  Sparkles,
  Search,
  Check,
  Upload
} from '../components/Icons';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [serverOnline, setServerOnline] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState('room1');
  const [showId, setShowId] = useState('2026-10-05T19:30');
  const [roomShowtimes, setRoomShowtimes] = useState([]);
  const [loadingShowtimes, setLoadingShowtimes] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Filter & Search toolbar state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all'); // 'all', 'illegal_occupant', 'missing_guest', 'over_capacity'
  
  // New alert animation tracking
  const [newAlertId] = useState(null);

  // Đồng hồ thời gian thực
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Kiểm tra Server Health
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

  // Tải danh sách cảnh báo
  const fetchAlerts = async () => {
    try {
      const data = await getActiveAlerts();
      setAlerts(data);
    } catch (e) {
      console.error('Lỗi tải danh sách cảnh báo:', e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const alertTimer = setInterval(fetchAlerts, 5000);
    return () => clearInterval(alertTimer);
  }, []);

  // Tải danh sách suất chiếu của phòng được chọn
  useEffect(() => {
    let isMounted = true;
    const fetchShows = async () => {
      setLoadingShowtimes(true);
      try {
        const shows = await getShowtimes(selectedRoom);
        if (isMounted) {
          const list = shows || [];
          setRoomShowtimes(list);
          if (list.length > 0) {
            setShowId(prev => {
              const exists = list.some(s => s.show_id === prev);
              return exists ? prev : list[0].show_id;
            });
          }
        }
      } catch (e) {
        console.error('Lỗi tải danh sách suất chiếu:', e);
      } finally {
        if (isMounted) setLoadingShowtimes(false);
      }
    };
    fetchShows();
    return () => { isMounted = false; };
  }, [selectedRoom]);

  const handleAnalyze = async () => {
    if (!showId) return alert('Vui lòng chọn suất chiếu trước khi chạy phân tích.');
    if (!imageFile) return alert('Vui lòng chọn ảnh snapshot phòng chiếu trước khi chạy.');
    setIsAnalyzing(true);
    try {
      await analyzeRoom(selectedRoom, showId, imageFile);
      await fetchAlerts();
    } catch (e) {
      alert('Lỗi AI: ' + e.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleResolve = async (id) => {
    try {
      await resolveAlert(id);
      await fetchAlerts();
    } catch (e) {
      alert('Không thể cập nhật trạng thái: ' + e.message);
    }
  };

  // Tính toán số liệu thống kê
  const illegalCount = alerts.filter(a => a.alert_type === 'illegal_occupant').length;
  const missingCount = alerts.filter(a => a.alert_type === 'missing_guest').length;
  const overCapCount = alerts.filter(a => a.alert_type === 'over_capacity').length;
  const totalCount = alerts.length;

  // Lọc và tìm kiếm cảnh báo
  const filteredAlerts = useMemo(() => {
    return alerts.filter(a => {
      if (filterType !== 'all' && a.alert_type !== filterType) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const room = (a.room_id || '').toLowerCase();
        const show = (a.show_id || '').toLowerCase();
        const seat = (a.seat_id || '').toLowerCase();
        return room.includes(q) || show.includes(q) || seat.includes(q);
      }
      return true;
    });
  }, [alerts, filterType, searchQuery]);

  return (
    <div className="soc-container">
      {/* 1. HEADER TRẠNG THÁI (TOP BAR) */}
      <header className="soc-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#0F172A', letterSpacing: '-0.3px' }}>
            CINESIGHT SOC
          </div>
          <span style={{
            fontSize: 12,
            color: '#475569',
            background: '#FFFFFF',
            border: '1px solid #CBD5E1',
            padding: '3px 10px',
            borderRadius: 6,
            fontWeight: 600,
            boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)'
          }}>
            Trung tâm Giám sát An ninh Phòng chiếu
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Status Pill nhấp nháy nhẹ */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            background: '#FFFFFF',
            border: '1px solid #CBD5E1',
            padding: '5px 12px',
            borderRadius: 9999,
            fontSize: 12.5,
            fontWeight: 600,
            color: '#1E293B',
            boxShadow: '0 1px 2px rgba(15, 23, 42, 0.05)'
          }}>
            <span style={{ position: 'relative', display: 'flex', width: 8, height: 8 }}>
              {serverOnline && (
                <span style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 9999,
                  backgroundColor: '#10B981',
                  opacity: 0.75,
                  animation: 'ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite'
                }} />
              )}
              <span style={{
                position: 'relative',
                display: 'inline-flex',
                width: 8,
                height: 8,
                borderRadius: 9999,
                backgroundColor: serverOnline ? '#10B981' : '#DC2626'
              }} />
            </span>
            <span>{serverOnline ? 'Hệ thống AI sẵn sàng' : 'Mất kết nối máy chủ'}</span>
          </div>

          {/* Đồng hồ kỹ thuật số */}
          <div style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 14,
            fontWeight: 700,
            color: '#0F172A',
            background: '#FFFFFF',
            border: '1px solid #CBD5E1',
            padding: '5px 12px',
            borderRadius: 6,
            boxShadow: '0 1px 2px rgba(15, 23, 42, 0.05)',
            letterSpacing: '0.5px'
          }}>
            {currentTime.toLocaleTimeString('vi-VN', { hour12: false })}
          </div>
        </div>
      </header>

      {/* 2. KHU VỰC BENTO GRID 4 THẺ KPI RIÊNG BIỆT VỚI TOP ACCENT BORDER & HIGH CONTRAST */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: 14,
        flexShrink: 0
      }}>
        {/* THẺ 1: TỔNG CẢNH BÁO */}
        <div style={{
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #CBD5E1',
          borderTop: '3px solid #2563EB',
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#1E293B', letterSpacing: '0.5px' }}>
              TỔNG CẢNH BÁO
            </span>
            <span style={{
              width: 30,
              height: 30,
              borderRadius: 6,
              background: '#EFF6FF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#2563EB'
            }}>
              <ShieldAlert size={18} />
            </span>
          </div>
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 32, fontWeight: 800, color: '#0F172A', lineHeight: 1 }}>
              {totalCount}
            </span>
            <span style={{ fontSize: 12, color: '#475569', fontWeight: 600 }}>sự vụ chờ xử lý</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#475569', fontWeight: 500 }}>
            Tổng hợp toàn bộ phòng chiếu
          </div>
        </div>

        {/* THẺ 2: KHÁCH LẬU */}
        <div style={{
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #CBD5E1',
          borderTop: '3px solid #DC2626',
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#1E293B', letterSpacing: '0.5px' }}>
              KHÁCH LẬU
            </span>
            <span style={{
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 4,
              background: '#FEE2E2',
              color: '#991B1B',
              border: '1px solid #FECACA',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}>
              <UserX size={13} />
              Nghiêm trọng
            </span>
          </div>
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 32, fontWeight: 800, color: '#DC2626', lineHeight: 1 }}>
              {illegalCount}
            </span>
            <span style={{ fontSize: 12, color: '#475569', fontWeight: 600 }}>ghế vi phạm</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#475569', fontWeight: 500 }}>
            Người ngồi nhưng không có vé
          </div>
        </div>

        {/* THẺ 3: VẮNG MẶT */}
        <div style={{
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #CBD5E1',
          borderTop: '3px solid #D97706',
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#1E293B', letterSpacing: '0.5px' }}>
              VẮNG MẶT
            </span>
            <span style={{
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 4,
              background: '#FEF3C7',
              color: '#92400E',
              border: '1px solid #FDE68A',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}>
              <UserMinus size={13} />
              Cần lưu ý
            </span>
          </div>
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 32, fontWeight: 800, color: '#D97706', lineHeight: 1 }}>
              {missingCount}
            </span>
            <span style={{ fontSize: 12, color: '#475569', fontWeight: 600 }}>ghế trống</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#475569', fontWeight: 500 }}>
            Vé đã bán nhưng khách chưa vào
          </div>
        </div>

        {/* THẺ 4: VƯỢT TẢI */}
        <div style={{
          background: '#FFFFFF',
          borderRadius: 8,
          border: '1px solid #CBD5E1',
          borderTop: '3px solid #2563EB',
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#1E293B', letterSpacing: '0.5px' }}>
              VƯỢT TẢI
            </span>
            <span style={{
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 4,
              background: '#DBEAFE',
              color: '#1E40AF',
              border: '1px solid #BFDBFE',
              display: 'flex',
              alignItems: 'center',
              gap: 4
            }}>
              <Users size={13} />
              Dung lượng
            </span>
          </div>
          <div style={{ marginTop: 12, display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontFamily: 'Inter, sans-serif', fontSize: 32, fontWeight: 800, color: '#2563EB', lineHeight: 1 }}>
              {overCapCount}
            </span>
            <span style={{ fontSize: 12, color: '#475569', fontWeight: 600 }}>phòng quá tải</span>
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#475569', fontWeight: 500 }}>
            Số người vượt lượng vé phát hành
          </div>
        </div>
      </div>

      {/* 3. KHU VỰC KIỂM TRA THỦ CÔNG (MANUAL SCAN) */}
      <div style={{
        background: '#FFFFFF',
        borderRadius: 8,
        border: '1px solid #CBD5E1',
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 14,
        boxShadow: '0 1px 3px rgba(15, 23, 42, 0.08)',
        flexShrink: 0
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            width: 32,
            height: 32,
            borderRadius: 6,
            background: '#EFF6FF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--brand-blue)'
          }}>
            <Sparkles size={18} />
          </span>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: 700, color: '#0F172A' }}>
              Kiểm tra thủ công bằng Snapshot Camera
            </div>
            <div style={{ fontSize: 12, color: '#475569', fontWeight: 500 }}>
              Nạp ảnh camera phòng chiếu để AI đối soát tức thời với hệ thống bán vé
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Chọn phòng chiếu */}
          <select
            value={selectedRoom}
            onChange={e => setSelectedRoom(e.target.value)}
            className="soc-input"
            style={{ width: 170, fontSize: 13, fontWeight: 600 }}
          >
            <option value="room1">Phòng chiếu 1</option>
            <option value="room2">Phòng chiếu 2</option>
            <option value="room3">Phòng chiếu 3</option>
            <option value="room4">Phòng chiếu 4</option>
          </select>

          {/* Chọn suất chiếu */}
          <select
            value={showId}
            onChange={e => setShowId(e.target.value)}
            className="soc-input"
            style={{ width: 230, fontSize: 13, fontWeight: 500 }}
            disabled={loadingShowtimes}
          >
            {roomShowtimes.length === 0 ? (
              <option value={showId}>{loadingShowtimes ? 'Đang tải suất chiếu...' : (showId || 'Không có suất chiếu')}</option>
            ) : (
              roomShowtimes.map(st => (
                <option key={st.show_id || st.id} value={st.show_id}>
                  {st.start_time || st.show_id.split('T')[1]} - {st.movie_title || st.title_vi || 'Phim'} ({st.date || st.show_id.split('T')[0]})
                </option>
              ))
            )}
          </select>

          {/* Vùng chọn file có hiển thị tên file rõ ràng */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            background: '#F8FAFC',
            border: '1px solid #CBD5E1',
            borderRadius: 6,
            padding: '4px 10px 4px 6px',
            gap: 8
          }}>
            <label style={{
              background: '#FFFFFF',
              border: '1px solid #CBD5E1',
              color: '#0F172A',
              padding: '5px 12px',
              borderRadius: 4,
              fontSize: 12.5,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5
            }}>
              <Upload size={14} />
              <span>Chọn ảnh...</span>
              <input type="file" accept="image/*" onChange={e => setImageFile(e.target.files[0])} hidden />
            </label>
            <span
              style={{
                fontSize: 12.5,
                color: imageFile ? '#0F172A' : '#475569',
                maxWidth: 200,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                fontWeight: imageFile ? 600 : 500
              }}
              title={imageFile ? imageFile.name : 'Chưa chọn file'}
            >
              {imageFile ? imageFile.name : 'Chưa chọn tệp snapshot'}
            </span>
          </div>

          {/* Nút Chạy AI màu thương hiệu #2563EB */}
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !serverOnline}
            className="soc-btn primary"
            style={{ fontSize: 13, padding: '8px 18px' }}
          >
            <Sparkles size={15} />
            <span>{isAnalyzing ? 'ĐANG XỬ LÝ...' : 'CHẠY AI'}</span>
          </button>
        </div>
      </div>

      {/* 4. BẢNG CẢNH BÁO CHỜ XỬ LÝ (LIVE FEED) VỚI TOOLBAR */}
      <div className="soc-panel soc-feed">
        {/* THANH CÔNG CỤ TRÊN ĐẦU BẢNG (TOOLBAR) */}
        <div style={{
          padding: '12px 16px',
          background: '#F8FAFC',
          borderBottom: '1px solid #CBD5E1',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
          flexShrink: 0
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#0F172A', letterSpacing: '0.5px' }}>
              CẢNH BÁO CHỜ XỬ LÝ (LIVE)
            </span>
            <span style={{
              fontSize: 11.5,
              fontWeight: 700,
              background: '#EFF6FF',
              border: '1px solid #BFDBFE',
              padding: '2px 8px',
              borderRadius: 9999,
              color: 'var(--brand-blue)'
            }}>
              {filteredAlerts.length} sự vụ
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {/* Bộ lọc loại vấn đề */}
            <div style={{ display: 'flex', background: '#FFFFFF', border: '1px solid #CBD5E1', borderRadius: 6, padding: 2 }}>
              <button
                onClick={() => setFilterType('all')}
                style={{
                  background: filterType === 'all' ? 'var(--brand-blue)' : 'transparent',
                  color: filterType === 'all' ? '#FFFFFF' : '#475569',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: filterType === 'all' ? '0 1px 3px rgba(37, 99, 235, 0.25)' : 'none'
                }}
              >
                Tất cả ({totalCount})
              </button>
              <button
                onClick={() => setFilterType('illegal_occupant')}
                style={{
                  background: filterType === 'illegal_occupant' ? 'var(--brand-blue)' : 'transparent',
                  color: filterType === 'illegal_occupant' ? '#FFFFFF' : '#475569',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: filterType === 'illegal_occupant' ? '0 1px 3px rgba(37, 99, 235, 0.25)' : 'none'
                }}
              >
                Khách lậu ({illegalCount})
              </button>
              <button
                onClick={() => setFilterType('missing_guest')}
                style={{
                  background: filterType === 'missing_guest' ? 'var(--brand-blue)' : 'transparent',
                  color: filterType === 'missing_guest' ? '#FFFFFF' : '#475569',
                  border: 'none',
                  padding: '4px 10px',
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: filterType === 'missing_guest' ? '0 1px 3px rgba(37, 99, 235, 0.25)' : 'none'
                }}
              >
                Vắng mặt ({missingCount})
              </button>
            </div>

            {/* Ô tìm kiếm nhanh */}
            <div style={{ position: 'relative', width: 200 }}>
              <span style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', color: '#64748B' }}>
                <Search size={14} />
              </span>
              <input
                type="text"
                placeholder="Tìm phòng, ghế, suất..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="soc-input"
                style={{ width: '100%', boxSizing: 'border-box', paddingLeft: 28, paddingRight: 8, fontSize: 12, height: 30 }}
              />
            </div>
          </div>
        </div>

        {/* NỘI DUNG BẢNG */}
        <div className="table-wrapper">
          <table className="soc-table">
            <thead>
              <tr>
                <th style={{ width: 110 }}>THỜI GIAN</th>
                <th style={{ width: 170 }}>SUẤT CHIẾU</th>
                <th style={{ width: 110 }}>PHÒNG</th>
                <th style={{ width: 90 }}>GHẾ</th>
                <th>VẤN ĐỀ</th>
                <th className="align-right" style={{ width: 170 }}>THAO TÁC</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-state">
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{
                        width: 52,
                        height: 52,
                        borderRadius: 9999,
                        background: '#EFF6FF',
                        border: '1px solid #BFDBFE',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'var(--brand-blue)',
                        marginBottom: 12
                      }}>
                        <ShieldCheck size={30} />
                      </div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#0F172A', marginBottom: 4 }}>
                        Hệ thống an toàn • Không có cảnh báo nào
                      </div>
                      <div style={{ fontSize: 13, color: '#475569', fontWeight: 500 }}>
                        Tất cả phòng chiếu đang hoạt động bình thường, không phát hiện vi phạm chỗ ngồi.
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredAlerts.map(a => {
                  let rowClass = '';
                  let issueBadge = null;

                  if (a.alert_type === 'illegal_occupant') {
                    rowClass = 'row-critical';
                    issueBadge = (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        background: '#FEE2E2',
                        color: '#991B1B',
                        border: '1px solid #FECACA',
                        padding: '3px 9px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 700
                      }}>
                        <UserX size={13} />
                        Khách lậu (Chiếm ghế không vé)
                      </span>
                    );
                  } else if (a.alert_type === 'over_capacity') {
                    rowClass = 'row-capacity';
                    issueBadge = (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        background: '#EFF6FF',
                        color: '#1E40AF',
                        border: '1px solid #BFDBFE',
                        padding: '3px 9px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 700
                      }}>
                        <Users size={13} />
                        Vượt tải (Quá số lượng vé)
                      </span>
                    );
                  } else {
                    rowClass = 'row-warning';
                    issueBadge = (
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        background: '#FEF3C7',
                        color: '#92400E',
                        border: '1px solid #FDE68A',
                        padding: '3px 9px',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 700
                      }}>
                        <UserMinus size={13} />
                        Vắng mặt (Ghế trống đã bán)
                      </span>
                    );
                  }

                  if (a.id === newAlertId) {
                    rowClass += ' new-alert-flash';
                  }

                  return (
                    <tr key={a.id} className={rowClass}>
                      <td className="mono" style={{ color: '#334155', fontWeight: 600 }}>
                        {new Date(a.timestamp).toLocaleTimeString('vi-VN', { hour12: false })}
                      </td>
                      <td className="mono">
                        <span style={{
                          background: '#F8FAFC',
                          border: '1px solid #CBD5E1',
                          padding: '2px 7px',
                          borderRadius: 4,
                          fontSize: 12,
                          color: '#0F172A',
                          fontWeight: 600
                        }}>
                          {a.show_id}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700, color: '#0F172A' }}>
                        {a.room_id}
                      </td>
                      <td className="mono font-bold" style={{ color: '#0F172A', fontSize: 13.5 }}>
                        {a.seat_id || 'N/A'}
                      </td>
                      <td>
                        {issueBadge}
                      </td>
                      <td className="align-right">
                        <button
                          className="action-btn"
                          onClick={() => handleResolve(a.id)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 5,
                            background: '#FFFFFF',
                            border: '1px solid #CBD5E1',
                            color: '#1E293B',
                            padding: '5px 12px',
                            borderRadius: 6,
                            fontSize: 12,
                            fontWeight: 600
                          }}
                        >
                          <Check size={14} />
                          <span>Đã xử lý</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
