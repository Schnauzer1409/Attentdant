import axiosClient from "./axiosClient"

export const studentApi = {
    attendance: async (form: FormData) => {
        const response  = await axiosClient.post('/api/attendance', form);
        return response.data
    }
}