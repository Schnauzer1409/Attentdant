import { lazy } from "react"

const StudentPage = lazy(() => import('../pages/StudentPage'))
const TeacherPage = lazy(() => import('../pages/TeacherPage'))

export const protectedRoutes = [
    {
        path: '/student',
        element: StudentPage
    },
    {
        path: '/teacher',
        element: TeacherPage
    }
]