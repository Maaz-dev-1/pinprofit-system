import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

export default function Evolution() {
    const [data, setData] = useState({ memory: {}, history: {} });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/evolution/summary')
            .then(r => r.ok ? r.json() : {})
            .then(d => setData(d))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const topNiches = data.memory?.top_niches || [];
    const nightlyRuns = data.history?.nightly_runs || [];
    const lastUpdated = data.memory?.last_updated;

    if (loading) {
        return (
            <motion.div className="page-container" {...pageVariants}>
                <h1 className="section-title pt-2">🧠 Evolution Engine</h1>
                <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="card animate-pulse h-20" />
                    ))}
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">🧠 Evolution Engine</h1>
            <p className="text-brand-subtext text-sm mb-4">
                PinProfit learns from every action. Gets smarter every night.
            </p>

            {/* Status Card */}
            <div className="card mb-4 bg-gradient-to-br from-brand-card to-brand-pink/5">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-brand-pink/20 flex items-center justify-center text-2xl">
                        🧬
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-brand-text">Self-Learning System</p>
                        <p className="text-xs text-brand-subtext">
                            {nightlyRuns.length > 0
                                ? `${nightlyRuns.length} analysis runs completed`
                                : 'Nightly analysis starts automatically at 3 AM IST'}
                        </p>
                        {lastUpdated && (
                            <p className="text-[10px] text-brand-subtext/50 mt-0.5">
                                Last update: {new Date(lastUpdated).toLocaleString('en-IN')}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Top Niches */}
            <div className="card mb-4">
                <h2 className="text-sm font-semibold text-brand-text mb-3">🏆 Top Researched Niches</h2>
                {topNiches.length === 0 ? (
                    <p className="text-xs text-brand-subtext text-center py-4">
                        No data yet. Start researching niches to build your learning database.
                    </p>
                ) : (
                    <div className="space-y-2">
                        {topNiches.map(([niche, count], i) => (
                            <div key={i} className="flex items-center gap-3 py-2 px-3 rounded-xl bg-brand-bg/50">
                                <span className="text-sm text-brand-cream font-bold w-6">{i + 1}</span>
                                <div className="flex-1">
                                    <p className="text-sm text-brand-text">{niche}</p>
                                </div>
                                <span className="text-xs text-brand-subtext bg-brand-border/50 px-2 py-0.5 rounded-full">
                                    {count}x
                                </span>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Learning History */}
            <div className="card mb-4">
                <h2 className="text-sm font-semibold text-brand-text mb-3">📜 Learning History</h2>
                {nightlyRuns.length === 0 ? (
                    <p className="text-xs text-brand-subtext text-center py-4">
                        No nightly analysis runs yet. The system learns while you sleep! 🌙
                    </p>
                ) : (
                    <div className="space-y-2">
                        {nightlyRuns.slice(-5).reverse().map((run, i) => (
                            <div key={i} className="py-2 px-3 rounded-xl bg-brand-bg/50 border border-brand-border/30">
                                <p className="text-xs text-brand-text">{run.insights}</p>
                                <p className="text-[10px] text-brand-subtext/50 mt-0.5">
                                    {new Date(run.date).toLocaleString('en-IN')}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* How It Works */}
            <div className="card">
                <h2 className="text-sm font-semibold text-brand-text mb-3">🔮 How Evolution Works</h2>
                <div className="space-y-3">
                    {[
                        { icon: '📊', title: 'Tracks Every Action', desc: 'Research, approvals, skips, clicks — everything is logged.' },
                        { icon: '🌙', title: 'Nightly Analysis (3 AM)', desc: 'Analyzes all data to find winning patterns and niches.' },
                        { icon: '🎯', title: 'Strategy Updates', desc: 'Updates scoring weights, platform priorities, and timing.' },
                        { icon: '📈', title: 'Continuous Improvement', desc: 'Each cycle makes recommendations more accurate.' },
                    ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3">
                            <span className="text-xl">{item.icon}</span>
                            <div>
                                <p className="text-xs font-semibold text-brand-text">{item.title}</p>
                                <p className="text-xs text-brand-subtext/70">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </motion.div>
    );
}
