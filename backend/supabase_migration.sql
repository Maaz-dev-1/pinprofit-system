-- =============================================
-- PinProfit — Supabase Migration SQL
-- Run this in Supabase → SQL Editor → New Query
-- =============================================

-- Core tables
CREATE TABLE IF NOT EXISTS research_sessions (
    id BIGSERIAL PRIMARY KEY,
    niche TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    products_found INT DEFAULT 0,
    platforms_scraped TEXT,
    google_trends_data TEXT,
    real_time_events TEXT,
    pinterest_trends TEXT,
    competitor_data TEXT,
    gemini_niche_analysis TEXT,
    scoring_weights_used TEXT,
    status TEXT DEFAULT 'running',
    error_log TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    platform TEXT,
    original_url TEXT,
    price DOUBLE PRECISION,
    mrp DOUBLE PRECISION,
    discount_pct DOUBLE PRECISION,
    rating DOUBLE PRECISION,
    review_count INT,
    asin TEXT,
    image_url TEXT,
    additional_images TEXT,
    description TEXT,
    feature_bullets TEXT,
    niche TEXT,
    score DOUBLE PRECISION,
    trend_bonus DOUBLE PRECISION,
    commission_estimate DOUBLE PRECISION,
    affiliate_type TEXT,
    stock_status TEXT,
    badges TEXT,
    gemini_sell_reason TEXT,
    research_session_id BIGINT REFERENCES research_sessions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS published_pins (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id),
    niche TEXT,
    affiliate_link TEXT,
    affiliate_type TEXT,
    affiliate_platform TEXT,
    pin_image_cloudinary_url TEXT,
    pin_image_local_path TEXT,
    title TEXT,
    description TEXT,
    seo_keywords TEXT,
    hashtags TEXT,
    topic_tags TEXT,
    scheduled_time TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    pinterest_pin_id TEXT,
    instagram_post_id TEXT,
    status TEXT DEFAULT 'pending',
    skip_reason TEXT,
    user_edits TEXT,
    original_ai_content TEXT,
    retry_count INT DEFAULT 0,
    last_retry_at TIMESTAMPTZ,
    pinterest_clicks INT DEFAULT 0,
    pinterest_impressions INT DEFAULT 0,
    pinterest_saves INT DEFAULT 0,
    instagram_reach INT DEFAULT 0,
    instagram_clicks INT DEFAULT 0,
    estimated_commission DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics (
    id BIGSERIAL PRIMARY KEY,
    pin_id BIGINT REFERENCES published_pins(id),
    fetch_date TIMESTAMPTZ,
    clicks INT DEFAULT 0,
    impressions INT DEFAULT 0,
    saves INT DEFAULT 0,
    estimated_commission DOUBLE PRECISION,
    data_source TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evolution_log (
    id BIGSERIAL PRIMARY KEY,
    log_type TEXT,
    data TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    type TEXT,
    title TEXT,
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS competitor_accounts (
    id BIGSERIAL PRIMARY KEY,
    niche TEXT,
    pinterest_url TEXT,
    account_name TEXT,
    avg_saves_per_pin DOUBLE PRECISION,
    posting_frequency TEXT,
    content_patterns TEXT,
    hashtag_strategy TEXT,
    last_analyzed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hashtag_performance (
    id BIGSERIAL PRIMARY KEY,
    hashtag TEXT,
    niche TEXT,
    times_used INT DEFAULT 0,
    avg_clicks_when_used DOUBLE PRECISION DEFAULT 0,
    performance_score DOUBLE PRECISION DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS keyword_performance (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT,
    niche TEXT,
    times_used INT DEFAULT 0,
    avg_clicks_when_used DOUBLE PRECISION DEFAULT 0,
    performance_score DOUBLE PRECISION DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Evolution tables (replace JSON files)
CREATE TABLE IF NOT EXISTS evolution_performance_log (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evolution_strategy_memory (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evolution_competitor_insights (
    id BIGSERIAL PRIMARY KEY,
    niche TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evolution_learning_history (
    id BIGSERIAL PRIMARY KEY,
    date TEXT,
    research_sessions INT DEFAULT 0,
    insights TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- STORAGE BUCKET — Run in Supabase → Storage
-- Create a PUBLIC bucket called "pin-images"
-- =============================================
-- Go to Supabase Dashboard → Storage → New Bucket
-- Name: pin-images
-- Public: YES (toggle on)
-- File size limit: 50MB
-- Allowed types: image/jpeg, image/png, image/webp
