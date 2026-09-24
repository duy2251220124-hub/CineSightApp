import axios from 'axios';

// Khi deploy thá»±c táº¿, Ä‘á»•i thÃ nh IP mÃ¡y chá»§ AI
const API_BASE = 'https://quill-device-deny.ngrok-free.dev';

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



