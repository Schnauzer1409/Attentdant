import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { localService } from '../services/localService';
import { commonService } from '../services/commonService';
import { authApi } from '../api/authApi';

const LoginPage: React.FC = () => {
    const [username, setUsername] = useState<string>('');
    const [password, setPassword] = useState<string>('');
    const [error, setError] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);

    const navigate = useNavigate();

    const toPage = (role: string) => {
        navigate(role === "teacher" ? "/teacher" : "/student")
    }

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const formData = new FormData();
            formData.append("username", username);
            formData.append("password", password);

            const data = await authApi.login(formData);

            if (data.status !== "ok") {
                setError(data.msg || "Đăng nhập thất bại");
                setLoading(false);
                return;
            }

            localService.save("token", data.token);
            localService.save("username", data.username);
            localService.save("role", data.role);

            toPage(data.role);

        } catch (err) {
            console.error(err)
        } finally {
            setLoading(false);
        }
    };



    useEffect(() => {
        const role = localService.get('role')

        if (commonService.isLogin()) {
            toPage(role || '')
        } else {
            commonService.logout();
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className='w-screen h-screen flex items-center justify-center bg-[#eef2f3]'>
                <div className="bg-white p-8 rounded-xl shadow-lg w-[400px]">
                    <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">
                        Đăng nhập
                    </h2>

                    <form onSubmit={handleLogin} className="space-y-4">
                        <div>
                            <input
                                type="text"
                                placeholder="Tên đăng nhập"
                                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>

                        <div>
                            <input
                                type="password"
                                placeholder="Mật khẩu"
                                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={`w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition-colors duration-200 ${loading ? "opacity-70 cursor-not-allowed" : ""
                                }`}
                        >
                            {loading ? "Đang xử lý..." : "Đăng nhập"}
                        </button>
                    </form>

                    {error && (
                        <div className="mt-4 text-red-500 text-sm text-center font-medium">
                            {error}
                        </div>
                    )}
                </div>
        </div>

    );
};

export default LoginPage;