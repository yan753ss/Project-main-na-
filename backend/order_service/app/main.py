"""Order service with MongoDB storage and in-memory fallback."""

import os
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# FastAPI application for order workflows.
app = FastAPI(title="Order Service")


class OrderStatus(str, Enum):
    """Available order statuses."""

    created = "created"
    paid = "paid"
    shipped = "shipped"
    cancelled = "cancelled"


class Order(BaseModel):
    """Input DTO for creating an order."""

    product_id: int = Field(gt=0, description="ID товара")
    quantity: int = Field(gt=0, le=1000, description="Количество")


class OrderRepository(Protocol):
    """Storage abstraction for order operations."""

    def create_order(self, order_payload: dict) -> dict:
        """Persist order and return saved representation."""

    def list_orders(self) -> list[dict]:
        """Return all stored orders."""

    def update_status(self, order_id: int, new_status: str) -> dict | None:
        """Update order status and return updated order or None."""


class InMemoryOrderRepository:
    """Fallback storage for local/testing scenarios."""

    def __init__(self):
        self._orders: list[dict] = []

    def create_order(self, order_payload: dict) -> dict:
        self._orders.append(order_payload)
        return order_payload

    def list_orders(self) -> list[dict]:
        return list(self._orders)

    def update_status(self, order_id: int, new_status: str) -> dict | None:
        for order in self._orders:
            if order["id"] == order_id:
                order["status"] = new_status
                order["updated_at"] = datetime.now(timezone.utc).isoformat()
                return order
        return None


class MongoOrderRepository:
    """MongoDB storage used by default."""

    def __init__(self, uri: str, db_name: str, collection_name: str):
        from pymongo import MongoClient  # type: ignore

        self._client = MongoClient(uri, serverSelectionTimeoutMS=1000)
        self._db_name = db_name
        self._collection_name = collection_name
        self._client.admin.command("ping")

    @property
    def _collection(self):
        return self._client[self._db_name][self._collection_name]

    def _next_id(self) -> int:
        latest = self._collection.find_one(sort=[("id", -1)])
        return 1 if latest is None else int(latest["id"]) + 1

    def create_order(self, order_payload: dict) -> dict:
        payload = dict(order_payload)
        payload["id"] = self._next_id()
        self._collection.insert_one(payload)
        return payload

    def list_orders(self) -> list[dict]:
        return list(self._collection.find({}, {"_id": 0}))

    def update_status(self, order_id: int, new_status: str) -> dict | None:
        from pymongo import ReturnDocument  # type: ignore

        updated_at = datetime.now(timezone.utc).isoformat()
        result = self._collection.find_one_and_update(
            {"id": order_id},
            {"$set": {"status": new_status, "updated_at": updated_at}},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        return result


def _build_repository() -> tuple[OrderRepository, str]:
    """Build repository based on environment configuration."""
    storage_mode = os.getenv("ORDER_STORAGE", "mongodb").lower()
    mongo_uri = os.getenv("ORDER_MONGODB_URI", os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    mongo_db = os.getenv("ORDER_MONGODB_DB", "shop")
    mongo_collection = os.getenv("ORDER_MONGODB_COLLECTION", "orders")

    if storage_mode == "mongodb":
        try:
            return MongoOrderRepository(mongo_uri, mongo_db, mongo_collection), "mongodb"
        except Exception as exc:
            return InMemoryOrderRepository(), f"fallback-memory({type(exc).__name__})"

    return InMemoryOrderRepository(), "memory"


order_repository, repository_mode = _build_repository()


@app.get("/health")
def healthcheck():
    """Basic liveness endpoint."""
    return {"status": "ok", "storage_backend": repository_mode}


@app.post("/order")
def create_order(order: Order):
    """Create a new order with metadata and default status."""
    order_payload = {
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": OrderStatus.created.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    saved_order = order_repository.create_order(order_payload)
    return {"status": "order created", "order": saved_order}


@app.get("/orders")
def get_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List orders with optional status filter and pagination."""
    all_orders = order_repository.list_orders()
    filtered_orders = all_orders
    if status_filter is not None:
        filtered_orders = [order for order in all_orders if order["status"] == status_filter.value]

    paginated_orders = filtered_orders[offset : offset + limit]
    return {
        "total": len(filtered_orders),
        "offset": offset,
        "limit": limit,
        "items": paginated_orders,
    }


@app.patch("/order/{order_id}/status")
def update_order_status(order_id: int, new_status: OrderStatus):
    """Update order status for broader usage scenarios."""
    updated_order = order_repository.update_status(order_id, new_status.value)
    if updated_order:
        return {"status": "updated", "order": updated_order}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
