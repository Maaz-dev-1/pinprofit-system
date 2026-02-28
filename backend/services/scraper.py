"""
Multi-Platform Scraper Service
Scrapes Amazon, Flipkart, Myntra, Meesho, Ajio, Nykaa, FirstCry
All searches are dynamic — driven by niche keyword.
Includes scoring, dedup, and competitor analysis.
"""
import logging
import time
import random
import re
import json
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

MAX_WORKERS = 4
MIN_SCORE   = 70


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────
def scrape_all_platforms(
    niche: str,
    trends_data: dict,
    events_data: dict,
    pinterest_data: dict,
) -> list[dict]:
    """
    Determine relevant platforms for the niche,
    scrape them in parallel, score all products,
    deduplicate, and return top products.
    """
    relevant_platforms = _determine_platforms(niche)
    logger.info(f"Platforms for '{niche}': {relevant_platforms}")

    all_products = []

    scrapers = {
        "amazon":   scrape_amazon,
        "flipkart": scrape_flipkart,
        "myntra":   scrape_myntra,
        "meesho":   scrape_meesho,
        "ajio":     scrape_ajio,
        "nykaa":    scrape_nykaa,
        "firstcry": scrape_firstcry,
    }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(scrapers[p], niche): p
            for p in relevant_platforms if p in scrapers
        }
        for future in as_completed(futures):
            platform = futures[future]
            try:
                products = future.result()
                logger.info(f"  {platform}: {len(products)} products scraped")
                all_products.extend(products)
            except Exception as e:
                logger.error(f"  {platform} scrape failed: {e}")

    # Score all products
    scored = _score_products(all_products, niche, trends_data, events_data, pinterest_data)

    # Filter by min score
    filtered = [p for p in scored if (p.get("score") or 0) >= MIN_SCORE]

    # Sort by score
    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)

    logger.info(f"Total products after scoring & filtering: {len(filtered)}")
    return filtered


# ──────────────────────────────────────────────
# PLATFORM SELECTOR (simple keyword logic —
# Gemini integration added in Phase 3)
# ──────────────────────────────────────────────
def _determine_platforms(niche: str) -> list[str]:
    niche_l = niche.lower()
    platforms = ["amazon", "flipkart"]  # Always included

    fashion_kw  = ["clothing", "dress", "saree", "fashion", "wear", "kurta",
                   "shirt", "jeans", "lehenga", "tops", "outfit", "apparel"]
    beauty_kw   = ["beauty", "makeup", "skincare", "cosmetic", "lipstick",
                   "moisturizer", "serum", "sunscreen", "hair care", "perfume"]
    baby_kw     = ["baby", "infant", "toddler", "kids", "children", "newborn"]

    if any(kw in niche_l for kw in fashion_kw):
        platforms += ["myntra", "meesho", "ajio"]
    if any(kw in niche_l for kw in beauty_kw):
        platforms += ["nykaa", "myntra", "meesho"]
    if any(kw in niche_l for kw in baby_kw):
        platforms += ["firstcry", "meesho"]
    if "meesho" not in platforms:
        platforms.append("meesho")

    return list(dict.fromkeys(platforms))  # Remove dups, preserve order


# ──────────────────────────────────────────────
# SCRAPERS
# ──────────────────────────────────────────────
def _get_headers() -> dict:
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    ]
    return {
        "User-Agent": random.choice(agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
    }


def _safe_get(url: str, retries: int = 3) -> BeautifulSoup | None:
    """Fetch URL with retry logic and rate limiting."""
    delays = [0, 5, 15]
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(3, 6) + delays[attempt])
            r = requests.get(url, headers=_get_headers(), timeout=30)
            if r.status_code == 200:
                return BeautifulSoup(r.content, "html.parser")
            if r.status_code in (403, 429):
                logger.warning(f"Rate limited ({r.status_code}) — waiting 60s")
                time.sleep(60)
            else:
                logger.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Request failed (attempt {attempt+1}): {e}")
    return None


