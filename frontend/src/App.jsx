import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

// Pages (we'll build these in later stages)
// import Login from './pages/Login'
// import Register from './pages/Register'
// import Dashboard from './pages/Dashboard'
// import Groups from './pages/Groups'

function Placeholder({ name }) {
  return (
    <div style={{ padding: '2rem', color: 'var(--color-text-secondary)' }}>
      <h2>{name} — coming soon</h2>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route path="/login" element={<Placeholder name="Login" />} />
        <Route path="/register" element={<Placeholder name="Register" />} />
        <Route path="/dashboard" element={<Placeholder name="Dashboard" />} />
        <Route path="/groups" element={<Placeholder name="Groups" />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
