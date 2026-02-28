import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';

const pageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.35 } },
    exit: { opacity: 0 },
};

const STEPS = [
    { num: 1, label: 'Upload Pin Image', icon: '🖼️' },
    { num: 2, label: 'Select Product', icon: '🛍️' },
    { num: 3, label: 'AI Content', icon: '🤖' },
    { num: 4, label: 'Approve & Post', icon: '🚀' },
];

export default function PinPublisher() {
    const [step, setStep] = useState(1);
    const [pinImage, setPinImage] = useState(null);
    const [pinImagePreview, setPinImagePreview] = useState('');
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [content, setContent] = useState(null);
    const [generating, setGenerating] = useState(false);
    const [posting, setPosting] = useState(false);
    const [postingTo, setPostingTo] = useState({ pinterest: true, instagram: false });
    const fileRef = useRef(null);

    // Load products for step 2
    useEffect(() => {
        if (step === 2) {
            fetch('/api/products?per_page=20&sort=score')
                .then(r => r.ok ? r.json() : { items: [] })
                .then(data => setProducts(data.items || []))
                .catch(() => { });
        }
    }, [step]);

    function handleImageUpload(e) {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            toast.error('Please select an image file.');
            return;
        }

        if (file.size > 20 * 1024 * 1024) {
            toast.error('Image must be under 20MB.');
            return;
        }

        setPinImage(file);
        const reader = new FileReader();
        reader.onload = (ev) => setPinImagePreview(ev.target.result);
        reader.readAsDataURL(file);
        toast.success('Image selected!');
    }

    async function generateContent() {
        if (!selectedProduct) {
            toast.error('Please select a product first.');
            return;
        }
        setGenerating(true);
        try {
            // For now generate placeholder content — Gemini integration via backend
            const res = await fetch('/api/pins/generate-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: selectedProduct.id }),
            });
            if (res.ok) {
                const data = await res.json();
                setContent(data);
                toast.success('AI content generated!');
            } else {
                // Fallback — generate client-side placeholder
                setContent({
                    title: selectedProduct.title,
                    description: `Check out this amazing ${selectedProduct.title}! Currently available at ₹${selectedProduct.price?.toLocaleString()} with great reviews. Perfect for anyone looking for quality products.`,
                    seo_keywords: ['trending', 'best price', 'top rated', 'India', selectedProduct.platform],
                    hashtags: ['#Shopping', '#BestDeals', '#TrendingNow', '#India', '#OnlineShopping'],
                    topic_tags: ['Shopping', 'Lifestyle'],
                    posting_time: { primary: '9:00 PM IST', secondary: '1:00 PM IST', reason: 'Peak engagement hours for Indian audience' },
                    sell_reason: 'This product is trending right now with high demand and competitive pricing.',
                });
                toast.success('Content generated (offline mode)');
            }
        } catch {
            // Fallback for offline mode
            setContent({
                title: selectedProduct.title,
                description: `Discover this ${selectedProduct.title}! Amazing quality at ₹${selectedProduct.price?.toLocaleString()}.`,
                seo_keywords: ['trending', 'best price', 'India'],
                hashtags: ['#Shopping', '#BestDeals', '#India'],
                topic_tags: ['Shopping'],
                posting_time: { primary: '9:00 PM IST', reason: 'Peak hours' },
                sell_reason: 'High demand product.',
            });
            toast.success('Content generated (demo mode)');
        }
        setGenerating(false);
    }

    async function publishPin() {
        if (!content) return;
        setPosting(true);
        try {
            // Upload image + create pin via backend
            const formData = new FormData();
            if (pinImage) formData.append('image', pinImage);
            formData.append('product_id', selectedProduct?.id?.toString() || '');
            formData.append('title', content.title);
            formData.append('description', content.description);
            formData.append('hashtags', JSON.stringify(content.hashtags));
            formData.append('keywords', JSON.stringify(content.seo_keywords));
            formData.append('post_to_pinterest', postingTo.pinterest.toString());
            formData.append('post_to_instagram', postingTo.instagram.toString());

            const res = await fetch('/api/pins/publish', {
                method: 'POST',
                body: formData,
            });

            if (res.ok) {
                toast.success('Pin published successfully! 🎉');
                // Reset wizard
                setStep(1);
                setPinImage(null);
                setPinImagePreview('');
                setSelectedProduct(null);
                setContent(null);
            } else {
                const data = await res.json();
                toast.error(data.message || 'Publishing failed.');
            }
        } catch {
            toast.error('Could not publish. Check backend connection.');
        }
        setPosting(false);
    }

    return (
        <motion.div className="page-container" {...pageVariants}>
            <h1 className="section-title pt-2">📌 Pin Publisher</h1>

            {/* Step Indicator */}
            <div className="flex items-center justify-between mb-6 px-2">
                {STEPS.map((s, i) => (
                    <div key={s.num} className="flex items-center">
                        <div
                            onClick={() => s.num < step && setStep(s.num)}
                            className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all cursor-pointer ${step === s.num ? 'bg-brand-pink text-white shadow-lg shadow-brand-pink/30' :
                                step > s.num ? 'bg-green-400/20 text-green-400' :
                                    'bg-brand-border text-brand-subtext/40'
                                }`}
                        >
                            {step > s.num ? '✓' : s.num}
                        </div>
                        {i < STEPS.length - 1 && (
                            <div className={`w-8 h-0.5 mx-1 ${step > s.num ? 'bg-green-400/40' : 'bg-brand-border'}`} />
                        )}
                    </div>
                ))}
            </div>
            <p className="text-center text-xs text-brand-subtext mb-4">{STEPS[step - 1].icon} {STEPS[step - 1].label}</p>

            {/* Step 1: Upload Image */}
            <AnimatePresence mode="wait">
                {step === 1 && (
                    <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <div className="card">
                            <h2 className="text-base font-semibold text-brand-text mb-3">📷 Upload Your Pin Image</h2>
                            <p className="text-xs text-brand-subtext mb-4">
                                Upload the pin image you want to post. Recommended: 1000×1500px (2:3 ratio).
                            </p>

                            {pinImagePreview ? (
                                <div className="relative mb-4">
                                    <img src={pinImagePreview} alt="Pin preview" className="w-full max-h-80 object-contain rounded-xl bg-brand-border/20" />
                                    <button
                                        onClick={() => { setPinImage(null); setPinImagePreview(''); }}
                                        className="absolute top-2 right-2 bg-red-500 text-white w-7 h-7 rounded-full text-sm"
                                    >✕</button>
                                </div>
                            ) : (
                                <div
                                    onClick={() => fileRef.current?.click()}
                                    className="border-2 border-dashed border-brand-border rounded-2xl py-12 text-center cursor-pointer hover:border-brand-pink transition-colors"
                                >
                                    <p className="text-4xl mb-2">📁</p>
                                    <p className="text-sm text-brand-subtext">Tap to select image</p>
                                    <p className="text-xs text-brand-subtext/50 mt-1">JPG, PNG, WEBP — max 20MB</p>
                                </div>
                            )}

                            <input ref={fileRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" />

                            <button
                                onClick={() => setStep(2)}
                                disabled={!pinImage}
                                className="btn-primary w-full mt-4 text-sm disabled:opacity-30"
                            >
                                Next → Select Product
                            </button>
                        </div>
                    </motion.div>
                )}

                {/* Step 2: Select Product */}
                {step === 2 && (
                    <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <div className="card">
                            <h2 className="text-sm font-semibold text-brand-text mb-3">🛍️ Select Product to Promote</h2>
                            <div className="space-y-2 max-h-96 overflow-y-auto">
                                {products.length === 0 ? (
                                    <p className="text-xs text-brand-subtext text-center py-4">No products found. Run research first.</p>
                                ) : products.map(p => (
                                    <div
                                        key={p.id}
                                        onClick={() => setSelectedProduct(p)}
                                        className={`flex items-center gap-3 p-2.5 rounded-xl cursor-pointer transition-all ${selectedProduct?.id === p.id
                                            ? 'bg-brand-pink/20 border border-brand-pink/40'
                                            : 'bg-brand-bg/50 border border-brand-border/30 hover:border-brand-pink/30'
                                            }`}
                                    >
                                        <div className="w-12 h-12 rounded-lg bg-brand-border/30 overflow-hidden flex-shrink-0">
                                            {p.image_url ? (
                                                <img src={p.image_url} alt="" className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-lg">📦</div>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs text-brand-text font-medium truncate">{p.title}</p>
                                            <p className="text-xs text-brand-subtext">₹{p.price?.toLocaleString()} · {p.platform} · ⭐{p.rating || '—'}</p>
                                        </div>
                                        <span className="text-xs text-brand-pink font-bold">{p.score}</span>
                                    </div>
                                ))}
                            </div>

                            <div className="flex gap-2 mt-4">
                                <button onClick={() => setStep(1)} className="flex-1 py-2.5 rounded-xl text-sm border border-brand-border text-brand-subtext">
                                    ← Back
                                </button>
                                <button
                                    onClick={() => setStep(3)}
                                    disabled={!selectedProduct}
                                    className="btn-primary flex-1 text-sm disabled:opacity-30"
                                >
                                    Next → Generate Content
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Step 3: AI Content Generation */}
                {step === 3 && (
                    <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <div className="card">
                            <h2 className="text-sm font-semibold text-brand-text mb-3">🤖 AI-Generated Content</h2>
                            {!content ? (
                                <>
                                    <p className="text-xs text-brand-subtext mb-4">
                                        Gemini AI will generate optimized title, description, hashtags, and posting time.
                                    </p>
                                    <button
                                        onClick={generateContent}
                                        disabled={generating}
                                        className="btn-primary w-full text-sm"
                                    >
                                        {generating ? '⏳ Generating with Gemini AI...' : '✨ Generate Content'}
                                    </button>
                                </>
                            ) : (
                                <>
                                    {/* Title */}
                                    <div className="mb-3">
                                        <label className="text-xs text-brand-subtext font-semibold">Title</label>
                                        <input
                                            type="text"
                                            className="input-field mt-1"
                                            value={content.title}
                                            onChange={e => setContent(c => ({ ...c, title: e.target.value }))}
                                        />
                                    </div>

                                    {/* Description */}
                                    <div className="mb-3">
                                        <label className="text-xs text-brand-subtext font-semibold">Description</label>
                                        <textarea
                                            className="input-field mt-1 min-h-[100px] resize-none"
                                            value={content.description}
                                            onChange={e => setContent(c => ({ ...c, description: e.target.value }))}
                                        />
                                    </div>

                                    {/* Keywords */}
                                    <div className="mb-3">
                                        <label className="text-xs text-brand-subtext font-semibold">SEO Keywords</label>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {(content.seo_keywords || []).map((kw, i) => (
                                                <span key={i} className="text-[10px] bg-brand-border/50 text-brand-subtext px-2 py-0.5 rounded-full">{kw}</span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Hashtags */}
                                    <div className="mb-3">
                                        <label className="text-xs text-brand-subtext font-semibold">Hashtags</label>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {(content.hashtags || []).map((h, i) => (
                                                <span key={i} className="text-[10px] bg-brand-pink/10 text-brand-pink px-2 py-0.5 rounded-full">{h}</span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Best Posting Time */}
                                    {content.posting_time && (
                                        <div className="mb-3 p-3 rounded-xl bg-brand-bg/50 border border-brand-border/30">
                                            <p className="text-xs text-brand-subtext font-semibold mb-1">⏰ Best Posting Time</p>
                                            <p className="text-sm text-brand-text">{content.posting_time.primary}</p>
                                            <p className="text-xs text-brand-subtext/60 mt-0.5">{content.posting_time.reason}</p>
                                        </div>
                                    )}

                                    {/* Sell Reason */}
                                    {content.sell_reason && (
                                        <div className="p-3 rounded-xl bg-green-400/10 border border-green-400/20 mb-3">
                                            <p className="text-xs text-green-400 font-semibold">💡 Why it will sell</p>
                                            <p className="text-xs text-brand-subtext mt-0.5">{content.sell_reason}</p>
                                        </div>
                                    )}
                                </>
                            )}

                            <div className="flex gap-2 mt-4">
                                <button onClick={() => setStep(2)} className="flex-1 py-2.5 rounded-xl text-sm border border-brand-border text-brand-subtext">
                                    ← Back
                                </button>
                                <button
                                    onClick={() => setStep(4)}
                                    disabled={!content}
                                    className="btn-primary flex-1 text-sm disabled:opacity-30"
                                >
                                    Next → Preview & Post
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Step 4: Approve & Post */}
                {step === 4 && (
                    <motion.div key="step4" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <div className="card">
                            <h2 className="text-sm font-semibold text-brand-text mb-3">🚀 Final Preview</h2>

                            {/* Pin Preview */}
                            <div className="rounded-xl overflow-hidden bg-brand-border/20 mb-4">
                                {pinImagePreview && (
                                    <img src={pinImagePreview} alt="Pin" className="w-full max-h-64 object-contain" />
                                )}
                                <div className="p-3">
                                    <p className="text-sm text-brand-text font-bold">{content?.title}</p>
                                    <p className="text-xs text-brand-subtext mt-1 line-clamp-3">{content?.description}</p>
                                    <div className="flex flex-wrap gap-1 mt-2">
                                        {(content?.hashtags || []).slice(0, 5).map((h, i) => (
                                            <span key={i} className="text-[10px] text-brand-pink">{h}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Post To */}
                            <div className="mb-4">
                                <p className="text-xs text-brand-subtext font-semibold mb-2">Post To:</p>
                                <div className="flex gap-3">
                                    <label className="flex items-center gap-2 text-sm text-brand-text cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={postingTo.pinterest}
                                            onChange={e => setPostingTo(p => ({ ...p, pinterest: e.target.checked }))}
                                            className="accent-brand-pink w-4 h-4"
                                        />
                                        📌 Pinterest
                                    </label>
                                    <label className="flex items-center gap-2 text-sm text-brand-text cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={postingTo.instagram}
                                            onChange={e => setPostingTo(p => ({ ...p, instagram: e.target.checked }))}
                                            className="accent-brand-pink w-4 h-4"
                                        />
                                        📸 Instagram
                                    </label>
                                </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex gap-2">
                                <button onClick={() => setStep(3)} className="flex-1 py-2.5 rounded-xl text-sm border border-brand-border text-brand-subtext">
                                    ← Edit
                                </button>
                                <button
                                    onClick={publishPin}
                                    disabled={posting || (!postingTo.pinterest && !postingTo.instagram)}
                                    className="btn-primary flex-1 text-sm disabled:opacity-30"
                                >
                                    {posting ? '⏳ Publishing...' : '🚀 Publish Now'}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}
