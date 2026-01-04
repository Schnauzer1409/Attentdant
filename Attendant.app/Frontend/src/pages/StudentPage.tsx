import React, { useEffect, useState } from 'react';
import { localService } from '../services/localService';
import { commonService } from '../services/commonService';
import { useNavigate } from 'react-router-dom';
import { studentApi } from '../api/studentApi';
import CaptureArea from '../components/CaptureArea';
import { useCapture } from '../hooks/useCapture';

export default function StudentPage() {
    const [msg, setMsg] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const { videoRef, canvasRef, isCapturing, captureError, handleCapture, startCamera, stopCamera } = useCapture();

    useEffect(() => {
        if (captureError) setMsg(captureError)
    }, [captureError])

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    }, [startCamera, stopCamera]);

    const username = localService.get("username") || "Sinh viên";

    const handleLogout = () => {
        commonService.logout()
        navigate('/');
    };

    const captureAttendance = async () => {
        if (isCapturing) return;

        setLoading(true)

        try {
            const blob = await handleCapture();
            if (!blob) return;

            const form = new FormData();
            form.append("username", localStorage.getItem("username") || "");
            form.append("file", blob, "face.jpg");

            const data = await studentApi.attendance(form);
            setMsg(data.msg || data.status);
        } catch (e) {
            console.error(e)
            setMsg("Lỗi kết nối server");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#eef2f3] flex flex-col items-center py-[60px] font-[Arial]">
            <div className="bg-white p-[25px] rounded-[12px] w-[500px] shadow-[0_0_15px_rgba(0,0,0,0.1)] text-center">
                <div className='flex flex-row justify-between'>
                    <h2 className="text-[1.5em] font-bold mb-4">Điểm danh khuôn mặt</h2>
                    <button onClick={handleLogout} className="bg-[#dc3545] text-white px-[20px] py-[10px] rounded-[6px] mb-4 hover:opacity-90">
                        Đăng xuất
                    </button>
                </div>


                <div className="text-[22px] font-bold my-[10px] text-red-600 uppercase">
                    {username}
                </div>

                <CaptureArea videoRef={videoRef} canvasRef={canvasRef} />

                <button
                    onClick={captureAttendance}
                    disabled={loading}
                    className="w-full bg-[#007bff] text-white px-[20px] py-[10px] rounded-[6px] mt-[10px] font-bold hover:bg-[#0056b3] disabled:bg-gray-400"
                >
                    {loading ? "Đang xử lý..." : "Chụp điểm danh"}
                </button>

                <p className="mt-[10px] text-red-600 font-medium min-h-[24px]">{msg}</p>
            </div>
        </div>
    );
};