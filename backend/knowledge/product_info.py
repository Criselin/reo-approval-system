import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_products: list[dict] = []


def load_products():
    """Load product catalog at startup."""
    global _products
    products_path = _DATA_DIR / "products.json"
    with open(products_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _products = data["products"]


def get_product_info(model_name: str) -> dict | None:
    """Find product by model name (fuzzy matching).

    Args:
        model_name: Product model name or partial name

    Returns:
        Product info dict or None if not found
    """
    if not _products:
        load_products()

    query = model_name.lower().strip()

    # Exact match first
    for product in _products:
        if product["model"].lower() == query:
            return product

    # Partial match
    for product in _products:
        if query in product["model"].lower() or query in product["name"].lower():
            return product

    # Fuzzy: check if any word in the query matches
    query_words = query.split()
    for product in _products:
        product_text = f"{product['model']} {product['name']}".lower()
        if any(word in product_text for word in query_words if len(word) > 2):
            return product

    return None


def list_products(product_type: str | None = None) -> list[dict]:
    """List all products, optionally filtered by type."""
    if not _products:
        load_products()

    if product_type:
        return [p for p in _products if product_type.lower() in p["type"].lower()]
    return _products
