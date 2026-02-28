"""
Content Generator Service
Uses Google Gemini AI to generate pin titles, descriptions,
SEO keywords, hashtags, topic tags, and best posting times.
All content is niche-specific and trend-aware.
"""
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _get_gemini_model(api_key: str = None):
    import google.generativeai as genai
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("Gemini API key not set")
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-1.5-flash")


async def generate_pin_content(
    product: dict,
    niche: str,
    trends_data: dict,
    events_data: dict,
    competitor_insights: dict,
    api_key: str = None,
) -> dict:
    """
    Generate complete pin content using Gemini AI.
    Returns: title, description, keywords, hashtags, topic_tags, posting_time
    """
    try:
        model = _get_gemini_model(api_key)
    except ValueError as e:
        return {"error": str(e)}

    trending_topics = events_data.get("trending_topics", [])
    rising_queries  = list(trends_data.get("rising_queries", {}).values())[:3]

    prompt = f"""You are an expert Pinterest affiliate marketer for the Indian market.

Product Details:
- Title: {product.get('title', '')}
- Description: {product.get('description', 'Not available')}
- Platform: {product.get('platform', '').title()}
- Price: ₹{product.get('price', 'N/A')}
- Rating: {product.get('rating', 'N/A')} stars ({product.get('review_count', 0)} reviews)
- Niche: {niche}

Current Trending Topics in India: {', '.join(trending_topics[:10])}
Rising Google Searches: {', '.join(str(q) for q in rising_queries[:5])}

Generate the following for a Pinterest + Instagram post:

1. TITLE: Use the exact product title as given. Optionally add ONE relevant emoji at the start if it fits naturally. Do not shorten or rewrite.

2. DESCRIPTION: Use the exact product description if available. If not, create a compelling 2-3 sentence description based on the product details. Add maximum 2 sentences connecting to current trends and a call-to-action. Keep under 500 characters total.

3. SEO_KEYWORDS: Generate 15 highly specific buyer-intent keywords for this exact product in this niche for Indian market. Mix: long-tail, location-specific (India), price-specific, trend-specific. Return as comma-separated list.

4. HASHTAGS: Generate 15 hashtags — mix of broad (#HomeDecor), medium (#ModernHomeDecor), specific (#MinimalistDecor), India-specific (#IndiaFinds), and current trend tags. Return as space-separated #hashtag list.

5. TOPIC_TAGS: Select 4 most relevant Pinterest topic categories for this product. Return as comma-separated list.

6. SELL_REASON: In 1 sentence, explain why this product will sell well RIGHT NOW based on current trends.

Format your response EXACTLY as:
TITLE: [title here]
DESCRIPTION: [description here]
SEO_KEYWORDS: [keyword1, keyword2, ...]
HASHTAGS: [#tag1 #tag2 ...]
TOPIC_TAGS: [topic1, topic2, topic3, topic4]
SELL_REASON: [one sentence reason]"""

    try:
        response = model.generate_content(prompt)
        text = response.text
        return _parse_content_response(text, product)
    except Exception as e:
        logger.error(f"Gemini content generation failed: {e}")
        return {"error": f"Content generation failed: {str(e)}"}


def _parse_content_response(text: str, product: dict) -> dict:
    """Parse Gemini response into structured content dict."""
    lines = text.strip().split("\n")
    result = {
        "title": "",
        "description": "",
        "seo_keywords": [],
        "hashtags": [],
        "topic_tags": [],
        "sell_reason": "",
    }

    for line in lines:
        if line.startswith("TITLE:"):
            result["title"] = line[6:].strip()
        elif line.startswith("DESCRIPTION:"):
            result["description"] = line[12:].strip()
        elif line.startswith("SEO_KEYWORDS:"):
            kws = line[13:].strip()
            result["seo_keywords"] = [k.strip() for k in kws.split(",") if k.strip()]
        elif line.startswith("HASHTAGS:"):
            hs = line[9:].strip()
            result["hashtags"] = [h.strip() for h in hs.split() if h.strip().startswith("#")]
        elif line.startswith("TOPIC_TAGS:"):
            ts = line[11:].strip()
            result["topic_tags"] = [t.strip() for t in ts.split(",") if t.strip()]
        elif line.startswith("SELL_REASON:"):
            result["sell_reason"] = line[12:].strip()

    # Fallbacks
    if not result["title"]:
        result["title"] = product.get("title", "")

    return result


def calculate_best_posting_time() -> dict:
    """
    Calculate best Pinterest posting time in IST.
    Based on platform data and day of week.
    """
    now_ist = datetime.now(timezone.utc)
    weekday = now_ist.weekday()  # 0=Mon, 6=Sun

    if weekday == 6:  # Sunday — highest traffic
        primary   = "8:00 PM IST"
        secondary = "10:00 AM IST"
        reason    = "Sunday has the highest Pinterest traffic in India. Evening slots see peak engagement."
    elif weekday == 5:  # Saturday
        primary   = "7:30 PM IST"
        secondary = "11:00 AM IST"
        reason    = "Saturday evenings are highly active. People browse Pinterest during leisure time."
    else:  # Weekdays
        primary   = "9:00 PM IST"
        secondary = "1:00 PM IST"
        reason    = "Weekday evenings (8PM-11PM IST) are peak times when people relax after work."

    return {
        "primary":   primary,
        "secondary": secondary,
        "reason":    reason,
    }
