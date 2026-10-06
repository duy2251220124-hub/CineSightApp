import { useState, useEffect } from 'react';
import { getConfigs, updateConfig } from '../api/cineSightApi';
import '../styles/dashboard.css';

export default function Settings() {
  const [capacityThreshold, setCapacityThreshold] = useState('0');
  const [configSaving, setConfigSaving] = useState(false);

  const fetchInitialData = async () => {
    try {
      const conf = await getConfigs();
      if (conf.capacity_threshold) setCapacityThreshold(conf.capacity_threshold);
    } catch (e) {
      alert("Lỗi tải dữ liệu Settings: " + e.message);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const handleSaveConfig = async () => {
    setConfigSaving(true);
    try {
      await updateConfig('capacity_threshold', capacityThreshold);
      alert('Đã lưu cấu hình!');
    } catch (e) {
      alert('Lỗi lưu cấu hình: ' + e.message);
    }
    setConfigSaving(false);
  };

  return (
    <div className="soc-container">
      <header className="soc-header" style={{ paddingBottom: 12, borderBottom: 'none' }}>
        <div className="soc-brand">CÀI ĐẶT HỆ THỐNG</div>
        <div className="soc-status">
          <span className="status-indicator online"></span>
          SETTINGS SERVER: SẴN SÀNG
        </div>
      </header>

      <div className="soc-controls-row" style={{ height: 'auto', flex: 1, alignItems: 'flex-start' }}>
        {/* PANEL: CẤU HÌNH */}
        <div className="soc-panel" style={{ flex: 1, maxWidth: 600 }}>
          <div className="panel-title">THÔNG SỐ VẬN HÀNH</div>
          <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div>
              <label style={{ display: 'block', marginBottom: 8, fontSize: 13, color: 'var(--text-dim)', fontWeight: 600 }}>
                NGƯỠNG CẢNH BÁO VƯỢT TẢI (SỐ NGƯỜI)
              </label>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <input 
                  type="number" 
                  min="0" 
                  className="soc-input" 
                  style={{ width: 100, fontSize: 16 }}
                  value={capacityThreshold}
                  onChange={e => setCapacityThreshold(e.target.value)}
                />
                <span style={{ fontSize: 13, color: 'var(--text-dim)' }}>
                  (Dư bao nhiêu người so với Tập A thì kích hoạt cảnh báo đỏ)
                </span>
              </div>
            </div>
            
            <div style={{ borderTop: '1px solid var(--grid-line)', paddingTop: 24 }}>
              <button 
                className="soc-btn primary" 
                onClick={handleSaveConfig} 
                disabled={configSaving}
                style={{ width: '100%', padding: '12px' }}
              >
                {configSaving ? 'ĐANG LƯU...' : 'LƯU CẤU HÌNH'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
