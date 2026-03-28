"""Product service.

В бета-версии целевой backend хранения — MongoDB.
Если MongoDB недоступна, используется безопасный fallback в in-memory режим.
"""

import os
from typing import Protocol

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# FastAPI application for products API.
app = FastAPI(title="Product Service")

# Разрешаем запросы с фронтенда (демо режим).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Каталог товаров с большим набором актуальных категорий (fallback-данные).
FALLBACK_PRODUCTS = [
    {"id": 1, "name": "Холодильник", "price": 50000, "category": "Кухня", "in_stock": True},
    {"id": 2, "name": "Телевизор", "price": 40000, "category": "Дом", "in_stock": True},
    {"id": 3, "name": "Посудомоечная машина", "price": 43000, "category": "Кухня", "in_stock": True},
    {"id": 4, "name": "Стиральная машина", "price": 37000, "category": "Дом", "in_stock": False},
    {"id": 5, "name": "Ноутбук", "price": 85000, "category": "Электроника", "in_stock": True},
    {"id": 6, "name": "Смартфон", "price": 65000, "category": "Электроника", "in_stock": True},
    {"id": 7, "name": "Планшет", "price": 35000, "category": "Электроника", "in_stock": True},
    {"id": 8, "name": "Пылесос", "price": 19000, "category": "Дом", "in_stock": True},
    {"id": 9, "name": "Микроволновая печь", "price": 14000, "category": "Кухня", "in_stock": False},
    {"id": 10, "name": "Кофемашина", "price": 28000, "category": "Кухня", "in_stock": True},
    {"id": 11, "name": "Электрочайник", "price": 4500, "category": "Кухня", "in_stock": True},
    {"id": 12, "name": "Утюг", "price": 3900, "category": "Дом", "in_stock": True},
]


class ProductRepository(Protocol):
    """Абстракция репозитория продуктов."""

    def list_products(self) -> list[dict]:
        """Return all products from selected storage backend."""


class InMemoryProductRepository:
    """Fallback repository for local/testing scenarios."""

    def __init__(self, items: list[dict]):
        self._items = items

    def list_products(self) -> list[dict]:
        return list(self._items)


class MongoProductRepository:
    """MongoDB repository used by default in beta configuration."""

    def __init__(self, uri: str, db_name: str, collection_name: str):
        try:
            from pymongo import MongoClient  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"pymongo import error: {exc}") from exc

        self._client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        self._db_name = db_name
        self._collection_name = collection_name

        # Force connection check early for transparent failure handling.
        self._client.admin.command("ping")

    def list_products(self) -> list[dict]:
        collection = self._client[self._db_name][self._collection_name]
        docs = list(collection.find({}, {"_id": 0}))
        return docs


def _build_repository() -> tuple[ProductRepository, str]:
    """Build repository and backend mode based on environment settings."""
    storage_mode = os.getenv("PRODUCT_STORAGE", "mongodb").lower()
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGODB_DB", "shop")
    mongo_collection = os.getenv("MONGODB_COLLECTION", "products")

    if storage_mode == "mongodb":
        try:
            return MongoProductRepository(mongo_uri, mongo_db, mongo_collection), "mongodb"
        except Exception as exc:
            # Системная ошибка в бета допустима, но программа продолжает работать через fallback.
            return InMemoryProductRepository(FALLBACK_PRODUCTS), f"fallback-memory({type(exc).__name__})"

    return InMemoryProductRepository(FALLBACK_PRODUCTS), "memory"


product_repository, repository_mode = _build_repository()


@app.get("/health")
def healthcheck():
    """Basic liveness endpoint with information about active storage backend."""
    return {"status": "ok", "storage_backend": repository_mode}


@app.get("/products")
def get_products(
    category: str | None = None,
    in_stock: bool | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    sort_by: str = "id",
    order: str = "asc",
    offset: int = 0,
    limit: int = 20,
):
    """Return products with filtering + sorting + pagination scenarios."""
    if min_price is not None and min_price < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_price must be >= 0")

    if max_price is not None and max_price < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="max_price must be >= 0")

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price must be less or equal to max_price",
        )

    filtered_products = product_repository.list_products()

    if category:
        filtered_products = [p for p in filtered_products if str(p.get("category", "")).lower() == category.lower()]

    if in_stock is not None:
        filtered_products = [p for p in filtered_products if p.get("in_stock") is in_stock]

    if min_price is not None:
        filtered_products = [p for p in filtered_products if int(p.get("price", 0)) >= min_price]

    if max_price is not None:
        filtered_products = [p for p in filtered_products if int(p.get("price", 0)) <= max_price]

    if sort_by not in {"id", "price", "name"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid sort_by value")

    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid order value")

    if offset < 0 or limit < 1 or limit > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid pagination parameters")

    reverse = order == "desc"
    sorted_products = sorted(filtered_products, key=lambda p: p.get(sort_by), reverse=reverse)
    paginated_products = sorted_products[offset : offset + limit]

    return {
        "total": len(sorted_products),
        "offset": offset,
        "limit": limit,
        "items": paginated_products,
        "storage_backend": repository_mode,
    }
