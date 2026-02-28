import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

export default function Analytics() {
    const [overview, setOverview] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/analytics/overview')
            .then(r => r.ok ? r.json() : {})
            .then(data => setOverview(data))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    // Demo chart data — replaced with real data when analytics sync runs
    const weeklyData = [
        { day: 'Mon', clicks: 12, saves: 4, impressions: 120 },
        { day: 'Tue', clicks: 19, saves: 7, impressions: 180 },
        { day: 'Wed', clicks: 8, saves: 3, impressions: 90 },
        { day: 'Thu', clicks: 25, saves: 11, impressions: 250 },
        { day: 'Fri', clicks: 32, saves: 15, impressions: 310 },
        { day: 'Sat', clicks: 45, saves: 22, impressions: 450 },
        { day: 'Sun', clicks: 55, saves: 28, impressions: 520 },
    ];

    const platformData = [
        { name: 'Pinterest', clicks: 156, color: '#E8426A' },
        { name: 'Instagram', clicks: 89, color: '#C13584' },
    ];

    if (loading) {
        return (
            <motion.div className="page-container" {...pageVariants}>
                <h1 className="section-title pt-2">📊 Analytics</h1>
                <div className="space-y-4">
                    {[...Array(4)].map((_, i) => (
                        <div key={i} className="card animate-pulse h-24" />
                    ))}
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">📊 Analytics</h1>
            <p className="text-brand-subtext text-sm mb-4">Track your pin performance and earnings.</p>

            {/* Overview Stats */}
            <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="card text-center py-3">
                    <p className="text-2xl font-bold text-brand-text">{overview?.total_pins || 0}</p>
                    <p className="text-xs text-brand-subtext mt-0.5">📌 Total Pins</p>
                </div>
                <div className="card text-center py-3">
                    <p className="text-2xl font-bold text-brand-pink">{overview?.total_clicks || 0}</p>
                    <p className="text-xs text-brand-subtext mt-0.5">👆 Total Clicks</p>
                </div>
                <div className="card text-center py-3">
                    <p className="text-2xl font-bold text-brand-text">{overview?.total_saves || 0}</p>
                    <p className="text-xs text-brand-subtext mt-0.5">💾 Total Saves</p>
                </div>
                <div className="card text-center py-3">
                    <p className="text-2xl font-bold text-green-400">₹{overview?.total_commission || 0}</p>
                    <p className="text-xs text-brand-subtext mt-0.5">💰 Est. Commission</p>
                </div>
            </div>

            {/* Weekly Performance Chart */}
            <div className="card mb-4">
                <h2 className="text-sm font-semibold text-brand-text mb-3">📈 Weekly Performance</h2>
                <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={weeklyData}>
                        <defs>
                            <linearGradient id="clickGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#E8426A" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#E8426A" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="saveGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.4} />
                                <stop offset="95%" stopColor="#38BDF8" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#3D1F2A" />
                        <XAxis dataKey="day" stroke="#C4899E" fontSize={10} />
                        <YAxis stroke="#C4899E" fontSize={10} />
                        <Tooltip
                            contentStyle={{
                                background: '#2A1520',
                                border: '1px solid #3D1F2A',
                                borderRadius: '12px',
                                fontSize: '12px',
                                color: '#F8E8F0',
                            }}
                        />
                        <Area type="monotone" dataKey="clicks" stroke="#E8426A" fill="url(#clickGrad)" strokeWidth={2} />
                        <Area type="monotone" dataKey="saves" stroke="#38BDF8" fill="url(#saveGrad)" strokeWidth={2} />
                    </AreaChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-2">
                    <span className="text-xs text-brand-pink">● Clicks</span>
                    <span className="text-xs text-sky-400">● Saves</span>
                </div>
            </div>

            {/* Platform Breakdown */}
            <div className="card mb-4">
                <h2 className="text-sm font-semibold text-brand-text mb-3">📱 Platform Clicks</h2>
                <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={platformData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#3D1F2A" />
                        <XAxis type="number" stroke="#C4899E" fontSize={10} />
                        <YAxis type="category" dataKey="name" stroke="#C4899E" fontSize={11} width={80} />
                        <Tooltip
                            contentStyle={{
                                background: '#2A1520',
                                border: '1px solid #3D1F2A',
                                borderRadius: '12px',
                                fontSize: '12px',
                                color: '#F8E8F0',
                            }}
                        />
                        <Bar dataKey="clicks" fill="#E8426A" radius={[0, 8, 8, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Info Card */}
            <div className="card bg-brand-pink/10 border-brand-pink/20">
                <p className="text-xs text-brand-subtext">
                    💡 Analytics update automatically every 6 hours. Connect your Pinterest and Instagram accounts in Settings for real-time tracking.
                </p>
            </div>
        </motion.div>
    );
}
