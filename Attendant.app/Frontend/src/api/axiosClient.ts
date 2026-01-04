import axios from 'axios';

const axiosClient = axios.create({
  // Lấy từ biến môi trường
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'multipart/form-data', // Mặc định cho form data điểm danh
    'ngrok-skip-browser-warning': 'true',
  },
});

// Interceptor: Tự động đính kèm Token vào mọi request nếu có
axiosClient.interceptors.request.use((config) => {
// config.headers['ngrok-skip-browser-warning'] = 'true';
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default axiosClient;