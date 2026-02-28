"""
Trend Detector Service
Handles: Google Trends, real-time event detection, Pinterest trends scraping.
All queries are dynamic — driven by user's niche input.
"""
import logging
import time
import random
from typing import Any

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# GOOGLE TRENDS ANALYSIS
# ──────────────────────────────────────────────
def analyze_google_trends(niche: str) -> dict:
    """
    Analyze Google Trends for the niche using pytrends.
    Returns rising queries, breakout queries, geographic data.
    """
    try:
        from pytrends.request import TrendReq

        pt = TrendReq(hl="en-US", tz=-330, geo="IN", timeout=(10, 25))

        # Build niche + sub-niche variations for comparison
        kw_list = [niche]
        pt.build_payload(kw_list, timeframe="now 7-d", geo="IN")

        interest_over_time = pt.interest_over_time()
        rising_queries     = {}
        breakout_queries   = {}
        related_topics     = {}

        try:
            related = pt.related_queries()
            for kw in kw_list:
                if kw in related:
                    rising = related[kw].get("rising")
                    if rising is not None and not rising.empty:
                        top_rising = rising.head(10).to_dict("records")
                        rising_queries[kw] = top_rising
                        breakout_queries[kw] = [
                            q for q in top_rising if q.get("value", 0) >= 5000
                        ]
        except Exception as e:
            logger.warning(f"Related queries failed: {e}")

        try:
            topics = pt.related_topics()
            for kw in kw_list:
                if kw in topics:
                    rising_topics = topics[kw].get("rising")
                    if rising_topics is not None and not rising_topics.empty:
                        related_topics[kw] = rising_topics.head(5).to_dict("records")
        except Exception as e:
            logger.warning(f"Related topics failed: {e}")

        # Interest percentage
        interest_pct = 0
        if not interest_over_time.empty and niche in interest_over_time.columns:
            interest_pct = int(interest_over_time[niche].mean())

        return {
            "niche": niche,
            "interest_pct": interest_pct,
            "rising_queries": rising_queries,
            "breakout_queries": breakout_queries,
            "related_topics": related_topics,
            "is_trending": interest_pct > 40,
        }

    except Exception as e:
        logger.error(f"Google Trends failed: {e}")
        return {"niche": niche, "interest_pct": 0, "rising_queries": {}, "is_trending": False, "error": str(e)}


# ──────────────────────────────────────────────
# REAL-TIME EVENT DETECTION
# ──────────────────────────────────────────────
def detect_realtime_events(niche: str) -> dict:
    """
    Detect real-time trending topics and events in India
    that could boost this niche. Fully dynamic — no hardcoded festivals.
    """
    from datetime import datetime
    import requests
    from bs4 import BeautifulSoup

    headers = _get_random_headers()
    events  = []
    trending_topics = []

    # SOURCE A — Google search for current trends
    try:
        month = datetime.now().strftime("%B %Y")
        queries = [
            f"trending in India today",
            f"upcoming festivals India {month}",
            f"{niche} trending India",
        ]
        for q in queries:
            time.sleep(random.uniform(2, 4))
            url = f"https://www.google.com/search?q={q.replace(' ', '+')}&num=5"
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            texts = [el.get_text(strip=True) for el in soup.select("h3, .BNeawe")]
            events.extend(texts[:5])
    except Exception as e:
        logger.warning(f"Google event search failed: {e}")

    # SOURCE B — pytrends trending searches India
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-US", tz=-330)
        trending = pt.trending_searches(pn="india")
        if trending is not None and not trending.empty:
            trending_topics = trending[0].tolist()[:20]
    except Exception as e:
        logger.warning(f"pytrends trending failed: {e}")

    # Combine and return
    all_items = list(set(events + trending_topics))
    return {
        "niche": niche,
        "trending_topics": trending_topics[:15],
        "detected_events": events[:10],
        "combined": all_items[:20],
    }


# ──────────────────────────────────────────────
# PINTEREST TRENDS SCRAPING
# ──────────────────────────────────────────────
def scrape_pinterest_trends(niche: str) -> dict:
    """
    Scrape Pinterest trends page for India.
    Extract trending keywords and topics related to niche.
    """
    import requests
    from bs4 import BeautifulSoup

    headers = _get_random_headers()
    trending_keywords = []

    try:
        url = "https://trends.pinterest.com/"
        time.sleep(random.uniform(2, 4))
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        # Extract any visible trend items
        items = soup.find_all(["h2", "h3", "span", "a"], limit=100)
        for item in items:
            text = item.get_text(strip=True)
            if niche.lower() in text.lower() or len(text) < 50:
                trending_keywords.append(text)
        trending_keywords = list(set(trending_keywords))[:20]
    except Exception as e:
        logger.warning(f"Pinterest trends scrape failed: {e}")

    return {
        "niche": niche,
        "trending_keywords": trending_keywords,
        "is_trending_on_pinterest": len(trending_keywords) > 0,
    }


# ──────────────────────────────────────────────
# UTILITY
# ──────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def _get_random_headers() -> dict:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8,hi;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
