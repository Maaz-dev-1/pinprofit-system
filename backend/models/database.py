"""
Database layer — Supabase PostgreSQL.
Replaces SQLAlchemy + SQLite with supabase-py.
All table operations go through supabase.table().
"""
import os
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ── Table Migration SQL ──────────────────────

MIGRATION_SQL = """
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
"""


async def init_db():
    """Create all tables in Supabase and seed defaults."""
    from services.supabase_client import get_supabase

    sb = get_supabase()

    # Run migration SQL via Supabase RPC (postgrest doesn't support raw SQL,
    # so we use individual table checks — tables auto-created via Supabase dashboard
    # or migration script. For now, try creating via REST if possible.)
    try:
        # Test connection by reading settings table
        sb.table("settings").select("key").limit(1).execute()
        logger.info("Database tables verified.")
    except Exception as e:
        logger.warning(f"Table check issue (tables may need manual creation): {e}")
        logger.info("Please run the migration SQL in Supabase SQL Editor if tables don't exist.")

    # Seed default settings
    await _seed_default_settings()
    logger.info("Database initialized.")


async def _seed_default_settings():
    """Pre-load API keys from env vars into settings table on first run."""
    from services.supabase_client import get_supabase

    env_to_db = {
        "GEMINI_API_KEY":          "gemini_api_key",
        "PINTEREST_APP_ID":        "pinterest_app_id",
        "PINTEREST_APP_SECRET":    "pinterest_app_secret",
        "PINTEREST_ACCESS_TOKEN":  "pinterest_access_token",
        "INSTAGRAM_APP_ID":        "instagram_app_id",
        "INSTAGRAM_APP_SECRET":    "instagram_app_secret",
        "INSTAGRAM_ACCESS_TOKEN":  "instagram_access_token",
        "AMAZON_ACCESS_KEY":       "amazon_access_key",
        "AMAZON_SECRET_KEY":       "amazon_secret_key",
        "AMAZON_ASSOCIATE_TAG":    "amazon_associate_tag",
        "CUELINKS_API_KEY":        "cuelinks_api_key",
        "GMAIL_ADDRESS":           "gmail_address",
        "GMAIL_APP_PASSWORD":      "gmail_app_password",
    }

    sb = get_supabase()
    for env_key, db_key in env_to_db.items():
        val = os.getenv(env_key, "")
        if val:
            try:
                existing = sb.table("settings").select("key").eq("key", db_key).execute()
                if not existing.data:
                    sb.table("settings").insert({
                        "key": db_key,
                        "value": val,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).execute()
            except Exception as e:
                logger.warning(f"Could not seed setting {db_key}: {e}")


# ── Helper functions used by routers ──────────

def get_setting_sync(key: str) -> str | None:
    """Get a setting value from Supabase (synchronous)."""
    from services.supabase_client import get_supabase
    try:
        result = get_supabase().table("settings").select("value").eq("key", key).execute()
        if result.data:
            return result.data[0]["value"]
    except Exception:
        pass
    return None


def set_setting_sync(key: str, value: str):
    """Upsert a setting value to Supabase (synchronous)."""
    from services.supabase_client import get_supabase
    try:
        get_supabase().table("settings").upsert({
            "key": key,
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        from services.supabase_client import queue_write
        queue_write("settings", "upsert", {"key": key, "value": value, "updated_at": datetime.now(timezone.utc).isoformat()})
