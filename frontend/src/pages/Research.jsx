import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

const RESEARCH_STEPS = [
    { label: 'Analyzing Google Trends', icon: '📊' },
    { label: 'Detecting real-time events', icon: '⚡' },
    { label: 'Scraping Pinterest trends', icon: '📌' },
    { label: 'Finding products across platforms', icon: '🛍️' },
    { label: 'Running competitor analysis', icon: '🕵️' },
    { label: 'Scoring and ranking products', icon: '🏆' },
    { label: 'Checking for duplicates', icon: '🔍' },
    { label: 'Saving results to database', icon: '💾' },
];

export default function Research() {
    const navigate = useNavigate();
    const [niche, setNiche] = useState('');
    const [isResearching, setIsResearching] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [completed, setCompleted] = useState(false);
    const [productsFound, setProductsFound] = useState(0);
    const [error, setError] = useState('');
    const [sessions, setSessions] = useState([]);
    const wsRef = useRef(null);

    // Load past research sessions
    useEffect(() => {
        fetch('/api/research/sessions')
            .then(r => r.ok ? r.json() : [])
            .then(data => setSessions(data))
            .catch(() => { });
    }, []);

    function connectWebSocket(sessionId) {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/research/${sessionId}`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.progress !== undefined) setProgress(data.progress);
                if (data.step) setCurrentStep(data.step);

                if (data.status === 'completed') {
                    setCompleted(true);
                    setIsResearching(false);
                    setProductsFound(data.products_found || 0);
                    toast.success(`Research complete! Found ${data.products_found || 0} products.`);
                    // Refresh sessions
                    fetch('/api/research/sessions')
                        .then(r => r.ok ? r.json() : [])
                        .then(d => setSessions(d))
                        .catch(() => { });
                }

                if (data.status === 'failed') {
                    setError(data.error || 'Research failed.');
                    setIsResearching(false);
                    toast.error('Research failed. Please try again.');
                }
            } catch (e) {
                console.error('WS parse error:', e);
            }
        };

        ws.onerror = () => {
            setError('WebSocket connection error. Check if backend is running.');
        };

        ws.onclose = () => {
            wsRef.current = null;
        };
    }

    async function startResearch() {
        if (!niche.trim()) {
            toast.error('Please enter a niche to research.');
            return;
        }

        setIsResearching(true);
        setProgress(0);
        setCurrentStep('Initializing research...');
        setCompleted(false);
        setError('');
        setProductsFound(0);

        try {
            const res = await fetch('/api/research/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ niche: niche.trim() }),
            });

            if (res.ok) {
                const data = await res.json();
                toast.success(`Research started for "${niche}"!`);
                connectWebSocket(data.session_id);
            } else {
                setError('Could not start research. Check backend.');
                setIsResearching(false);
                toast.error('Failed to start research.');
            }
        } catch {
            setError('Backend not connected.');
            setIsResearching(false);
            toast.error('Backend not connected.');
        }
    }

    function formatTime(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const now = new Date();
        const diff = Math.floor((now - d) / 1000);
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    }

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">🔬 Research Engine</h1>
            <p className="text-brand-subtext text-sm mb-4">
                Enter any niche — we'll find trending products across 7+ platforms.
            </p>

            {/* Niche Input */}
            {!isResearching && !completed && (
                <div className="card mb-4">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            className="input-field flex-1"
                            placeholder="e.g. Men Watches, Home Decor, Baby Toys..."
                            value={niche}
                            onChange={e => setNiche(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && startResearch()}
                        />
                    </div>
                    <button
                        onClick={startResearch}
                        className="btn-primary w-full mt-3 text-base"
                    >
                        🚀 Start Research
                    </button>
                </div>
            )}

            {/* Progress Display */}
            <AnimatePresence>
                {isResearching && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0 }}
                        className="card mb-4"
                    >
                        <h2 className="text-base font-semibold text-brand-text mb-3">
                            Researching: <span className="text-brand-pink">{niche}</span>
                        </h2>

                        {/* Progress Bar */}
                        <div className="w-full bg-brand-border rounded-full h-3 mb-3 overflow-hidden">
                            <motion.div
                                className="h-full bg-gradient-to-r from-brand-pink to-pink-400 rounded-full"
                                animate={{ width: `${progress}%` }}
                                transition={{ duration: 0.5, ease: 'easeOut' }}
                            />
                        </div>
                        <p className="text-xs text-brand-subtext text-center mb-4">{progress}%</p>

                        {/* Current Step */}
                        <p className="text-sm text-brand-text font-medium text-center animate-pulse">
                            {currentStep}
                        </p>

                        {/* Steps List */}
                        <div className="mt-4 space-y-2">
                            {RESEARCH_STEPS.map((step, i) => {
                                const pctThreshold = (i + 1) * 12;
                                const done = progress >= pctThreshold;
                                const active = !done && progress >= (i * 12);
                                return (
                                    <div key={i} className={`flex items-center gap-3 py-1.5 px-3 rounded-xl text-xs transition-all ${done ? 'text-green-400 bg-green-400/10' : active ? 'text-brand-pink bg-brand-pink/10 animate-pulse' : 'text-brand-subtext/40'}`}>
                                        <span className="text-base">{done ? '✅' : active ? step.icon : '⬜'}</span>
                                        <span>{step.label}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Error Display */}
            {error && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="card border-red-500/30 bg-red-500/10 mb-4"
                >
                    <p className="text-red-400 text-sm">❌ {error}</p>
                    <button
                        onClick={() => { setError(''); setCompleted(false); }}
                        className="btn-primary mt-3 text-sm"
                    >
                        🔄 Try Again
                    </button>
                </motion.div>
            )}

            {/* Completion Screen */}
            <AnimatePresence>
                {completed && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="card mb-4 border-green-500/30"
                    >
                        <div className="text-center">
                            <p className="text-4xl mb-2">🎉</p>
                            <h2 className="text-lg font-bold text-brand-text">Research Complete!</h2>
                            <p className="text-brand-subtext text-sm mt-1">
                                Found <span className="text-brand-pink font-bold">{productsFound}</span> high-scoring products for <span className="text-brand-cream font-semibold">"{niche}"</span>
                            </p>
                        </div>
                        <div className="flex gap-2 mt-4">
                            <button
                                onClick={() => navigate('/products')}
                                className="btn-primary flex-1 text-sm"
                            >
                                🛍️ View Products
                            </button>
                            <button
                                onClick={() => { setCompleted(false); setNiche(''); }}
                                className="flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold border border-brand-border text-brand-subtext hover:text-brand-pink hover:border-brand-pink transition-colors"
                            >
                                🔄 New Research
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Past Research Sessions */}
            {sessions.length > 0 && (
                <div className="card">
                    <h2 className="text-sm font-semibold text-brand-text mb-3">📋 Past Research</h2>
                    <div className="space-y-2">
                        {sessions.map(s => (
                            <div
                                key={s.id}
                                className="flex items-center justify-between py-2 px-3 rounded-xl bg-brand-bg/50 border border-brand-border/50"
                            >
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-brand-text font-medium truncate">{s.niche}</p>
                                    <p className="text-xs text-brand-subtext">
                                        {s.status === 'completed' ? `✅ ${s.products_found || 0} products` : s.status === 'running' ? '⏳ Running...' : '❌ Failed'}
                                        {' · '}{formatTime(s.started_at)}
                                    </p>
                                </div>
                                {s.status === 'completed' && (
                                    <button
                                        onClick={() => { setNiche(s.niche); navigate('/products'); }}
                                        className="text-xs text-brand-pink ml-2 flex-shrink-0"
                                    >
                                        View →
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
}
