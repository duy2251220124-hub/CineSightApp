import axios from 'axios';

// Khi deploy thực tế, đổi thành IP máy chủ AI
const API_BASE = 'http://127.0.0.1:8000';

const api = axios.create({ baseURL: API_BASE });

export const analyzeRoom = async (roomId, imageFile) => {
  const formData = new FormData();
  formData.append('room_id', roomId);
  formData.append('image', imageFile);
  const res = await api.post('/api/v1/analyze', formData);
  return res.data;
};

export const healthCheck = async () => {
  const res = await api.get('/');
  return res.data;
};

