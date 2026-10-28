from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from gurkerl_recommender.config import SourceConfig
from gurkerl_recommender.models import Nutrition, Product
from gurkerl_recommender.sample_data import SAMPLE_PRODUCTS


class ProductSource(Protocol):
    def fetch_products(self) -> list[Product]:
        """Fetch candidate products to rank."""


class SampleProductSource:
    def fetch_products(self) -> list[Product]:
        return list(SAMPLE_PRODUCTS)


class JsonProductSource:
    def __init__(self, path: Path) -> None:
        self.path = path

    def fetch_products(self) -> list[Product]:
        with self.path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return [Product.from_dict(item) for item in payload]


class GurkerlProductSource:
    def fetch_products(self) -> list[Product]:
        raise NotImplementedError(
            "Real Gurkerl fetching is not wired yet. Start with sample or json source."
        )


class GurkerlPublicProductSource:
    DEFAULT_URLS = (
        "https://www.gurkerl.at/rette-lebensmittel",
        "https://www.gurkerl.at/aktionen",
    )

    def __init__(self, urls: tuple[str, ...] = ()) -> None:
        self.urls = urls or self.DEFAULT_URLS

    def fetch_products(self) -> list[Product]:
        products: list[Product] = []
        for url in self.urls:
            products.extend(parse_gurkerl_public_html(_fetch_text(url), source_url=url))
        return _deduplicate_products(products)


def enrich_gurkerl_public_details(products: list[Product]) -> list[Product]:
    enriched: list[Product] = []
    for product in products:
        enriched.append(enrich_gurkerl_public_detail(product))
    return enriched


def enrich_gurkerl_public_detail(product: Product) -> Product:
    if product.detail_url is None:
        return product
    nutrition = parse_gurkerl_detail_nutrition_html(_fetch_text(product.detail_url))
    if nutrition is None:
        return product
    return replace(
        product,
        nutrition_per_100g=nutrition,
        nutrition_source="exact",
    )


def build_product_source(config: SourceConfig) -> ProductSource:
    if config.type == "sample":
        return SampleProductSource()
    if config.type == "json":
        if config.products_path is None:
            raise ValueError("source.products_path is required for json source")
        return JsonProductSource(config.products_path)
    if config.type == "gurkerl":
        return GurkerlProductSource()
    if config.type == "gurkerl_public":
        return GurkerlPublicProductSource(config.urls)
    raise ValueError(f"Unknown product source: {config.type}")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text:
            self.lines.append(text)


def parse_gurkerl_public_html(html: str, source_url: str = "") -> list[Product]:
    next_data_products = _parse_next_data_products(html, source_url=source_url)
    if next_data_products:
        return next_data_products

    parser = _TextExtractor()
    parser.feed(html)
    return parse_gurkerl_public_lines(parser.lines, source_url=source_url)


def parse_gurkerl_detail_nutrition_html(html: str) -> Nutrition | None:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
    )
    if match is None:
        return None
    payload = json.loads(match.group(1))
    values = _find_nutritional_values(payload)
    if values is None:
        return None
    return Nutrition(
        protein_g=_nutrient_amount(values, "protein"),
        sugar_g=_nutrient_amount(values, "sugars"),
        calories=_nutrient_amount(values, "energyKCal"),
        fat_g=_nutrient_amount(values, "fats"),
        carbs_g=_nutrient_amount(values, "carbohydrates"),
    )


def _find_nutritional_values(payload: object) -> dict[str, object] | None:
    found: list[dict[str, object]] = []

    def walk(value: object) -> None:
        if found:
            return
        if isinstance(value, dict):
            nutritional_values = value.get("nutritionalValues")
            if isinstance(nutritional_values, list):
                for entry in nutritional_values:
                    if not isinstance(entry, dict):
                        continue
                    values = entry.get("values")
                    if isinstance(values, dict):
                        found.append(values)
                        return
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return found[0] if found else None


def _nutrient_amount(values: dict[str, object], key: str) -> float | None:
    nutrient = values.get(key)
    if not isinstance(nutrient, dict):
        return None
    return _optional_number(nutrient.get("amount"))


