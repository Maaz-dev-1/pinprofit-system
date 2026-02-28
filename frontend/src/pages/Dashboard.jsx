import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35, ease: 'easeOut' } },
    exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

function getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    return 'Good Evening';
}

function getDateStr() {
    return new Date().toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long',
    });
}

export default function Dashboard() {
    const navigate = useNavigate();
    const [niche, setNiche] = useState('');
    const [recentNiches, setRecentNiches] = useState([]);
    const [stats, setStats] = useState({ pins_today: 0, total_clicks: 0, commission: 0, pending: 0 });
    const [activity, setActivity] = useState([]);
    const [pendingPins, setPendingPins] = useState([]);

    useEffect(() => {
        // Load stats and activity from API
        fetchDashboard();
        // Load recent niches from localStorage
        const stored = JSON.parse(localStorage.getItem('recentNiches') || '[]');
        setRecentNiches(stored);
    }, []);

    async function fetchDashboard() {
        try {
            const [statsRes, activityRes, pendingRes] = await Promise.all([
                fetch('/api/dashboard/stats'),
                fetch('/api/dashboard/activity'),
                fetch('/api/pins/pending?limit=2'),
            ]);
            if (statsRes.ok) setStats(await statsRes.json());
            if (activityRes.ok) setActivity((await activityRes.json()).items || []);
            if (pendingRes.ok) setPendingPins((await pendingRes.json()).items || []);
        } catch {
            // Backend not connected yet — use dummy data for UI preview
            setStats({ pins_today: 0, total_clicks: 0, commission: 0, pending: 0 });
            setActivity([{ id: 1, message: 'Welcome to PinProfit! Start by typing a niche below.', time: 'Just now' }]);
        }
    }

    function handleStartResearch() {
        if (!niche.trim()) return;
        const trimmed = niche.trim();
        // Save to recent niches
        const updated = [trimmed, ...recentNiches.filter(n => n !== trimmed)].slice(0, 5);
        localStorage.setItem('recentNiches', JSON.stringify(updated));
        setRecentNiches(updated);
        navigate('/research', { state: { niche: trimmed } });
    }

    return (
        <motion.div className="page-container" {...pageVariants}>
            {/* Header */}
            <div className="flex items-start justify-between mb-6 pt-2">
                <div>
                    <h1 className="text-2xl font-bold text-brand-text">{getGreeting()} 👋</h1>
                    <p className="text-brand-subtext text-sm mt-0.5">{getDateStr()}</p>
                </div>
                <div className="w-10 h-10 bg-brand-pink rounded-2xl flex items-center justify-center text-xl">
                    📌
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 gap-3 mb-6">
                <StatCard label="Pins Today" value={stats.pins_today} icon="📌" />
                <StatCard label="Total Clicks" value={stats.total_clicks} icon="👆" />
                <StatCard label="Est. Earnings" value={`₹${stats.commission}`} icon="💰" />
                <StatCard label="Pending" value={stats.pending} icon="⏳" accent />
            </div>

            {/* Niche Input */}
            <div className="card mb-6">
                <h2 className="text-base font-semibold text-brand-text mb-3">🔍 Start Research</h2>
                <input
                    id="niche-input"
                    type="text"
                    className="input-field mb-3"
                    placeholder="Type any niche... (e.g. Men Watches, Home Decor, Baby Toys)"
                    value={niche}
                    onChange={e => setNiche(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleStartResearch()}
                />

                {/* Recent niche chips */}
                {recentNiches.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                        {recentNiches.map(n => (
                            <button
                                key={n}
                                onClick={() => setNiche(n)}
                                className="badge bg-brand-border text-brand-subtext border border-brand-border/50 hover:border-brand-pink hover:text-brand-pink transition-colors py-1 px-3 text-xs touch-manipulation"
                            >
                                {n}
                            </button>
                        ))}
                    </div>
                )}

                <button
                    id="start-research-btn"
                    onClick={handleStartResearch}
                    disabled={!niche.trim()}
                    className="btn-primary w-full text-base"
                >
                    🚀 Start Research
                </button>
            </div>

            {/* Pending Approvals */}
            {pendingPins.length > 0 && (
                <div className="card mb-6">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="text-base font-semibold text-brand-text">⏳ Pending Approvals</h2>
                        <span className="badge bg-brand-pink/20 text-brand-pink border border-brand-pink/30">
                            {stats.pending}
                        </span>
                    </div>
                    <div className="space-y-2">
                        {pendingPins.map(pin => (
                            <div key={pin.id} className="bg-brand-dark/50 rounded-2xl p-3 flex items-center gap-3">
                                <div className="w-12 h-12 bg-brand-border rounded-xl flex-shrink-0 overflow-hidden">
                                    {pin.image_url && <img src={pin.image_url} alt="" className="w-full h-full object-cover" />}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-brand-text truncate">{pin.title || 'Untitled Pin'}</p>
                                    <p className="text-xs text-brand-subtext">{pin.niche || '—'}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={() => navigate('/publisher')}
                        className="btn-secondary w-full mt-3 text-sm"
                    >
                        View All →
                    </button>
                </div>
            )}

            {/* Recent Activity */}
            <div className="card">
                <h2 className="text-base font-semibold text-brand-text mb-3">⚡ Recent Activity</h2>
                {activity.length === 0 ? (
                    <p className="text-brand-subtext text-sm text-center py-4">No activity yet. Start your first research!</p>
                ) : (
                    <div className="space-y-3">
                        {activity.map((item, i) => (
                            <div key={item.id || i} className="flex items-start gap-3">
                                <div className="w-1.5 h-1.5 bg-brand-pink rounded-full mt-2 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-brand-text">{item.message}</p>
                                    <p className="text-xs text-brand-subtext mt-0.5">{item.time}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </motion.div>
    );
}

function StatCard({ label, value, icon, accent }) {
    return (
        <div className={`card flex flex-col items-center justify-center py-4 gap-1 ${accent ? 'border-brand-pink/40' : ''}`}>
            <span className="text-2xl">{icon}</span>
            <span className={`text-xl font-bold ${accent ? 'text-brand-pink' : 'text-brand-text'}`}>{value}</span>
            <span className="text-xs text-brand-subtext font-medium">{label}</span>
        </div>
    );
}
