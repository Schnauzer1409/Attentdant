import type { JSX } from "react";
import { Navigate } from "react-router-dom";
import { commonService } from "../services/commonService";

interface IProtectedRouteProps {
    children: JSX.Element;
}

export default function ProtectedRoute({ children }: IProtectedRouteProps) {
    const isLogin = commonService.isLogin();

    if (!isLogin) {
        return <Navigate to="/" replace />;
    }

    return children;
}