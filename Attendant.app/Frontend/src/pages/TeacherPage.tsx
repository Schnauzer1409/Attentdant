import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { teacherApi } from '../api/teacherApi';
import { useCapture } from '../hooks/useCapture';
import CaptureArea from '../components/CaptureArea';
import { commonService } from '../services/commonService';

export default function TeacherPage() {
    const [tab, setTab] = useState<'enroll' | 'watermark'>('enroll');
    const [studentId, setStudentId] = useState('');
    const [msg, setMsg] = useState('');
    const [wmImg, setWmImg] = useState<string | null>(null);
    const [showSetBtn, setShowSetBtn] = useState(false);

    const navigate = useNavigate();

    const { videoRef, canvasRef, isCapturing, captureError, handleCapture, startCamera, stopCamera } = useCapture();
    

    useEffect(() => {
        startCamera();
        return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tab]);

    useEffect(() => {
        if (captureError) setMsg(captureError)
    }, [captureError])

    // --- LOGIC ENROLL ---
    const handleEnroll = async () => {
        if (!studentId.trim()) return setMsg("Vui lòng nhập MSSV");
        if (isCapturing) return ;

        const blob = await handleCapture();
        if (!blob) return;

        const form = new FormData();
        form.append("username", studentId);
        form.append("file", blob, "enroll.jpg");

        try {
            const data = await teacherApi.enroll(form);
            setMsg(data.msg || data.status);
        } catch (err) {
            console.error(err)
            setMsg("Lỗi khi enroll sinh viên");
        }
    };

    // --- LOGIC WATERMARK ---
    const processWatermarkFlow = async (file: File | Blob) => {
        setMsg("Đang xử lý watermark...");
        const form = new FormData();
        form.append("file", file);

        try {
            // Gọi upload
            await teacherApi.uploadWatermark(form);
            // Gọi generate và nhận trực tiếp data
            const dataGen = await teacherApi.generateWatermark(form);

            setWmImg(dataGen.watermark);
            setShowSetBtn(true);
            setMsg("Ảnh đã cắt phía dưới. Ấn 'Set watermark' để xác nhận.");
        } catch (err) {
            console.error(err)
            setMsg("Lỗi xử lý watermark");
        }
    };

    const captureWatermark = async () => {
        const blob = await handleCapture();
        if (blob) processWatermarkFlow(blob);
    };

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) processWatermarkFlow(file);
    };

    const confirmSetWatermark = async () => {
        try {
            const data = await teacherApi.setWatermark();
            if (data.status === "ok") {
                setShowSetBtn(false);
                setMsg("✓ Đã xác nhận watermark thành công");
            }
        } catch (err) {
            console.error(err)
            setMsg("Lỗi xác nhận watermark");
        }
    };

    const clearEncodings = async () => {
        if (!confirm("Bạn có chắc muốn xóa toàn bộ dữ liệu khuôn mặt không?")) return;
        try {
            const data = await teacherApi.clearEncodings();
            alert(data.msg);
        } catch (err) {
            console.error(err)
            alert("Lỗi khi xóa dữ liệu");
        }
    };

    const handleLogout = () => {
        commonService.logout();
        navigate('/');
    }

    return (
        <div className="min-h-screen bg-[#eef2f3] py-[60px] font-[Arial]">
            <div className="max-w-[450px] mx-auto bg-white p-[25px] rounded-[12px] shadow-lg text-center">
                <div className='flex flex-row justify-between'>
                    <h2 className="text-xl font-bold mb-4">Trang giáo viên</h2>
                    <button onClick={handleLogout} className="bg-[#dc3545] text-white px-4 py-2 rounded-md mb-6">Đăng xuất</button>
                </div>
                
                <div className="flex gap-2 mb-6 justify-center">
                    <button onClick={() => setTab('enroll')} className={`flex-1 px-4 py-2 rounded-md font-bold ${tab === 'enroll' ? 'bg-[#4CAF50] text-white' : 'bg-gray-200'}`}>Enroll Sinh Viên</button>
                    <button onClick={() => setTab('watermark')} className={`flex-1 px-4 py-2 rounded-md font-bold ${tab === 'watermark' ? 'bg-[#4CAF50] text-white' : 'bg-gray-200'}`}>Watermark</button>
                </div>

                {tab === 'enroll' ? (
                    <div>
                        <h3 className="font-bold mb-2">Thêm ảnh mẫu (Enroll)</h3>
                        <input
                            type="text" placeholder="Nhập MSSV"
                            className="w-full p-2 border rounded-md mb-4 outline-none border-[#bbb]"
                            value={studentId} onChange={(e) => setStudentId(e.target.value)}
                        />
                        <CaptureArea videoRef={videoRef} canvasRef={canvasRef} />
                        <button onClick={handleEnroll} className="mt-5 w-full bg-[#007bff] text-white py-2 rounded-md font-bold">Chụp ảnh & Enroll</button>
                    </div>
                ) : (
                    <div>
                        <h3 className="font-bold mb-2">Quản lý Watermark</h3>
                        <CaptureArea videoRef={videoRef} canvasRef={canvasRef} />
                        <button onClick={captureWatermark} className="mt-5 w-full bg-[#007bff] text-white py-2 rounded-md font-bold mb-4">Chụp ảnh watermark</button>

                        <div className="border-t pt-4">
                            <p className="text-sm mb-2 text-gray-500">Hoặc upload file ảnh:</p>
                            <input type="file" accept="image/*" onChange={handleFileUpload} className="mb-4 text-sm" />
                        </div>

                        {wmImg && (
                            <div className="mt-4 p-2 bg-gray-50 rounded">
                                <img src={`data:image/jpeg;base64,${wmImg}`} className="mx-auto w-[150px] border shadow-sm" alt="Preview" />
                                {showSetBtn && (
                                    <button onClick={confirmSetWatermark} className="mt-2 bg-green-600 text-white px-4 py-2 rounded-md font-bold shadow-md">✅ Set watermark</button>
                                )}
                            </div>
                        )}
                    </div>
                )}

                <p className="mt-4 text-red-600 min-h-6 font-medium">{msg}</p>

                <button onClick={clearEncodings} className="mt-10 text-xs text-gray-400 hover:text-red-500 underline transition-colors">Xóa toàn bộ dữ liệu nhận diện</button>
            </div>
        </div>
    );
};
