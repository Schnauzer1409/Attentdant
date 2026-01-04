import axiosClient from "./axiosClient";

export const authApi = {
    login: async (formData: FormData) => {
    const response = await axiosClient.post('/api/login', formData);
    return response.data;
  },
}