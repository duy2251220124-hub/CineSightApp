import axios from 'axios';

// Vấn đề 5 (Phương án 5A): Tự động nhận diện API_BASE
// 1. Ưu tiên biến môi trường VITE_API_BASE nếu có cấu hình
// 2. Khi chạy Vite dev server (cổng 5173) -> gọi http://localhost:8000
// 3. Khi đã build và được phục vụ trực tiếp bởi FastAPI (cùng origin) -> dùng đường dẫn tương đối ""
const resolveApiBase = () => {
  if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) {
    return String(import.meta.env.VITE_API_BASE).trim().replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location) {
    if (window.location.port === '5173') {
      return 'http://localhost:8000';
    }
    return '';
  }
  return 'http://localhost:8000';
};

const API_BASE = resolveApiBase();

const api = axios.create({ 
  headers: { 'ngrok-skip-browser-warning': 'true' },
  baseURL: API_BASE,
});

const AUTH_TOKEN_KEY = 'cinesight_auth_token';
const AUTH_USER_KEY = 'cinesight_auth_user';

export const getStoredToken = () => {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY) || null;
  } catch {
    return null;
  }
};

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem(AUTH_USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || parsed.role !== 'Quản lý') {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_USER_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
};

export const logoutUser = () => {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
  } catch {
    // ignore storage errors
  }
};

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const loginUser = async (username, password) => {
  const res = await api.post('/api/v1/login', {
    username: (username || '').trim(),
    password: (password || '').trim(),
    client: 'web_admin',
  });
  if (res.data && res.data.status === 'success') {
    if (!res.data.user || res.data.user.role !== 'Quản lý') {
      const err = new Error('Forbidden');
      err.response = {
        status: 403,
        data: {
          error: 'Tài khoản Nhân viên (Soát vé) chỉ được đăng nhập trên Mobile App. Vui lòng dùng tài khoản Quản lý cho Web Admin!',
        },
      };
      throw err;
    }
    if (res.data.token) {
      localStorage.setItem(AUTH_TOKEN_KEY, res.data.token);
    }
    if (res.data.user) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(res.data.user));
    }
  }
  return res.data;
};

export { API_BASE };

export const analyzeRoom = async (roomId, showId, imageFile, triggerSource = 'MANUAL') => {
  const formData = new FormData();
  formData.append('room_id', roomId);
  formData.append('show_id', showId);
  formData.append('trigger_source', triggerSource);
  formData.append('image', imageFile);
  const res = await api.post('/api/v1/analyze', formData);
  return res.data;
};

export const triggerPreShowScan = async (roomId, showId, offsetMinutes = -3) => {
  const res = await api.post('/api/v1/scheduler/trigger_pre_show', {
    room_id: roomId,
    show_id: showId,
    offset_minutes: offsetMinutes,
  });
  return res.data;
};

export const getSchedulerStatus = async () => {
  const res = await api.get('/api/v1/scheduler/status');
  return res.data;
};

export const getActiveAlerts = async (roomId = null) => {
  const url = roomId ? `/api/v1/alerts?room_id=${roomId}` : '/api/v1/alerts';
  const res = await api.get(url);
  return res.data.alerts || [];
};

export const getActiveAlertsData = async (roomId = null) => {
  const url = roomId ? `/api/v1/alerts?room_id=${roomId}` : '/api/v1/alerts';
  const res = await api.get(url);
  return res.data || { alerts: [], grouped_alerts: [] };
};

export const resolveRoomAlerts = async (roomId, showId) => {
  const res = await api.post('/api/v1/resolve_room_alerts', {
    room_id: roomId,
    show_id: showId,
  });
  return res.data;
};

export const healthCheck = async () => {
  const res = await api.get('/', {
    headers: { Accept: 'application/json' },
  });
  return res.data;
};

export const resolveAlert = async (alertId) => {
  const res = await api.post(`/api/v1/resolve_alert/${alertId}`);
  return res.data;
};

