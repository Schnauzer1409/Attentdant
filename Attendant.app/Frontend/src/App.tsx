import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import LoginPage from './pages/LoginPage'
import ProtectedRoute from './components/ProtectedRoute'
import { protectedRoutes } from './routes/protectedRoutes'

function App() {

  return (
    <>
      <Routes>
        <Route path='/' element={<Navigate to='/login' />} />
        <Route path='/login' element={<LoginPage />} />
        {protectedRoutes.map((route) => {
          const Component = route.element;
          
          return (
            <Route 
              key={route.path} 
              path={route.path} 
              element={
                <ProtectedRoute>
                  <Component />
                </ProtectedRoute>
              } 
            />
          );
        })}
        
      </Routes>
    </>
  )
}

export default App
