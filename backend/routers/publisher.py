import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Query, File, UploadFile, Form
from services.supabase_client import get_supabase
from models.schemas import PinOut, PinListOut

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.get("/pending")
async def get_pending_pins(limit: int = Query(10, ge=1, le=50)):
    sb = get_supabase()
    r = sb.table("published_pins").select("*", count="exact").eq("status", "pending").order("created_at", desc=True).limit(limit).execute()
    return {"items": r.data or [], "total": r.count or 0}


@router.get("")
async def list_pins(
    status: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10),
):
    sb = get_supabase()
    q = sb.table("published_pins").select("*", count="exact")
    if status:
        q = q.eq("status", status)
    q = q.order("created_at", desc=True)
    offset = (page - 1) * per_page
    q = q.range(offset, offset + per_page - 1)
    r = q.execute()
    return {"items": r.data or [], "total": r.count or 0}


@router.post("/generate-content")
async def generate_pin_content(data: dict):
    """Generate AI content for a product pin using Gemini."""
    product_id = data.get("product_id")
    if not product_id:
        return {"error": "product_id required"}

    sb = get_supabase()
    result = sb.table("products").select("*").eq("id", product_id).execute()
    if not result.data:
        return {"error": "Product not found"}
    product = result.data[0]

    from services.content_generator import generate_pin_content as gen, calculate_best_posting_time
    from models.database import get_setting_sync

    api_key = get_setting_sync("gemini_api_key")

    product_dict = {
        "title": product.get("title"),
        "description": product.get("description"),
        "platform": product.get("platform"),
        "price": product.get("price"),
        "rating": product.get("rating"),
        "review_count": product.get("review_count"),
    }

    content = await gen(
        product=product_dict,
        niche=product.get("niche") or "",
        trends_data={},
        events_data={"trending_topics": []},
        competitor_insights={},
        api_key=api_key,
    )

    if content.get("error"):
        niche = product.get("niche") or "trending"
        platform = product.get("platform") or "Store"
        price = product.get("price")
        content = {
            "title": product.get("title"),
            "description": f"Check out {product.get('title')}! Available at ₹{price:,.0f} on {platform.title()}." if price else product.get("description") or "",
            "seo_keywords": [niche, platform, "best price", "India", "online shopping"],
            "hashtags": [f"#{platform.title()}", "#Shopping", "#BestDeals", "#India", "#TrendingNow"],
            "topic_tags": ["Shopping", niche.title()],
            "sell_reason": product.get("gemini_sell_reason") or "Great value product with high ratings.",
        }

    content["posting_time"] = calculate_best_posting_time()
    return content