export const getAlertHistory = async (roomId, alertType, status) => {
  let url = '/api/v1/alerts/history?';
  if (roomId) url += `room_id=${roomId}&`;
  if (alertType) url += `alert_type=${alertType}&`;
  if (status) url += `status=${status}`;
  
  const res = await api.get(url);
  return res.data.alerts || [];
};

export const getRoomsConfig = async () => {
  const res = await api.get('/api/v1/rooms');
  return res.data.rooms || [];
};

export const getShowtimes = async (roomId = null, date = null) => {
  const params = {};
  if (roomId) params.room_id = roomId;
  if (date) params.date = date;
  const res = await api.get('/api/v1/showtimes', { params });
  return res.data.showtimes || [];
};

export const getTicketsList = async (roomId, showId) => {
  const params = {};
  if (roomId) params.room_id = roomId;
  if (showId && showId !== 'undefined' && showId !== 'null') params.show_id = showId;
  const res = await api.get('/api/v1/tickets', { params });
  return res.data.tickets || [];
};

export const clearTickets = async (roomId = null, showId = null) => {
  const params = {};
  if (roomId) params.room_id = roomId;
  if (showId && showId !== 'undefined' && showId !== 'null') params.show_id = showId;
  const res = await api.delete('/api/v1/tickets', { params });
  return res.data;
};

export const getConfigs = async () => {
  const res = await api.get('/api/v1/configs');
  return res.data.configs || {};
};

export const updateConfig = async (key, value) => {
  const res = await api.post('/api/v1/configs', { key, value });
  return res.data;
};

export const getEmployees = async () => {
  const res = await api.get('/api/v1/employees');
  return res.data.employees || [];
};

export const getShifts = async () => {
  const res = await api.get('/api/v1/shifts');
  return res.data.shifts || [];
};

export const addEmployee = async (username, password, name, role, shift = null) => {
  const payload = { username, password, name, role: role || 'Soát vé' };
  if (shift) payload.shift = shift;
  const res = await api.post('/api/v1/employees', payload);
  return res.data;
};

export const deleteEmployee = async (empId) => {
  const res = await api.delete(`/api/v1/employees/${empId}`);
  return res.data;
};

export const updateEmployee = async (empId, username, password, name, role, shift = null, isActive = null) => {
  const payload = { username, password, name, role };
  if (shift !== undefined) payload.shift = shift;
  if (isActive !== null && isActive !== undefined) payload.is_active = isActive;
  const res = await api.put(`/api/v1/employees/${empId}`, payload);
  return res.data;
};

export const getIncidents = async (params = {}) => {
  const res = await api.get('/api/v1/incidents', { params });
  return res.data.incidents || [];
};

export const getIncident = async (id) => {
  const res = await api.get(`/api/v1/incidents/${id}`);
  return res.data.incident || null;
};

export const resolveIncident = async (id, resolverId = null) => {
  const storedUser = getStoredUser();
  const effectiveResolverId = resolverId || (storedUser && storedUser.id) || null;
  const payload = effectiveResolverId ? { resolver_id: effectiveResolverId } : {};
  const res = await api.post(`/api/v1/incidents/${id}/resolve`, payload);
  return res.data;
};

export const deleteIncident = async (id) => {
  const res = await api.delete(`/api/v1/incidents/${id}`);
  return res.data;
};

export const clearResolvedIncidents = async () => {
  const res = await api.delete('/api/v1/incidents/resolved/clear');
  return res.data;
};

export const getIncidentCategories = async () => {
  const res = await api.get('/api/v1/incident_categories');
  return res.data.categories || [];
};

export const getMovies = async (activeOnly = true) => {
  const res = await api.get('/api/v1/movies', { params: { active_only: activeOnly } });
  return res.data.movies || [];
};

export const getRoomSeats = async (roomId) => {
  const res = await api.get(`/api/v1/rooms/${roomId}/seats`);
  return res.data;
};
