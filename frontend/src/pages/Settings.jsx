import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

const SECTIONS = [
    { key: 'gemini', label: '🤖 AI Engine', icon: '🤖' },
    { key: 'pinterest', label: '📌 Pinterest', icon: '📌' },
    { key: 'instagram', label: '📸 Instagram', icon: '📸' },
    { key: 'amazon', label: '🟠 Amazon Associates', icon: '🟠' },
    { key: 'cuelinks', label: '🔵 Cuelinks', icon: '🔵' },
    { key: 'email', label: '📧 Gmail Notifications', icon: '📧' },
];

const STATUS_COLORS = {
    green: 'text-green-400 bg-green-400/10 border-green-400/20',
    yellow: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20',
    red: 'text-red-400 bg-red-400/10 border-red-400/20',
    grey: 'text-brand-subtext/40 bg-brand-border/20 border-brand-border/20',
};

const STATUS_DOTS = { green: '🟢', yellow: '🟡', red: '🔴', grey: '⚪' };

function MaskedInput({ id, label, placeholder, value, onChange, hint, updatedAt }) {
    const [show, setShow] = useState(false);
    return (
        <div className="mb-4">
            <label htmlFor={id} className="text-xs font-semibold text-brand-subtext block mb-1">{label}</label>
            <div className="relative">
                <input
                    id={id}
                    type={show ? 'text' : 'password'}
                    className="input-field pr-12"
                    placeholder={placeholder}
                    value={value}
                    onChange={e => onChange(e.target.value)}
                    autoComplete="off"
                />
                <button
                    type="button"
                    onClick={() => setShow(s => !s)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-subtext text-xs touch-manipulation"
                >
                    {show ? '🙈' : '👁️'}
                </button>
            </div>
            <div className="flex items-center justify-between mt-1">
                {hint && <p className="text-xs text-brand-subtext/60">{hint}</p>}
                {updatedAt && (
                    <p className="text-[10px] text-brand-subtext/40 ml-auto">
                        Updated: {new Date(updatedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' })}
                    </p>
                )}
            </div>
        </div>
    );
}

function TextInput({ id, label, placeholder, value, onChange, hint, updatedAt }) {
    return (
        <div className="mb-4">
            <label htmlFor={id} className="text-xs font-semibold text-brand-subtext block mb-1">{label}</label>
            <input
                id={id}
                type="text"
                className="input-field"
                placeholder={placeholder}
                value={value}
                onChange={e => onChange(e.target.value)}
            />
            <div className="flex items-center justify-between mt-1">
                {hint && <p className="text-xs text-brand-subtext/60">{hint}</p>}
                {updatedAt && (
                    <p className="text-[10px] text-brand-subtext/40 ml-auto">
                        Updated: {new Date(updatedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' })}
                    </p>
                )}
            </div>
        </div>
    );
}

function UsageBar({ label, pct, color = 'brand-pink' }) {
    const barColor = pct >= 90 ? 'bg-red-400' : pct >= 80 ? 'bg-yellow-400' : 'bg-green-400';
    return (
        <div className="mb-3">
            <div className="flex justify-between text-xs mb-1">
                <span className="text-brand-subtext">{label}</span>
                <span className="text-brand-subtext">{pct}%</span>
            </div>
            <div className="w-full bg-brand-border rounded-full h-2 overflow-hidden">
                <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${Math.min(pct, 100)}%` }} />
            </div>
        </div>
    );
}

export default function Settings() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [activeSection, setActiveSection] = useState('gemini');
    const [cfg, setCfg] = useState({
        gemini_api_key: '', pinterest_app_id: '', pinterest_app_secret: '', pinterest_access_token: '',
        instagram_app_id: '', instagram_app_secret: '', instagram_access_token: '',
        amazon_access_key: '', amazon_secret_key: '', amazon_associate_tag: '',
        cuelinks_api_key: '',
        gmail_address: '', gmail_app_password: '', notification_email: '',
    });
    const [updatedAt, setUpdatedAt] = useState({});
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState({});
    const [oauthLoading, setOauthLoading] = useState({});
    const [health, setHealth] = useState([]);
    const [hasIssues, setHasIssues] = useState(false);

    // Load settings + health on mount
    useEffect(() => {
        fetch('/api/settings')
            .then(r => r.ok ? r.json() : {})
            .then(data => {
                if (data.settings) {
                    setCfg(prev => ({ ...prev, ...data.settings }));
                    setUpdatedAt(data.timestamps || data.updated_at || {});
                } else {
                    setCfg(prev => ({ ...prev, ...data }));
                }
            })
            .catch(() => { });

        fetch('/api/settings/health')
            .then(r => r.ok ? r.json() : { services: [] })
            .then(data => {
                setHealth(data.services || []);
                setHasIssues(data.has_issues || false);
            })
            .catch(() => { });
    }, []);

    // Handle OAuth callback URL params
    useEffect(() => {
        const oauth = searchParams.get('oauth');
        const status = searchParams.get('status');
        if (oauth && status) {
            if (status === 'success') {
                toast.success(`${oauth.charAt(0).toUpperCase() + oauth.slice(1)} connected successfully! 🎉`);
                setActiveSection(oauth);
                fetch('/api/settings').then(r => r.ok ? r.json() : {}).then(data => {
                    if (data.settings) { setCfg(prev => ({ ...prev, ...data.settings })); setUpdatedAt(data.timestamps || {}); }
                }).catch(() => { });
            } else {
                toast.error(`${oauth.charAt(0).toUpperCase() + oauth.slice(1)} OAuth failed. Please try again.`);
                setActiveSection(oauth);
            }
            setSearchParams({});
        }
    }, [searchParams, setSearchParams]);

    function update(key) {
        return (val) => setCfg(prev => ({ ...prev, [key]: val }));
    }

    async function save() {
        setSaving(true);
        try {
            const res = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cfg),
            });
            if (res.ok) {
                toast.success('Settings saved!');
                const r = await fetch('/api/settings');
                if (r.ok) {
                    const data = await r.json();
                    if (data.settings) { setCfg(prev => ({ ...prev, ...data.settings })); setUpdatedAt(data.timestamps || {}); }
                }
                const h = await fetch('/api/settings/health');
                if (h.ok) { const hd = await h.json(); setHealth(hd.services || []); setHasIssues(hd.has_issues || false); }
            } else toast.error('Could not save. Is backend running?');
        } catch { toast.error('Could not connect to backend.'); }
        finally { setSaving(false); }
    }

    async function testConnection(service) {
        setTesting(t => ({ ...t, [service]: 'loading' }));
        try {
            const res = await fetch(`/api/settings/test/${service}`, { method: 'POST' });
            const data = await res.json();
            if (data.ok) {
                toast.success(data.message || `${service} connected!`);
                setTesting(t => ({ ...t, [service]: 'ok' }));
            } else {
                toast.error(data.message || `${service} connection failed.`);
                setTesting(t => ({ ...t, [service]: 'fail' }));
            }
        } catch {
            toast.error('Backend not connected.');
            setTesting(t => ({ ...t, [service]: 'fail' }));
        }
    }

    async function startOAuth(platform) {
        setOauthLoading(o => ({ ...o, [platform]: true }));
        try {
            const res = await fetch(`/api/settings/oauth/${platform}/url`);
            const data = await res.json();
            if (data.ok && data.url) window.location.href = data.url;
            else toast.error(data.message || `Could not start ${platform} OAuth. Save App ID & Secret first.`);
        } catch { toast.error('Backend not connected.'); }
        finally { setOauthLoading(o => ({ ...o, [platform]: false })); }
    }

    async function sendTestEmail() {
        setTesting(t => ({ ...t, test_email: 'loading' }));
        try {
            const res = await fetch('/api/settings/test-email', { method: 'POST' });
            const data = await res.json();
            if (data.ok) { toast.success(data.message); setTesting(t => ({ ...t, test_email: 'ok' })); }
            else { toast.error(data.message); setTesting(t => ({ ...t, test_email: 'fail' })); }
        } catch { toast.error('Backend not connected.'); setTesting(t => ({ ...t, test_email: 'fail' })); }
    }

    function TestBtn({ service }) {
        const state = testing[service];
        return (
            <button onClick={() => testConnection(service)} disabled={state === 'loading'}
                className="badge bg-brand-border text-brand-subtext border border-brand-border hover:border-brand-pink hover:text-brand-pink transition-colors py-1.5 px-3 text-xs touch-manipulation mt-2">
                {state === 'loading' ? '⏳ Testing...' : state === 'ok' ? '✅ Connected' : state === 'fail' ? '❌ Failed — Retry' : '🔌 Test Connection'}
            </button>
        );
    }

    function OAuthBtn({ platform, label }) {
        const loading = oauthLoading[platform];
        return (
            <button onClick={() => startOAuth(platform)} disabled={loading}
                className="w-full bg-gradient-to-r from-brand-pink to-brand-pink/80 text-white font-semibold py-2.5 px-4 rounded-xl text-sm transition-all hover:shadow-lg hover:shadow-brand-pink/20 active:scale-[0.98] touch-manipulation mt-2 mb-3">
                {loading ? '⏳ Redirecting...' : `🔗 ${label}`}
            </button>
        );
    }

    // Get health info for a specific service
    const getHealth = (svc) => health.find(h => h.service === svc) || {};

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">⚙️ Settings</h1>
            <p className="text-brand-subtext text-sm mb-4">All keys are stored securely in Supabase.</p>

            {/* ── SYSTEM HEALTH DASHBOARD ── */}
            <div className="card mb-4">
                <h2 className="text-sm font-semibold text-brand-text mb-3">🩺 System Health</h2>
                <div className="space-y-1.5">
                    {health.length === 0 ? (
                        <p className="text-xs text-brand-subtext text-center py-3 animate-pulse">Loading health status...</p>
                    ) : health.map(svc => (
                        <div key={svc.service}
                            className={`flex items-center justify-between py-2 px-3 rounded-xl border ${STATUS_COLORS[svc.status]}`}>
                            <div className="flex items-center gap-2">
                                <span className="text-sm">{STATUS_DOTS[svc.status]}</span>
                                <span className="text-xs font-semibold">{svc.label}</span>
                            </div>
                            <span className="text-[11px]">{svc.message}</span>
                        </div>
                    ))}
                </div>
                {hasIssues && (
                    <div className="mt-3 p-2.5 rounded-xl bg-red-400/10 border border-red-400/20">
                        <p className="text-xs text-red-400 font-semibold">⚠️ Some services need attention. Check the sections below.</p>
                    </div>
                )}
            </div>

            {/* Section Tabs */}
            <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scroll-smooth snap-x snap-mandatory">
                {SECTIONS.map(s => {
                    const svcHealth = getHealth(s.key);
                    const hasBadge = svcHealth.status === 'red' || svcHealth.status === 'yellow';
                    return (
                        <button key={s.key} onClick={() => setActiveSection(s.key)}
                            className={`relative flex-shrink-0 px-3 py-2 rounded-2xl text-xs font-semibold touch-manipulation transition-all ${activeSection === s.key
                                ? 'bg-brand-pink text-white' : 'bg-brand-card text-brand-subtext border border-brand-border'
                                }`}>
                            {s.label}
                            {hasBadge && (
                                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 border border-brand-card" />
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Section Content */}
            <div className="card">
                {activeSection === 'gemini' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">🤖 Google Gemini AI</h2>
                        {getHealth('gemini').usage_pct !== undefined && (
                            <UsageBar label="Daily API Usage" pct={getHealth('gemini').usage_pct} />
                        )}
                        <MaskedInput id="gemini-key" label="Gemini API Key" placeholder="AIza..." value={cfg.gemini_api_key} onChange={update('gemini_api_key')}
                            hint="Get free key at ai.google.dev — use gemini-1.5-flash model" updatedAt={updatedAt.gemini_api_key} />
                        <TestBtn service="gemini" />
                    </>
                )}

                {activeSection === 'pinterest' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">📌 Pinterest</h2>
                        <TextInput id="pint-app-id" label="App ID" placeholder="Pinterest App ID" value={cfg.pinterest_app_id} onChange={update('pinterest_app_id')}
                            hint="Create app at developers.pinterest.com" updatedAt={updatedAt.pinterest_app_id} />
                        <MaskedInput id="pint-app-secret" label="App Secret" placeholder="Pinterest App Secret" value={cfg.pinterest_app_secret} onChange={update('pinterest_app_secret')}
                            updatedAt={updatedAt.pinterest_app_secret} />
                        <OAuthBtn platform="pinterest" label="Connect Pinterest Account" />
                        <MaskedInput id="pint-token" label="Access Token (auto-filled after OAuth)" placeholder="Auto-filled after connecting" value={cfg.pinterest_access_token} onChange={update('pinterest_access_token')}
                            hint="Token is auto-filled when you click 'Connect Pinterest' above" updatedAt={updatedAt.pinterest_access_token} />
                        <TestBtn service="pinterest" />
                    </>
                )}

                {activeSection === 'instagram' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">📸 Instagram</h2>
                        <TextInput id="ig-app-id" label="Facebook App ID" placeholder="Facebook App ID" value={cfg.instagram_app_id} onChange={update('instagram_app_id')}
                            hint="Create at developers.facebook.com → Add Instagram Product" updatedAt={updatedAt.instagram_app_id} />
                        <MaskedInput id="ig-app-secret" label="Facebook App Secret" placeholder="Facebook App Secret" value={cfg.instagram_app_secret} onChange={update('instagram_app_secret')}
                            updatedAt={updatedAt.instagram_app_secret} />
                        <OAuthBtn platform="instagram" label="Connect Instagram Account" />
                        <MaskedInput id="ig-token" label="Access Token (auto-filled after OAuth)" placeholder="Auto-filled after connecting" value={cfg.instagram_access_token} onChange={update('instagram_access_token')}
                            hint="Long-lived token — auto-refreshed every 45 days" updatedAt={updatedAt.instagram_access_token} />
                        <TestBtn service="instagram" />
                    </>
                )}

                {activeSection === 'amazon' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">🟠 Amazon Associates</h2>
                        <MaskedInput id="amz-key" label="Access Key" placeholder="Amazon PA-API Access Key" value={cfg.amazon_access_key} onChange={update('amazon_access_key')}
                            hint="From affiliate-program.amazon.in → PA-API 5.0" updatedAt={updatedAt.amazon_access_key} />
                        <MaskedInput id="amz-secret" label="Secret Key" placeholder="Amazon PA-API Secret Key" value={cfg.amazon_secret_key} onChange={update('amazon_secret_key')}
                            updatedAt={updatedAt.amazon_secret_key} />
                        <TextInput id="amz-tag" label="Associate Tag" placeholder="your-tag-21" value={cfg.amazon_associate_tag} onChange={update('amazon_associate_tag')}
                            updatedAt={updatedAt.amazon_associate_tag} />
                        <TestBtn service="amazon" />
                    </>
                )}

                {activeSection === 'cuelinks' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">🔵 Cuelinks</h2>
                        <MaskedInput id="cue-key" label="API Key" placeholder="Cuelinks API Key" value={cfg.cuelinks_api_key} onChange={update('cuelinks_api_key')}
                            hint="Get from app.cuelinks.com → API section" updatedAt={updatedAt.cuelinks_api_key} />
                        <TestBtn service="cuelinks" />
                    </>
                )}

                {activeSection === 'email' && (
                    <>
                        <h2 className="text-base font-semibold text-brand-text mb-4">📧 Email Notifications</h2>
                        <TextInput id="gmail-addr" label="Gmail Address" placeholder="you@gmail.com" value={cfg.gmail_address} onChange={update('gmail_address')}
                            updatedAt={updatedAt.gmail_address} />
                        <MaskedInput id="gmail-pass" label="Gmail App Password" placeholder="xxxx xxxx xxxx xxxx" value={cfg.gmail_app_password} onChange={update('gmail_app_password')}
                            hint="Enable 2FA → Create App Password at myaccount.google.com" updatedAt={updatedAt.gmail_app_password} />
                        <TextInput id="notif-email" label="Notification Email (can be same)" placeholder="you@gmail.com" value={cfg.notification_email} onChange={update('notification_email')}
                            hint="All alerts and reports are sent to this address" updatedAt={updatedAt.notification_email} />
                        <div className="flex gap-2 flex-wrap mt-2">
                            <TestBtn service="email" />
                            <button onClick={sendTestEmail} disabled={testing.test_email === 'loading'}
                                className="badge bg-brand-pink/20 text-brand-pink border border-brand-pink/30 hover:bg-brand-pink hover:text-white transition-colors py-1.5 px-3 text-xs touch-manipulation mt-2">
                                {testing.test_email === 'loading' ? '⏳ Sending...' : testing.test_email === 'ok' ? '✅ Email Sent!' : '📨 Send Test Email'}
                            </button>
                        </div>
                    </>
                )}
            </div>

            <button id="save-settings-btn" onClick={save} disabled={saving} className="btn-primary w-full mt-4 text-base">
                {saving ? '⏳ Saving...' : '💾 Save All Settings'}
            </button>

            <p className="text-center text-xs text-brand-subtext/40 mt-6">PinProfit v1.0.0 — 100% Free</p>
        </motion.div>
    );
}
