import { useState, useEffect, useMemo } from 'react';
import { healthCheck, getActiveAlertsData, resolveAlert, resolveRoomAlerts } from '../api/cineSightApi';
import {
  ShieldAlert,
  ShieldCheck,
  UserX,
  UserMinus,
  Users,
  Search,
  Check
} from '../components/Icons';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [serverOnline, setServerOnline] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [groupedAlerts, setGroupedAlerts] = useState([]);
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

  // Tải danh sách cảnh báo (cả bản ghi chi tiết và nhóm theo phòng)
  const fetchAlerts = async () => {
    try {
      const data = await getActiveAlertsData();
      setAlerts(data.alerts || []);
      setGroupedAlerts(data.grouped_alerts || []);
    } catch (e) {
      console.error('Lỗi tải danh sách cảnh báo:', e);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const alertTimer = setInterval(fetchAlerts, 5000);
    return () => clearInterval(alertTimer);
  }, []);

  const handleResolve = async (id, resolution = 'violation_handled') => {
    try {
      await resolveAlert(id, resolution);
      await fetchAlerts();
    } catch (e) {
      alert('Không thể cập nhật trạng thái: ' + e.message);
    }
  };

  const handleResolveRoom = async (roomId, showId, resolution = 'violation_handled') => {
    try {
      await resolveRoomAlerts(roomId, showId, resolution);
      await fetchAlerts();
    } catch (e) {
      alert('Không thể xử lý cảnh báo phòng: ' + (e.response?.data?.error || e.message));
    }
  };

  // Tính toán số liệu thống kê
  const illegalCount = alerts.filter(a => a.alert_type === 'illegal_occupant' || a.alert_type === 'duplicate_scan' || a.alert_type === 'forged_ticket').length;
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
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: serverOnline ? '#10B981' : '#DC2626',
              flexShrink: 0
            }} />
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

      {/* 3. BẢNG CẢNH BÁO CHỜ XỬ LÝ (LIVE FEED) VỚI TOOLBAR */}
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

        {/* PHIẾU ĐIỀU HÀNH PHÒNG CHIẾU CÓ CẢNH BÁO (GOM NHÓM & XỬ LÝ 1 CHẠM) */}
        {groupedAlerts.length > 0 && (
          <div style={{ padding: '0 16px 12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {groupedAlerts.map(g => (
              <div
                key={`${g.room_id}-${g.show_id}`}
                style={{
                  background: '#FEF2F2',
                  border: '1.5px solid #FECACA',
                  borderRadius: 8,
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontWeight: 800, fontSize: 13.5, color: '#991B1B' }}>
                      🚨 {g.room_id.toUpperCase()} • SUẤT {g.show_id}
                    </span>
                    <span style={{
                      background: '#FEE2E2',
                      color: '#991B1B',
                      fontSize: 11,
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: 4,
                      border: '1px solid #FECACA',
                    }}>
                      {g.total_alerts} ghế bất thường
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 18, fontSize: 13, color: '#334155', flexWrap: 'wrap' }}>
                    <span>🎟️ Số vé đã quét: <strong style={{ color: '#0F172A' }}>{g.scanned_tickets_count}</strong></span>
                    <span>👥 Số người hiện có: <strong style={{ color: '#0F172A' }}>{g.detected_people_count}</strong></span>
                    <span>⚠️ Ghế cảnh báo: <strong style={{ color: '#DC2626' }}>{g.all_alerted_seats.join(', ') || 'N/A'}</strong></span>
                    {g.vip_seat_hopping && g.vip_seat_hopping.length > 0 && (
                      <span style={{ color: '#B45309', fontWeight: 700 }}>
                        🔄 VIP Seat Hopping: {g.vip_seat_hopping.map(p => `${p.from_seat} ➔ VIP ${p.to_seat}`).join(', ')}
                      </span>
                    )}
                    {g.duplicate_scan_seats && g.duplicate_scan_seats.length > 0 && (
                      <span style={{ color: '#991B1B', fontWeight: 700 }}>
                        ⚠️ Quét trùng đa thiết bị: {g.duplicate_scan_seats.join(', ')}
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button
                    onClick={() => handleResolveRoom(g.room_id, g.show_id, 'violation_handled')}
                    style={{
                      background: '#DC2626',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 14px',
                      borderRadius: 6,
                      fontWeight: 700,
                      fontSize: 12,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      boxShadow: '0 2px 4px rgba(220, 38, 38, 0.25)',
                    }}
                  >
                    <Check size={14} />
                    <span>XỬ LÝ VI PHẠM ({g.total_alerts} GHẾ)</span>
                  </button>
                  <button
                    onClick={() => handleResolveRoom(g.room_id, g.show_id, 'ticket_verified')}
                    style={{
                      background: '#059669',
                      color: '#FFFFFF',
                      border: 'none',
                      padding: '8px 14px',
                      borderRadius: 6,
                      fontWeight: 700,
                      fontSize: 12,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <Check size={14} />
                    <span>VÉ HỢP LỆ SÓT QUÉT (BỔ SUNG TẬP A)</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

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
                        {a.suspected_type === 'vip_seat_hopping'
                          ? `🔄 Tự ý nâng hạng VIP (từ ghế Thường ${a.hopping_from})`
                          : `Khách lậu (Chiếm ghế ${a.seat_tier === 'VIP' ? 'VIP' : 'Thường'} không vé)`}
                      </span>
                    );
                  } else if (a.alert_type === 'duplicate_scan') {
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
                        ⚠️ Gian lận quét trùng vé đa thiết bị
                      </span>
                    );
                  } else if (a.alert_type === 'forged_ticket') {
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
                        🚨 Vé giả mạo chữ ký số HMAC-SHA256
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
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button
                            className="action-btn"
                            onClick={() => handleResolve(a.id, 'violation_handled')}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 4,
                              background: '#FFFFFF',
                              border: '1px solid #CBD5E1',
                              color: '#1E293B',
                              padding: '5px 10px',
                              borderRadius: 6,
                              fontSize: 11.5,
                              fontWeight: 600
                            }}
                          >
                            <Check size={13} />
                            <span>Xử lý vi phạm</span>
                          </button>
                          {a.alert_type === 'illegal_occupant' && (
                            <button
                              className="action-btn"
                              onClick={() => handleResolve(a.id, 'ticket_verified')}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                                background: '#ECFDF5',
                                border: '1px solid #6EE7B7',
                                color: '#065F46',
                                padding: '5px 10px',
                                borderRadius: 6,
                                fontSize: 11.5,
                                fontWeight: 700
                              }}
                              title="Khách có vé hợp lệ bị sót quét - Bổ sung vào Tập A"
                            >
                              <Check size={13} />
                              <span>Có vé (Bổ sung Tập A)</span>
                            </button>
                          )}
                        </div>
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
