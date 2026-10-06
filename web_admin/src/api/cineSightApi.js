import axios from 'axios';

// Khi deploy thực tế, đổi thành IP máy chủ AI
const API_BASE = 'http://localhost:8000';

const api = axios.create({ 
  baseURL: API_BASE,
});

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

export const getTicketsList = async (roomId, showId) => {
  const res = await api.get(`/api/v1/tickets?room_id=${roomId}&show_id=${showId}`);
  return res.data.tickets || [];
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

export const addEmployee = async (username, password, name, role) => {
  const res = await api.post('/api/v1/employees', { username, password, name, role });
  return res.data;
};

export const deleteEmployee = async (empId) => {
  const res = await api.delete(`/api/v1/employees/${empId}`);
  return res.data;
};
