import axiosClient from './axiosClient';

export const teacherApi = {
  enroll: (formData: FormData) => 
    axiosClient.post('/api/enroll', formData).then(res => res.data),

  uploadWatermark: (formData: FormData) => 
    axiosClient.post('/api/upload_watermark', formData).then(res => res.data),

  generateWatermark: (formData: FormData) => 
    axiosClient.post('/api/teacher_generate_watermark', formData).then(res => res.data),

  setWatermark: () => 
    axiosClient.post('/api/set_watermark').then(res => res.data),

  clearEncodings: () => 
    axiosClient.get('/api/clear_encodings').then(res => res.data),
};