@router.post("/publish")
async def publish_pin(
    image: UploadFile = File(None),
    product_id: str = Form(""),
    title: str = Form(""),
    description: str = Form(""),
    hashtags: str = Form("[]"),
    keywords: str = Form("[]"),
    post_to_pinterest: str = Form("true"),
    post_to_instagram: str = Form("false"),
):
    """Publish pin to Pinterest and/or Instagram."""
    from models.database import get_setting_sync

    sb = get_supabase()

    # Save uploaded image + upload to Supabase Storage
    image_path = None
    public_url = None

    if image and image.filename:
        ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        filename = f"pin_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        image_path = str(UPLOAD_DIR / filename)
        file_bytes = await image.read()

        # Save locally temporarily
        with open(image_path, "wb") as f:
            f.write(file_bytes)

        # Upload to Supabase Storage (pin-images bucket)
        try:
            storage = sb.storage.from_("pin-images")
            storage.upload(
                path=filename,
                file=file_bytes,
                file_options={"content-type": image.content_type or "image/jpeg"},
            )
            # Build public URL
            project_ref = os.getenv("SUPABASE_URL", "").replace("https://", "").split(".")[0]
            public_url = f"https://{project_ref}.supabase.co/storage/v1/object/public/pin-images/{filename}"
            logger.info(f"Uploaded to Supabase Storage: {public_url}")
        except Exception as e:
            logger.warning(f"Supabase Storage upload failed: {e}")

        # Delete local temp file
        try:
            os.unlink(image_path)
        except Exception:
            pass

    # Get product info
    product = None
    if product_id:
        r = sb.table("products").select("*").eq("id", int(product_id)).execute()
        product = r.data[0] if r.data else None

    # Generate affiliate link
    affiliate_url = product.get("original_url", "") if product else ""
    if product and product.get("affiliate_type") == "amazon_associates" and product.get("asin"):
        from services.affiliate_manager import generate_amazon_affiliate_link_sync
        link = generate_amazon_affiliate_link_sync(product["asin"])
        affiliate_url = link or affiliate_url
    elif product:
        from services.affiliate_manager import generate_cuelinks_link_sync
        link = generate_cuelinks_link_sync(product.get("original_url", ""))
        affiliate_url = link or affiliate_url

    # Parse hashtags/keywords
    try:
        hashtag_list = json.loads(hashtags) if hashtags else []
    except json.JSONDecodeError:
        hashtag_list = []
    try:
        keyword_list = json.loads(keywords) if keywords else []
    except json.JSONDecodeError:
        keyword_list = []

    # Create pin record
    pin_data = {
        "product_id": int(product_id) if product_id else None,
        "niche": product.get("niche") if product else None,
        "title": title,
        "description": description,
        "hashtags": json.dumps(hashtag_list),
        "seo_keywords": json.dumps(keyword_list),
        "pin_image_local_path": None,
        "pin_image_cloudinary_url": public_url,  # Supabase Storage URL stored here
        "affiliate_link": affiliate_url,
        "affiliate_type": product.get("affiliate_type") if product else None,
        "status": "pending",
    }
    r = sb.table("published_pins").insert(pin_data).execute()
    pin_id = r.data[0]["id"] if r.data else None

    results = {"pinterest": None, "instagram": None}

    # Post to Pinterest
    if post_to_pinterest == "true":
        token = get_setting_sync("pinterest_access_token")
        if token and public_url:
            from services.pinterest_api import PinterestAPI
            try:
                api = PinterestAPI(access_token=token)
                boards = await api.get_boards()
                if boards:
                    board_id = boards[0]["id"]
                    result = await api.create_pin(
                        board_id=board_id,
                        title=title,
                        description=description + "\n" + " ".join(hashtag_list),
                        link=affiliate_url,
                        media_url=public_url,
                    )
                    if pin_id:
                        sb.table("published_pins").update({"pinterest_pin_id": result.get("id")}).eq("id", pin_id).execute()
                    results["pinterest"] = "posted"
            except Exception as e:
                logger.error(f"Pinterest post failed: {e}")
                results["pinterest"] = f"failed: {str(e)[:50]}"

    # Post to Instagram
    if post_to_instagram == "true":
        token = get_setting_sync("instagram_access_token")
        if token and public_url:
            from services.instagram_api import InstagramAPI
            try:
                api = InstagramAPI(access_token=token)
                ig_id = await api.get_ig_business_account()
                if ig_id:
                    caption = f"{title}\n\n{description}\n\n{' '.join(hashtag_list)}"
                    result = await api.publish_image(ig_id, public_url, caption)
                    if pin_id:
                        sb.table("published_pins").update({"instagram_post_id": result.get("id")}).eq("id", pin_id).execute()
                    results["instagram"] = "posted"
            except Exception as e:
                logger.error(f"Instagram post failed: {e}")
                results["instagram"] = f"failed: {str(e)[:50]}"

    # Update pin status
    status = "posted" if results["pinterest"] == "posted" or results["instagram"] == "posted" else "pending"
    update_data = {"status": status}
    if status == "posted":
        update_data["posted_at"] = datetime.now(timezone.utc).isoformat()
    if pin_id:
        sb.table("published_pins").update(update_data).eq("id", pin_id).execute()

    # Log evolution event
    sb.table("evolution_log").insert({
        "log_type": "pin_published",
        "data": json.dumps({
            "message": f"Pin published: {title[:50]}",
            "pinterest": results["pinterest"],
            "instagram": results["instagram"],
        }),
    }).execute()

    return {
        "ok": True,
        "pin_id": pin_id,
        "results": results,
        "message": "Pin published!" if status == "posted" else "Pin saved as pending.",
    }
