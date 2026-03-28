"""Order service with validation, error handling, and multiple scenarios."""

from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# FastAPI application for order workflows.
app = FastAPI(title="Order Service")

# In-memory order registry for beta version demo.
orders: list[dict] = []


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


@app.get("/health")
def healthcheck():
    """Basic liveness endpoint."""
    return {"status": "ok"}


@app.post("/order")
def create_order(order: Order):
    """Create a new order with metadata and default status."""
    order_payload = {
        "id": len(orders) + 1,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": OrderStatus.created.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    orders.append(order_payload)
    return {"status": "order created", "order": order_payload}


@app.get("/orders")
def get_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List orders with optional status filter and pagination."""
    filtered_orders = orders
    if status_filter is not None:
        filtered_orders = [order for order in orders if order["status"] == status_filter.value]

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
    for order in orders:
        if order["id"] == order_id:
            order["status"] = new_status.value
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            return {"status": "updated", "order": order}

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
