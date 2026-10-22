import axios from 'axios';

// Khi deploy thực tế, dùng biến môi trường VITE_API_BASE hoặc fallback localhost:8000
const API_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE) 
  ? import.meta.env.VITE_API_BASE 
  : 'http://localhost:8000';

const api = axios.create({ 
  baseURL: API_BASE,
});

export { API_BASE };

export const analyzeRoom = async (roomId, showId, imageFile) => {
  const formData = new FormData();
  formData.append('room_id', roomId);
  formData.append('show_id', showId);
  formData.append('image', imageFile);
  const res = await api.post('/api/v1/analyze', formData);
  return res.data;
};

export const getActiveAlerts = async (roomId = null) => {
  const url = roomId ? `/api/v1/alerts?room_id=${roomId}` : '/api/v1/alerts';
  const res = await api.get(url);
  return res.data.alerts || [];
};

export const healthCheck = async () => {
  const res = await api.get('/');
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
  const payload = { username, password, name, role };
  if (shift) payload.shift = shift;
  const res = await api.post('/api/v1/employees', payload);
  return res.data;
};

export const deleteEmployee = async (empId) => {
  const res = await api.delete(`/api/v1/employees/${empId}`);
  return res.data;
};

export const updateEmployee = async (empId, username, password, name, role, shift = null) => {
  const payload = { username, password, name, role };
  if (shift) payload.shift = shift;
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

export const resolveIncident = async (id, resolver) => {
  const res = await api.post(`/api/v1/incidents/${id}/resolve`, {
    resolver_id: 1,
    resolver_name: resolver || 'Quản trị viên',
    resolver: resolver || 'Quản trị viên'
  });
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
