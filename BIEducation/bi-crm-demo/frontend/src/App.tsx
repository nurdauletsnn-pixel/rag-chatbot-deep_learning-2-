import { Toaster } from 'react-hot-toast'
import { Dashboard } from './components/Dashboard'

function App() {
  return (
    <>
      <Toaster position="top-right" toastOptions={{ className: 'rounded-2xl border border-slate-200 shadow-lg' }} />
      <Dashboard />
    </>
  )
}

export default App