def parse_gurkerl_public_lines(
    lines: list[str],
    source_url: str = "",
) -> list[Product]:
    products: list[Product] = []
    current_category = "other"
    pending_expiry: str | None = None
    is_save_food_page = "rette-lebensmittel" in source_url

    for index, line in enumerate(lines):
        category = _map_category(line)
        if category is not None:
            current_category = category
            continue

        if _looks_like_expiry(line):
            pending_expiry = line
            continue

        parsed = _parse_product_line(line)
        if parsed is None:
            continue

        size = _next_size(lines, index)
        category = _infer_category(parsed["name"], current_category)
        products.append(
            Product(
                id=_product_id(source_url, parsed["name"]),
                name=parsed["name"],
                category=category,
                price=parsed["price"],
                size=size,
                nutrition_per_100g=_estimate_nutrition(category, parsed["name"]),
                nutrition_source="estimated",
                detail_url=None,
                is_promotion=not is_save_food_page,
                is_save_food=is_save_food_page or pending_expiry is not None,
                discount_percent=parsed["discount_percent"],
                expires_in_days=_expiry_days(pending_expiry),
                tags=tuple(tag for tag in (pending_expiry, "public-gurkerl") if tag),
            )
        )
        pending_expiry = None

    return products


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 gurkerl-recommender/0.1",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_next_data_products(html: str, source_url: str) -> list[Product]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
    )
    if match is None:
        return []

    payload = json.loads(match.group(1))
    cards = _find_product_cards(payload)
    is_save_food_page = "rette-lebensmittel" in source_url
    products = [
        _product_from_card(card, source_url=source_url, is_save_food_page=is_save_food_page)
        for card in cards
    ]
    return _deduplicate_products([product for product in products if product is not None])


def _find_product_cards(payload: object) -> list[dict[str, object]]:
    cards: list[dict[str, object]] = []

    def walk(value: object) -> None:
        if isinstance(value, dict):
            if _looks_like_product_card(value):
                cards.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return cards


def _looks_like_product_card(value: dict[str, object]) -> bool:
    return "productId" in value and "name" in value and "prices" in value


def _product_from_card(
    card: dict[str, object],
    source_url: str,
    is_save_food_page: bool,
) -> Product | None:
    stock = card.get("stock")
    if isinstance(stock, dict) and stock.get("availabilityStatus") != "AVAILABLE":
        return None

    prices = card.get("prices")
    if not isinstance(prices, dict):
        return None

    sale_price = _optional_number(prices.get("salePrice")) or _optional_number(
        prices.get("price")
    )
    if sale_price is None:
        return None

    original_price = _optional_number(prices.get("originalPrice"))
    discount = _discount_percent(prices.get("saleText"), sale_price, original_price)
    if discount <= 0:
        return None

    name = str(card.get("name", "")).strip()
    if not name:
        return None

    expiry_text = _expiry_badge_text(card)
    category = _infer_category(name, "other")
    return Product(
        id=f"gurkerl-{card['productId']}",
        name=name,
        category=category,
        price=sale_price,
        size=str(card.get("textualAmount") or "") or None,
        brand=str(card["brand"]) if card.get("brand") else None,
        nutrition_per_100g=_estimate_nutrition(category, name),
        nutrition_source="estimated",
        detail_url=_detail_url(card),
        is_promotion=not is_save_food_page,
        is_save_food=is_save_food_page or expiry_text is not None,
        discount_percent=discount,
        expires_in_days=_expiry_days(expiry_text),
        tags=tuple(tag for tag in (expiry_text, "public-gurkerl") if tag),
    )


def _detail_url(card: dict[str, object]) -> str | None:
    slug = card.get("slug")
    product_id = card.get("productId")
    if not slug or not product_id:
        return None
    return f"https://www.gurkerl.at/{product_id}-{slug}"


