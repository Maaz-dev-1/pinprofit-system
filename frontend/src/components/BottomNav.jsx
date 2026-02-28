import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const tabs = [
    {
        to: '/',
        label: 'Home',
        icon: (active) => (
            <svg viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'}
                stroke="currentColor" strokeWidth={active ? 0 : 1.8}
                className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
        ),
    },
    {
        to: '/research',
        label: 'Research',
        icon: (active) => (
            <svg viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'}
                stroke="currentColor" strokeWidth={active ? 0 : 1.8}
                className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
        ),
    },
    {
        to: '/publisher',
        label: 'Pins',
        icon: (active) => (
            <svg viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'}
                stroke="currentColor" strokeWidth={active ? 0 : 1.8}
                className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
        ),
    },
    {
        to: '/analytics',
        label: 'Analytics',
        icon: (active) => (
            <svg viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'}
                stroke="currentColor" strokeWidth={active ? 0 : 1.8}
                className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
        ),
    },
    {
        to: '/settings',
        label: 'Settings',
        icon: (active) => (
            <svg viewBox="0 0 24 24" fill={active ? 'currentColor' : 'none'}
                stroke="currentColor" strokeWidth={active ? 0 : 1.8}
                className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        ),
    },
];

export default function BottomNav() {
    const [hasIssues, setHasIssues] = useState(false);

    // Check system health for notification badge
    useEffect(() => {
        fetch('/api/settings/health')
            .then(r => r.ok ? r.json() : { has_issues: false })
            .then(data => setHasIssues(data.has_issues || false))
            .catch(() => { });

        // Re-check every 5 minutes
        const interval = setInterval(() => {
            fetch('/api/settings/health')
                .then(r => r.ok ? r.json() : { has_issues: false })
                .then(data => setHasIssues(data.has_issues || false))
                .catch(() => { });
        }, 5 * 60 * 1000);

        return () => clearInterval(interval);
    }, []);

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 glass border-t border-brand-border safe-bottom">
            <div className="max-w-lg mx-auto flex items-center justify-around px-2 pt-2 pb-1">
                {tabs.map((tab) => (
                    <NavLink
                        key={tab.to}
                        to={tab.to}
                        end={tab.to === '/'}
                        className="touch-manipulation"
                    >
                        {({ isActive }) => (
                            <motion.div
                                className={`flex flex-col items-center gap-0.5 min-w-[56px] py-1 px-2 rounded-2xl transition-colors duration-200 ${isActive ? 'text-brand-pink' : 'text-brand-subtext'
                                    }`}
                                whileTap={{ scale: 0.88 }}
                            >
                                <div className="relative">
                                    {tab.icon(isActive)}
                                    {isActive && (
                                        <motion.div
                                            layoutId="nav-dot"
                                            className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-brand-pink rounded-full"
                                        />
                                    )}
                                    {/* Red notification badge on Settings when services need attention */}
                                    {tab.to === '/settings' && hasIssues && !isActive && (
                                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                                    )}
                                </div>
                                <span className={`text-[10px] font-semibold ${isActive ? 'text-brand-pink' : 'text-brand-subtext'}`}>
                                    {tab.label}
                                </span>
                            </motion.div>
                        )}
                    </NavLink>
                ))}
            </div>
        </nav>
    );
}
