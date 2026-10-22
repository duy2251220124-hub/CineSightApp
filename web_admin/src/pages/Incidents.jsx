import { useState, useEffect, useMemo } from 'react';
import { getIncidents, resolveIncident, getIncidentCategories } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Hiệu ứng cảnh báo mới
  const [newIncidentId, setNewIncidentId] = useState(null);

  // Bộ lọc
  const [statusFilter, setStatusFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [roomFilter, setRoomFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  const [selectedIncident, setSelectedIncident] = useState(null);

  useEffect(() => {
    let currentIds = new Set();

    const initFetch = async () => {
      setLoading(true);
      setError(null);
      try {
        const [cats, data] = await Promise.all([
          getIncidentCategories(),
          getIncidents()
        ]);
        setCategories(cats);
        setIncidents(data);
        currentIds = new Set(data.map(i => i.id));
      } catch (e) {
        setError("Lỗi kết nối đến máy chủ. Vui lòng thử lại.");
      }
      setLoading(false);
    };

    initFetch();

    // Polling 5s
    const interval = setInterval(async () => {
      try {
        const data = await getIncidents();
        setIncidents(data);
        
        // Kiểm tra sự cố mới để chớp flash
        const newIds = data.filter(i => !currentIds.has(i.id)).map(i => i.id);
        if (newIds.length > 0 && currentIds.size > 0) {
          setNewIncidentId(newIds[0]); // Chớp dòng mới nhất
          setTimeout(() => setNewIncidentId(null), 3000);
        }
        currentIds = new Set(data.map(i => i.id));
      } catch (e) {
        console.error("Lỗi polling: ", e);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Giữ nguyên panel chi tiết nếu sự cố đang mở được cập nhật (ví dụ: bị ai đó resolve)
  useEffect(() => {
    if (selectedIncident) {
      const updated = incidents.find(i => i.id === selectedIncident.id);
      if (updated && updated.status !== selectedIncident.status) {
        setSelectedIncident(updated);
      }
    }
  }, [incidents, selectedIncident]);

  const handleResolve = async (id) => {
    // Không tự bịa người xử lý vì chưa có login.
    const resolver = window.prompt("Hệ thống chưa có đăng nhập. Vui lòng nhập tên người xử lý:", "Admin");
    if (!resolver) return;

    try {
      await resolveIncident(id, resolver);
      setIncidents(prev => prev.map(inc => 
        inc.id === id ? { ...inc, status: 'resolved', resolved_by_name: resolver, resolved_at: new Date().toISOString() } : inc
      ));
    } catch (e) {
      alert("Không thể đánh dấu xử lý: " + e.message);
    }
  };

  const openCount = incidents.filter(i => i.status === 'open').length;
  const highCount = incidents.filter(i => i.status === 'open' && i.severity === 'high').length;
  const resolvedToday = incidents.filter(i => {
    if (i.status !== 'resolved' || !i.resolved_at) return false;
    const date = new Date(i.resolved_at);
    const today = new Date();
    return date.getDate() === today.getDate() && date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
  }).length;

  const rooms = useMemo(() => {
    const r = new Set(incidents.map(i => i.room_id).filter(Boolean));
    return Array.from(r);
  }, [incidents]);

  const filtered = useMemo(() => {
    return incidents.filter(i => {
      if (statusFilter !== 'all' && i.status !== statusFilter) return false;
      if (categoryFilter !== 'all' && i.category !== categoryFilter) return false;
      if (severityFilter !== 'all' && i.severity !== severityFilter) return false;
      if (roomFilter !== 'all' && i.room_id !== roomFilter) return false;
      
      if (dateFilter !== 'all') {
        const d = new Date(i.created_at);
        const today = new Date();
        if (dateFilter === 'today') {
           if (d.getDate() !== today.getDate() || d.getMonth() !== today.getMonth() || d.getFullYear() !== today.getFullYear()) return false;
        } else if (dateFilter === '7days') {
           const diff = (today - d) / (1000 * 60 * 60 * 24);
           if (diff > 7) return false;
        }
      }
      
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (!i.title?.toLowerCase().includes(q) && 
            !i.description?.toLowerCase().includes(q) &&
            !i.room_id?.toLowerCase().includes(q) &&
            !i.seat_ids?.toLowerCase().includes(q) &&
            !i.reporter_name?.toLowerCase().includes(q)) {
          return false;
        }
      }
      return true;
    }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }, [incidents, statusFilter, categoryFilter, severityFilter, roomFilter, dateFilter, searchQuery]);

  const getCategoryLabel = (code) => {
    const c = categories.find(x => x.code === code);
    return c ? c.label : code;
  };

  const formatSeats = (seatStr) => {
    if (!seatStr) return '--';
    try {
      const arr = JSON.parse(seatStr);
      if (Array.isArray(arr)) return arr.join(', ');
    } catch (e) {}
    return seatStr;
  };

  const formatTime = (isoString) => {
    if (!isoString) return '--';
    const d = new Date(isoString);
    const today = new Date();
    const isToday = d.getDate() === today.getDate() && d.getMonth() === today.getMonth() && d.getFullYear() === today.getFullYear();
    const timeStr = d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    return isToday ? timeStr : `${timeStr} ${d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit'})}`;
  };

  const formatShow = (showId) => {
    if (!showId) return '--';
    const d = new Date(showId);
    if (isNaN(d)) return showId;
    return `Suất ${d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })} · ${d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })}`;
  };

  return (
    <div className="soc-container" style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none', flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div className="soc-brand" style={{ color: 'var(--brand-blue)' }}>QUẢN LÝ THÔNG BÁO</div>
        </div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          DATABASE: SẴN SÀNG
        </div>
      </header>

      {/* THANH LỌC (Đưa lên trên theo yêu cầu) */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 16, flexShrink: 0, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Trạng thái</label>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="soc-input" style={{ width: 110 }}>
            <option value="all">Tất cả</option>
            <option value="open">Đang chờ</option>
            <option value="resolved">Đã xử lý</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Loại sự cố</label>
          <select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)} className="soc-input" style={{ width: 140 }}>
            <option value="all">Tất cả</option>
            {categories.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Mức độ</label>
          <select value={severityFilter} onChange={e => setSeverityFilter(e.target.value)} className="soc-input" style={{ width: 100 }}>
            <option value="all">Tất cả</option>
            <option value="high">Cao</option>
            <option value="normal">Bình thường</option>
            <option value="low">Thấp</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Phòng</label>
          <select value={roomFilter} onChange={e => setRoomFilter(e.target.value)} className="soc-input" style={{ width: 140 }}>
            <option value="all">Tất cả</option>
            {rooms.map(r => (
              <option key={r} value={r}>
                {r === 'room1' ? 'Phòng chiếu 1' : r === 'room2' ? 'Phòng chiếu 2' : r === 'room3' ? 'Phòng chiếu 3' : r === 'room4' ? 'Phòng chiếu 4' : r}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Thời gian</label>
          <select value={dateFilter} onChange={e => setDateFilter(e.target.value)} className="soc-input" style={{ width: 110 }}>
            <option value="all">Tất cả</option>
            <option value="today">Hôm nay</option>
            <option value="7days">7 ngày qua</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 200 }}>
          <label style={{ fontSize: 12, color: 'var(--text-dim)' }}>Tìm kiếm</label>
          <input 
            type="text" 
            placeholder="Tìm theo tiêu đề, phòng, ghế..." 
            className="soc-input" 
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* THANH CHỈ SỐ */}
      <div className="soc-panel" style={{ flexShrink: 0, marginBottom: 16 }}>
        <div className="stats-bar">
          <div className="stat-item" style={{ flex: 1, justifyContent: 'center' }}>
            <span className="stat-label">ĐANG CHỜ XỬ LÝ:</span>
            <span className="stat-val" style={{ color: openCount > 0 ? '#ffb86c' : 'var(--text-dim)' }}>{openCount}</span>
          </div>
          <div className="stat-item" style={{ flex: 1, justifyContent: 'center' }}>
            <span className="stat-label">SỰ CỐ MỨC CAO:</span>
            <span className="stat-val" style={{ color: highCount > 0 ? 'var(--alert-red)' : 'var(--text-dim)' }}>{highCount}</span>
          </div>
          <div className="stat-item" style={{ flex: 1, justifyContent: 'center', borderRight: 'none' }}>
            <span className="stat-label">ĐÃ XỬ LÝ HÔM NAY:</span>
            <span className="stat-val" style={{ color: '#14C692' }}>{resolvedToday}</span>
          </div>
        </div>
      </div>

      {/* CONTENT AREA: Split Pane */}
      <div style={{ display: 'flex', flex: 1, gap: 16, minHeight: 0 }}>
        {/* BẢNG DỮ LIỆU */}
        <div className="soc-panel soc-feed" style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, overflow: 'hidden' }}>
          {error ? (
             <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32 }}>
               <div style={{ color: 'var(--alert-red)', fontWeight: 600, marginBottom: 8 }}>{error}</div>
               <button className="soc-btn" onClick={() => window.location.reload()}>Thử lại</button>
             </div>
          ) : loading && incidents.length === 0 ? (
             <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
               Đang tải dữ liệu...
             </div>
          ) : (
            <div className="table-wrapper" style={{ flex: 1, overflowY: 'auto' }}>
              <table className="soc-table">
                <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--surface)', zIndex: 1, boxShadow: '0 1px 0 var(--grid-line)' }}>
                  <tr>
                    <th>Thời gian</th>
                    <th>Loại</th>
                    <th>Mức độ</th>
                    <th>Phòng</th>
                    <th>Suất chiếu</th>
                    <th>Ghế</th>
                    <th>Người báo</th>
                    <th>Trạng thái</th>
                    <th className="align-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="empty-state">
                        {incidents.length === 0 ? "Chưa có sự cố nào được báo." : "Không tìm thấy sự cố nào phù hợp với bộ lọc."}
                      </td>
                    </tr>
                  ) : filtered.map(inc => {
                    const isHigh = inc.severity === 'high' && inc.status === 'open';
                    const isSelected = selectedIncident?.id === inc.id;
                    
                    let rowClasses = [];
                    if (isHigh) rowClasses.push('row-critical');
                    if (inc.id === newIncidentId) rowClasses.push('new-alert-flash'); // Hiệu ứng chớp

                    return (
                      <tr 
                        key={inc.id} 
                        className={rowClasses.join(' ')}
                        onClick={() => setSelectedIncident(inc)}
                        style={{ 
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'rgba(0, 243, 255, 0.1)' : undefined
                        }}
                      >
                        <td className="mono" style={{ whiteSpace: 'nowrap' }}>
                          {formatTime(inc.created_at)}
                        </td>
                        <td>{getCategoryLabel(inc.category)}</td>
                        <td className={isHigh ? 'alert-red' : ''}>
                          {inc.severity === 'high' ? 'Cao' : inc.severity === 'low' ? 'Thấp' : 'Bình thường'}
                        </td>
                        <td>
                          {inc.room_id === 'room1' ? 'Phòng chiếu 1' : inc.room_id === 'room2' ? 'Phòng chiếu 2' : inc.room_id === 'room3' ? 'Phòng chiếu 3' : inc.room_id === 'room4' ? 'Phòng chiếu 4' : (inc.room_id || '--')}
                        </td>
                        <td>{formatShow(inc.show_id)}</td>
                        <td className="mono">{formatSeats(inc.seat_ids)}</td>
                        <td>
                          <div>{inc.reporter_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{inc.shift_label || 'Chưa phân ca'}</div>
                        </td>
                        <td>
                          {inc.status === 'open' ? (
                            <span style={{ color: '#ffb86c' }}>Đang chờ</span>
                          ) : (
                            <span style={{ color: '#14C692' }}>Đã xử lý</span>
                          )}
                        </td>
                        <td className="align-right">
                          {inc.status === 'open' && (
                            <button 
                              className="soc-btn action-btn" 
                              style={{ color: 'var(--brand-blue)', borderColor: 'rgba(0, 243, 255, 0.3)' }}
                              onClick={(e) => { e.stopPropagation(); handleResolve(inc.id); }}
                            >
                              XỬ LÝ
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* CHI TIẾT SỰ CỐ PANEL */}
        <div className="soc-panel" style={{ width: 350, display: 'flex', flexDirection: 'column', flexShrink: 0, padding: 0, overflow: 'hidden' }}>
          {!selectedIncident ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', textAlign: 'center', padding: 32 }}>
              <div>Chọn một sự cố trong danh sách để xem chi tiết</div>
            </div>
          ) : (
            <>
              <div style={{ padding: '16px', borderBottom: '1px solid var(--grid-line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 600, color: 'var(--brand-blue)' }}>CHI TIẾT SỰ CỐ #{selectedIncident.id}</div>
                <button 
                  onClick={() => setSelectedIncident(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: 18 }}
                  title="Đóng"
                >
                  ✕
                </button>
              </div>
              
              <div style={{ padding: 16, overflowY: 'auto', flex: 1 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Tiêu đề</div>
                  <div style={{ fontSize: 16, fontWeight: 600, marginTop: 4 }}>{selectedIncident.title}</div>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Mô tả</div>
                  <div style={{ marginTop: 4, whiteSpace: 'pre-wrap', color: 'var(--text-main)', lineHeight: 1.5 }}>
                    {selectedIncident.description || 'Không có mô tả chi tiết.'}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Loại sự cố</div>
                    <div style={{ marginTop: 4 }}>{getCategoryLabel(selectedIncident.category)}</div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Mức độ</div>
                    <div style={{ marginTop: 4, color: selectedIncident.severity === 'high' && selectedIncident.status === 'open' ? 'var(--alert-red)' : 'inherit' }}>
                      {selectedIncident.severity === 'high' ? 'Cao' : selectedIncident.severity === 'low' ? 'Thấp' : 'Bình thường'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Phòng chiếu</div>
                    <div style={{ marginTop: 4, fontWeight: 600, color: '#0F172A' }}>
                      {selectedIncident.room_id === 'room1' ? 'Phòng chiếu 1' : selectedIncident.room_id === 'room2' ? 'Phòng chiếu 2' : selectedIncident.room_id === 'room3' ? 'Phòng chiếu 3' : selectedIncident.room_id === 'room4' ? 'Phòng chiếu 4' : (selectedIncident.room_id || '--')}
                    </div>
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, color: 'var(--text-dim)' }}>Danh sách ghế</div>
                    <div className="mono" style={{ marginTop: 4 }}>{formatSeats(selectedIncident.seat_ids)}</div>
                  </div>
                </div>

                <div style={{ marginBottom: 16, padding: 12, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 4 }}>
                  <div style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 8 }}>Thông tin người báo</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr', gap: 4 }}>
                    <span style={{ color: 'var(--text-dim)' }}>Người báo:</span> 
                    <span>{selectedIncident.reporter_name} ({selectedIncident.reporter_role})</span>
                    <span style={{ color: 'var(--text-dim)' }}>Ca làm việc:</span> 
                    <span>{selectedIncident.shift_label || '--'}</span>
                    <span style={{ color: 'var(--text-dim)' }}>Thời gian:</span> 
                    <span className="mono">{formatTime(selectedIncident.created_at)}</span>
                  </div>
                </div>

                {selectedIncident.status === 'resolved' && (
                  <div style={{ marginBottom: 16, padding: 12, backgroundColor: 'rgba(20, 198, 146, 0.1)', borderRadius: 4, border: '1px solid rgba(20, 198, 146, 0.2)' }}>
                    <div style={{ fontSize: 12, color: '#14C692', marginBottom: 8, fontWeight: 600 }}>THÔNG TIN XỬ LÝ</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr', gap: 4 }}>
                      <span style={{ color: 'var(--text-dim)' }}>Người xử lý:</span> 
                      <span>{selectedIncident.resolved_by_name}</span>
                      <span style={{ color: 'var(--text-dim)' }}>Thời gian:</span> 
                      <span className="mono">{formatTime(selectedIncident.resolved_at)}</span>
                    </div>
                  </div>
                )}
              </div>

              {selectedIncident.status === 'open' && (
                <div style={{ padding: 16, borderTop: '1px solid var(--grid-line)' }}>
                  <button 
                    className="soc-btn primary" 
                    style={{ width: '100%', padding: '12px', fontSize: 14 }}
                    onClick={() => handleResolve(selectedIncident.id)}
                  >
                    ĐÁNH DẤU ĐÃ XỬ LÝ
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
