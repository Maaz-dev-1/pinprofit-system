from fastapi import APIRouter, Query, HTTPException
from services.supabase_client import get_supabase
from models.schemas import ProductOut, ProductListOut

router = APIRouter()


@router.get("", response_model=ProductListOut)
async def list_products(
    niche: str = Query(None),
    platform: str = Query(None),
    sort: str = Query("score"),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
):
    sb = get_supabase()
    q = sb.table("products").select("*", count="exact")

    if niche:
        q = q.ilike("niche", f"%{niche}%")
    if platform and platform.lower() != "all":
        q = q.ilike("platform", f"%{platform}%")
    if search:
        q = q.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")

    # Sort
    sort_map = {
        "score":      ("score", True),
        "commission": ("commission_estimate", True),
        "rating":     ("rating", True),
        "price_asc":  ("price", False),
        "price_desc": ("price", True),
    }
    col, desc = sort_map.get(sort, ("score", True))
    q = q.order(col, desc=desc)

    # Paginate
    offset = (page - 1) * per_page
    q = q.range(offset, offset + per_page - 1)

    result = q.execute()
    total = result.count or 0
    items = result.data or []

    return ProductListOut(items=items, total=total, page=page, per_page=per_page)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int):
    sb = get_supabase()
    result = sb.table("products").select("*").eq("id", product_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.data[0]
