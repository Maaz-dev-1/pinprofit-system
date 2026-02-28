import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import BottomNav from './components/BottomNav';
import Dashboard from './pages/Dashboard';
import Research from './pages/Research';
import Products from './pages/Products';
import PinPublisher from './pages/PinPublisher';
import Analytics from './pages/Analytics';
import Evolution from './pages/Evolution';
import Settings from './pages/Settings';

export default function App() {
  return (
    <div className="relative bg-brand-dark min-h-screen">
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/research" element={<Research />} />
          <Route path="/products" element={<Products />} />
          <Route path="/publisher" element={<PinPublisher />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/evolution" element={<Evolution />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
      <BottomNav />
    </div>
  );
}