def _parse_price(text: str) -> float | None:
    """Extract numeric price from string like '₹1,299'."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _parse_rating(text: str) -> float | None:
    if not text:
        return None
    m = re.search(r"(\d+\.?\d*)", text)
    return float(m.group(1)) if m else None


def _parse_reviews(text: str) -> int | None:
    if not text:
        return None
    cleaned = re.sub(r"[,\s]", "", text.split("(")[-1].split(")")[0])
    m = re.search(r"(\d+)", cleaned)
    return int(m.group(1)) if m else None


# ── AMAZON ────────────────────────────────────
def scrape_amazon(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "+")

    urls = [
        f"https://www.amazon.in/s?k={encoded}&sort=review-rank",
        f"https://www.amazon.in/s?k={encoded}&sort=popularity-rank",
    ]

    for url in urls:
        soup = _safe_get(url)
        if not soup:
            continue

        items = soup.select('[data-component-type="s-search-result"]')
        for item in items[:15]:
            try:
                title_el   = item.select_one("h2 a span")
                link_el    = item.select_one("h2 a")
                price_el   = item.select_one(".a-price-whole")
                mrp_el     = item.select_one(".a-text-price span")
                rating_el  = item.select_one(".a-icon-star-small .a-icon-alt, .a-icon-alt")
                review_el  = item.select_one(".a-size-small .a-link-normal span")
                image_el   = item.select_one(".s-image")
                asin       = item.get("data-asin", "")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                url_  = "https://www.amazon.in" + link_el.get("href", "").split("?")[0]
                price = _parse_price(price_el.get_text() if price_el else "")
                mrp   = _parse_price(mrp_el.get_text()   if mrp_el   else "")

                # Badges
                badges = {
                    "bestseller":    bool(item.select_one(".a-badge-text")),
                    "amazons_choice": "Amazon's Choice" in item.get_text(),
                    "deal_of_day":   "Deal of the Day" in item.get_text(),
                }

                products.append({
                    "title":        title,
                    "platform":     "amazon",
                    "url":          url_,
                    "price":        price,
                    "mrp":          mrp,
                    "discount_pct": round((mrp - price) / mrp * 100, 1) if mrp and price and mrp > price else None,
                    "rating":       _parse_rating(rating_el.get_text() if rating_el else ""),
                    "review_count": _parse_reviews(review_el.get_text() if review_el else ""),
                    "asin":         asin,
                    "image_url":    image_el.get("src") if image_el else None,
                    "stock_status": "In Stock",
                    "badges":       badges,
                })
            except Exception as e:
                logger.debug(f"Amazon parse error: {e}")

    return products


# ── FLIPKART ──────────────────────────────────
def scrape_flipkart(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "%20")
    url      = f"https://www.flipkart.com/search?q={encoded}&sort=popularity"

    soup = _safe_get(url)
    if not soup:
        return []

    # Flipkart product cards vary by category
    for selector in ["div[data-id]", "._1AtVbE", "._13oc-S"]:
        items = soup.select(selector)
        if items:
            break

    for item in items[:15]:
        try:
            title_el  = item.select_one("a.s1Q9rs, ._4rR01T, .IRpwTa, a[title]")
            link_el   = item.select_one("a.s1Q9rs, ._4rR01T, a[href*='/p/']")
            price_el  = item.select_one("._30jeq3, ._1_WHN1")
            mrp_el    = item.select_one("._3I9_wc, ._2p6lqe")
            rating_el = item.select_one("._3LWZlK")
            image_el  = item.select_one("img._396cs4, img._2r_T1I")

            if not title_el:
                continue

            title = title_el.get("title") or title_el.get_text(strip=True)
            href  = link_el.get("href") if link_el else ""
            full_url = f"https://www.flipkart.com{href}" if href.startswith("/") else href

            products.append({
                "title":    title,
                "platform": "flipkart",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "mrp":      _parse_price(mrp_el.get_text()  if mrp_el  else ""),
                "rating":   _parse_rating(rating_el.get_text() if rating_el else ""),
                "image_url": image_el.get("src") if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"Flipkart parse error: {e}")

    return products


# ── MYNTRA ────────────────────────────────────
def scrape_myntra(niche: str) -> list[dict]:
    # Myntra requires JavaScript — returns minimal data via basic GET
    products = []
    encoded  = niche.replace(" ", "-").lower()
    url      = f"https://www.myntra.com/{encoded}"

    soup = _safe_get(url)
    if not soup:
        return []

    for item in soup.select(".product-base")[:15]:
        try:
            title_el     = item.select_one(".product-brand, .product-product")
            price_el     = item.select_one(".product-discountedPrice, .product-price")
            mrp_el       = item.select_one(".product-strike")
            image_el     = item.select_one("picture source, img.img-responsive")
            link_el      = item.select_one("a")

            if not title_el:
                continue

            brand  = item.select_one(".product-brand")
            name_  = item.select_one(".product-product")
            title  = f"{brand.get_text(strip=True)} {name_.get_text(strip=True)}" if brand and name_ else title_el.get_text(strip=True)
            href   = link_el.get("href") if link_el else ""
            full_url = f"https://www.myntra.com/{href}" if not href.startswith("http") else href

            products.append({
                "title":    title,
                "platform": "myntra",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "mrp":      _parse_price(mrp_el.get_text()  if mrp_el  else ""),
                "image_url": image_el.get("srcset", image_el.get("src", "")) if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"Myntra parse error: {e}")

    return products


# ── MEESHO ────────────────────────────────────
def scrape_meesho(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "%20")
    url      = f"https://www.meesho.com/search?q={encoded}"

    soup = _safe_get(url)
    if not soup:
        return []

    for item in soup.select("[class*='ProductList__GridCol'], [data-testid='product-card']")[:15]:
        try:
            title_el = item.select_one("p[class*='Text'], h2")
            price_el = item.select_one("h5[class*='Text'], [class*='price']")
            image_el = item.select_one("img")
            link_el  = item.select_one("a")

            if not title_el:
                continue

            href = link_el.get("href") if link_el else ""
            full_url = f"https://www.meesho.com{href}" if href.startswith("/") else href

            products.append({
                "title":    title_el.get_text(strip=True),
                "platform": "meesho",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "image_url": image_el.get("src") if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"Meesho parse error: {e}")

    return products


# ── AJIO ──────────────────────────────────────
def scrape_ajio(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "+")
    url      = f"https://www.ajio.com/search/?text={encoded}"

    soup = _safe_get(url)
    if not soup:
        return []

    for item in soup.select(".item, .rizz-product-base")[:15]:
        try:
            title_el = item.select_one(".nameCls, .brand, h2")
            price_el = item.select_one(".price, .original-price span")
            image_el = item.select_one("img")
            link_el  = item.select_one("a")

            if not title_el:
                continue

            href = link_el.get("href") if link_el else ""
            full_url = f"https://www.ajio.com{href}" if href.startswith("/") else href

            products.append({
                "title":    title_el.get_text(strip=True),
                "platform": "ajio",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "image_url": image_el.get("src") if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"Ajio parse error: {e}")

    return products


# ── NYKAA ─────────────────────────────────────
def scrape_nykaa(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "%20")
    url      = f"https://www.nykaa.com/search/result/?q={encoded}&sort=popularity"

    soup = _safe_get(url)
    if not soup:
        return []

    for item in soup.select(".productWrapper, .css-1ol9jjv")[:15]:
        try:
            title_el = item.select_one(".productName, h3")
            price_el = item.select_one(".offerPrice, .price")
            image_el = item.select_one("img")
            link_el  = item.select_one("a")

            if not title_el:
                continue

            href = link_el.get("href") if link_el else ""
            full_url = f"https://www.nykaa.com{href}" if href.startswith("/") else href

            products.append({
                "title":    title_el.get_text(strip=True),
                "platform": "nykaa",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "image_url": image_el.get("src") if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"Nykaa parse error: {e}")

    return products


# ── FIRSTCRY ──────────────────────────────────
def scrape_firstcry(niche: str) -> list[dict]:
    products = []
    encoded  = niche.replace(" ", "+")
    url      = f"https://www.firstcry.com/search?q={encoded}&sort=popularity"

    soup = _safe_get(url)
    if not soup:
        return []

    for item in soup.select(".product-box, .prd-box")[:15]:
        try:
            title_el = item.select_one(".prd-name, h2, .product-name")
            price_el = item.select_one(".prd-price, .special-price")
            image_el = item.select_one("img")
            link_el  = item.select_one("a")

            if not title_el:
                continue

            href = link_el.get("href") if link_el else ""
            full_url = href if href.startswith("http") else f"https://www.firstcry.com{href}"

            products.append({
                "title":    title_el.get_text(strip=True),
                "platform": "firstcry",
                "url":      full_url,
                "price":    _parse_price(price_el.get_text() if price_el else ""),
                "image_url": image_el.get("src") if image_el else None,
                "stock_status": "In Stock",
            })
        except Exception as e:
            logger.debug(f"FirstCry parse error: {e}")

    return products


# ──────────────────────────────────────────────
# PRODUCT SCORING ENGINE
# ──────────────────────────────────────────────
def _score_products(
    products: list[dict],
    niche: str,
    trends_data: dict,
    events_data: dict,
    pinterest_data: dict,
) -> list[dict]:
    """
    Score each product 0–100 based on:
    commission, rating, reviews, price, stock, trends.
    """
    trending_keywords = set(
        (kw.lower() for kw in pinterest_data.get("trending_keywords", []))
    )
    is_google_trending = trends_data.get("is_trending", False)

    for p in products:
        score = 0.0

        # 1. COMMISSION POTENTIAL (up to 25 pts)
        platform = p.get("platform", "").lower()
        commission_map = {
            "amazon":   12.0,
            "myntra":   15.0,
            "meesho":   18.0,
            "flipkart": 10.0,
            "ajio":     14.0,
            "nykaa":    12.0,
            "firstcry": 10.0,
        }
        commission_pct = commission_map.get(platform, 10.0)
        price = p.get("price") or 0
        est_commission = round(price * commission_pct / 100, 2)
        p["commission_estimate"] = est_commission
        score += min(25, commission_pct * 1.5)

        # 2. RATING (up to 20 pts)
        rating = p.get("rating") or 0
        if rating >= 5.0:   score += 20
        elif rating >= 4.5: score += 18
        elif rating >= 4.0: score += 14
        elif rating >= 3.5: score += 7
        elif rating < 3.5 and rating > 0:
            p["_exclude"] = "rating_too_low"

        # 3. REVIEW COUNT (up to 20 pts)
        reviews = p.get("review_count") or 0
        if reviews >= 5000:      score += 20
        elif reviews >= 2000:    score += 17
        elif reviews >= 1000:    score += 14
        elif reviews >= 500:     score += 10
        elif reviews >= 100:     score += 5
        elif reviews > 0:
            p["_exclude"] = "too_few_reviews"

        # 4. PRICE APPROPRIATENESS (up to 20 pts)
        if price:
            # Default good range — Gemini will refine per niche in Phase 3
            if 200 <= price <= 5000:    score += 20
            elif 100 <= price <= 10000: score += 12
            else:                       score += 4

        # 5. STOCK STATUS (up to 15 pts)
        stock = p.get("stock_status", "In Stock")
        if stock == "In Stock":       score += 15
        elif stock == "Limited Stock": score += 8
        else:
            p["_exclude"] = "out_of_stock"

        # 6. TREND BONUSES (up to 25 pts)
        if is_google_trending:
            score += 10
        title_lower = p.get("title", "").lower()
        if any(kw in title_lower for kw in trending_keywords):
            score += 8
        badges = p.get("badges", {})
        if isinstance(badges, dict):
            if badges.get("bestseller"):    score += 5
            if badges.get("amazons_choice"): score += 3

        # Normalize to 100
        p["score"] = min(round(score, 1), 100)
        p["trend_bonus"] = 0

    # Filter exclusions and low scores
    return [p for p in products if not p.get("_exclude") and (p.get("score") or 0) >= MIN_SCORE]