def _optional_number(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _discount_percent(
    sale_text: object,
    sale_price: float,
    original_price: float | None,
) -> float:
    if isinstance(sale_text, str):
        match = re.search(r"-(\d+)\s*%", sale_text)
        if match:
            return float(match.group(1))
    if original_price and original_price > sale_price:
        return round((original_price - sale_price) / original_price * 100)
    return 0


def _expiry_badge_text(card: dict[str, object]) -> str | None:
    badges = card.get("badges")
    if not isinstance(badges, list):
        return None
    for badge in badges:
        if not isinstance(badge, dict):
            continue
        text = str(badge.get("text", ""))
        if badge.get("type") == "EXPIRING" or _looks_like_expiry(text):
            return text
    return None


def _parse_product_line(line: str) -> dict[str, object] | None:
    match = re.match(
        r"^(?:ca\.\s*)?(\d+)\s+(\d{2})\s+€\s+"
        r"(?:(\d+[,.]\d{2})\s+€\s+)?"
        r"(?:nur heute\s+)?-(\d+)\s+%\s+"
        r"(?:(?:bis|ab)\s+[^A-ZÄÖÜa-zäöü]+)?"
        r"(.+)$",
        line,
    )
    if match is None:
        return None

    euros, cents, _original_price, discount, name = match.groups()
    name = _clean_product_name(name)
    if not name:
        return None
    return {
        "price": float(f"{euros}.{cents}"),
        "discount_percent": float(discount),
        "name": name,
    }


def _clean_product_name(name: str) -> str:
    name = re.sub(r"^(?:bis|ab)\s+\d{1,2}\.\s*\d+\.\s+", "", name)
    name = re.sub(r"^ab\s+\d+\s+Stk\.\s+", "", name)
    return name.strip()


def _next_size(lines: list[str], index: int) -> str | None:
    for candidate in lines[index + 1 : index + 4]:
        if re.search(r"\b(?:g|kg|ml|l|Stk)\b", candidate):
            return candidate
    return None


def _looks_like_expiry(line: str) -> bool:
    return (
        "Morgen verbrauchen" in line
        or "Haltbar bis" in line
        or "Ausverkauft. Haltbar bis" in line
    )


def _expiry_days(line: str | None) -> int | None:
    if line is None:
        return None
    if "Morgen verbrauchen" in line:
        return 1
    return None


def _map_category(line: str) -> str | None:
    categories = {
        "Fleisch & Fisch": "meat",
        "Kühlregal": "dairy",
        "Obst & Gemüse": "vegetables",
        "Brot & Gebäck": "grains",
        "Getränke": "drinks",
        "Süßes & Salziges": "snacks",
        "Vorratsschrank": "grains",
    }
    return categories.get(line.strip())


def _infer_category(name: str, fallback: str) -> str:
    lowered = name.lower()
    if any(
        word in lowered
        for word in (
            "beef",
            "extrawurst",
            "fisch",
            "filet",
            "fleisch",
            "hirsch",
            "huhn",
            "kabeljau",
            "lamm",
            "reh",
            "rind",
            "salami",
            "würstel",
        )
    ):
        return "meat"
    if re.search(r"\b(?:eifix|vollei|eier|ei)\b", lowered):
        return "eggs"
    if any(
        word in lowered
        for word in ("joghurt", "mozzarella", "protein", "skyr", "topfen")
    ):
        return "dairy"
    if any(word in lowered for word in ("spinat", "gurke", "tomate", "zucchini")):
        return "vegetables"
    return fallback


def _estimate_nutrition(category: str, name: str) -> Nutrition:
    lowered = name.lower()
    if category == "meat":
        return Nutrition(protein_g=20, sugar_g=0.5, calories=170)
    if category == "eggs":
        return Nutrition(protein_g=12, sugar_g=1, calories=140)
    if "protein" in lowered or "topfen" in lowered or "skyr" in lowered:
        return Nutrition(protein_g=10, sugar_g=4, calories=100)
    if "milchreis" in lowered or "panna cotta" in lowered:
        return Nutrition(protein_g=3, sugar_g=14, calories=150)
    if "sahne" in lowered or "schmand" in lowered:
        return Nutrition(protein_g=3, sugar_g=4, calories=240)
    if category == "dairy":
        return Nutrition(protein_g=6, sugar_g=5, calories=130)
    if category == "vegetables":
        return Nutrition(protein_g=2, sugar_g=3, calories=40)
    return Nutrition()


def _product_id(source_url: str, name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    source = "save-food" if "rette-lebensmittel" in source_url else "promo"
    return f"{source}-{slug}"


def _deduplicate_products(products: list[Product]) -> list[Product]:
    deduped: dict[str, Product] = {}
    for product in products:
        existing = deduped.get(product.id)
        if existing is None or product.discount_percent > existing.discount_percent:
            deduped[product.id] = product
    return list(deduped.values())
