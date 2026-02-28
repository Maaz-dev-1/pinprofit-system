import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

const PLATFORMS = ['All', 'Amazon', 'Flipkart', 'Myntra', 'Meesho', 'Ajio', 'Nykaa', 'FirstCry'];
const SORTS = [
    { key: 'score', label: '🏆 Score' },
    { key: 'commission', label: '💰 Commission' },
    { key: 'rating', label: '⭐ Rating' },
    { key: 'price_asc', label: '💲 Price ↑' },
    { key: 'price_desc', label: '💲 Price ↓' },
];

function ProductCard({ product }) {
    const badges = typeof product.badges === 'string' ? JSON.parse(product.badges || '{}') : (product.badges || {});

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="card mb-3 p-3"
        >
            <div className="flex gap-3">
                {/* Product Image */}
                <div className="w-20 h-20 flex-shrink-0 rounded-xl bg-brand-border/30 overflow-hidden">
                    {product.image_url ? (
                        <img
                            src={product.image_url}
                            alt={product.title}
                            className="w-full h-full object-cover"
                            loading="lazy"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-2xl">📦</div>
                    )}
                </div>

                {/* Product Info */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-brand-text font-medium line-clamp-2 leading-tight">{product.title}</p>

                    <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs font-bold text-brand-pink">₹{product.price?.toLocaleString() || '—'}</span>
                        {product.mrp && product.mrp > (product.price || 0) && (
                            <>
                                <span className="text-xs text-brand-subtext/50 line-through">₹{product.mrp.toLocaleString()}</span>
                                <span className="text-xs text-green-400 font-semibold">-{product.discount_pct?.toFixed(0)}%</span>
                            </>
                        )}
                    </div>

                    <div className="flex items-center gap-3 mt-1">
                        {product.rating > 0 && (
                            <span className="text-xs text-yellow-400">⭐ {product.rating}</span>
                        )}
                        {product.review_count > 0 && (
                            <span className="text-xs text-brand-subtext">({product.review_count.toLocaleString()})</span>
                        )}
                        <span className="text-xs text-brand-subtext/60 capitalize">{product.platform}</span>
                    </div>
                </div>

                {/* Score Badge */}
                <div className="flex flex-col items-center justify-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold ${(product.score || 0) >= 90 ? 'bg-green-400/20 text-green-400 ring-1 ring-green-400/30' :
                        (product.score || 0) >= 80 ? 'bg-brand-pink/20 text-brand-pink ring-1 ring-brand-pink/30' :
                            'bg-brand-border/50 text-brand-subtext'
                        }`}>
                        {product.score || 0}
                    </div>
                    <span className="text-[10px] text-brand-subtext mt-0.5">Score</span>
                </div>
            </div>

            {/* Bottom Row — Badges + Commission */}
            <div className="flex items-center justify-between mt-2 pt-2 border-t border-brand-border/30">
                <div className="flex gap-1 flex-wrap">
                    {badges.bestseller && <span className="text-[10px] bg-yellow-400/20 text-yellow-400 px-2 py-0.5 rounded-full">🏷️ Bestseller</span>}
                    {badges.amazons_choice && <span className="text-[10px] bg-blue-400/20 text-blue-400 px-2 py-0.5 rounded-full">✨ Choice</span>}
                    {badges.deal_of_day && <span className="text-[10px] bg-red-400/20 text-red-400 px-2 py-0.5 rounded-full">🔥 Deal</span>}
                </div>
                <div className="text-right">
                    <span className="text-xs text-green-400 font-semibold">~₹{(product.commission_estimate || 0).toFixed(0)}</span>
                    <span className="text-[10px] text-brand-subtext block">Est. commission</span>
                </div>
            </div>
        </motion.div>
    );
}

export default function Products() {
    const [products, setProducts] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [platform, setPlatform] = useState('All');
    const [sort, setSort] = useState('score');
    const perPage = 10;

    useEffect(() => {
        loadProducts();
    }, [page, platform, sort]);

    async function loadProducts(searchOverride) {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                per_page: perPage.toString(),
                sort,
            });
            if (platform !== 'All') params.set('platform', platform.toLowerCase());
            if (searchOverride ?? search) params.set('search', searchOverride ?? search);

            const res = await fetch(`/api/products?${params}`);
            if (res.ok) {
                const data = await res.json();
                setProducts(data.items || []);
                setTotal(data.total || 0);
            }
        } catch {
            toast.error('Could not load products.');
        } finally {
            setLoading(false);
        }
    }

    function handleSearch(e) {
        e.preventDefault();
        setPage(1);
        loadProducts(search);
    }

    const totalPages = Math.ceil(total / perPage);

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">🛍️ Products</h1>
            <p className="text-brand-subtext text-sm mb-3">
                {total > 0 ? `${total} products found` : 'Run a research to discover products'}
            </p>

            {/* Search Bar */}
            <form onSubmit={handleSearch} className="mb-3">
                <div className="flex gap-2">
                    <input
                        type="text"
                        className="input-field flex-1"
                        placeholder="Search products..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    <button type="submit" className="bg-brand-pink text-white px-4 py-2.5 rounded-xl text-sm font-semibold">
                        🔍
                    </button>
                </div>
            </form>

            {/* Platform Filter Tabs */}
            <div className="flex gap-1.5 overflow-x-auto pb-2 mb-3 snap-x snap-mandatory">
                {PLATFORMS.map(p => (
                    <button
                        key={p}
                        onClick={() => { setPlatform(p); setPage(1); }}
                        className={`flex-shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold touch-manipulation transition-all ${platform === p
                            ? 'bg-brand-pink text-white'
                            : 'bg-brand-card text-brand-subtext border border-brand-border'
                            }`}
                    >
                        {p}
                    </button>
                ))}
            </div>

            {/* Sort Options */}
            <div className="flex gap-1.5 overflow-x-auto pb-2 mb-4 snap-x snap-mandatory">
                {SORTS.map(s => (
                    <button
                        key={s.key}
                        onClick={() => { setSort(s.key); setPage(1); }}
                        className={`flex-shrink-0 px-2.5 py-1.5 rounded-lg text-xs touch-manipulation transition-all ${sort === s.key
                            ? 'bg-brand-cream/20 text-brand-cream font-bold'
                            : 'text-brand-subtext/60 hover:text-brand-subtext'
                            }`}
                    >
                        {s.label}
                    </button>
                ))}
            </div>

            {/* Products List */}
            {loading ? (
                <div className="space-y-3">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="card animate-pulse p-3">
                            <div className="flex gap-3">
                                <div className="w-20 h-20 rounded-xl bg-brand-border/30" />
                                <div className="flex-1 space-y-2">
                                    <div className="h-3 bg-brand-border/30 rounded w-3/4" />
                                    <div className="h-3 bg-brand-border/30 rounded w-1/2" />
                                    <div className="h-2 bg-brand-border/30 rounded w-1/3" />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : products.length === 0 ? (
                <div className="card text-center py-8">
                    <p className="text-3xl mb-2">🔍</p>
                    <p className="text-brand-subtext text-sm">No products found.</p>
                    <p className="text-brand-subtext/60 text-xs mt-1">Run a research from the Research tab first.</p>
                </div>
            ) : (
                <AnimatePresence>
                    {products.map(p => (
                        <ProductCard key={p.id} product={p} />
                    ))}
                </AnimatePresence>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex justify-center gap-2 mt-4">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-3 py-1.5 rounded-lg text-xs border border-brand-border text-brand-subtext disabled:opacity-30"
                    >
                        ← Prev
                    </button>
                    <span className="px-3 py-1.5 text-xs text-brand-subtext">
                        {page} / {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-3 py-1.5 rounded-lg text-xs border border-brand-border text-brand-subtext disabled:opacity-30"
                    >
                        Next →
                    </button>
                </div>
            )}
        </motion.div>
    );
}
