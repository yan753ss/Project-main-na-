"""Smoke/integration-like tests for beta backend services."""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

# Allow imports from repository root when running pytest in this environment.
sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.notification_service.app.main import healthcheck as notification_healthcheck
from backend.notification_service.app.main import notify
from backend.order_service.app.main import (
    Order,
    OrderStatus,
    create_order,
    get_orders,
    healthcheck as order_healthcheck,
    orders,
    update_order_status,
)
from backend.product_service.app.main import get_products, healthcheck as product_healthcheck
from backend.user_service.app.main import User, get_users, healthcheck as user_healthcheck, login, register, users


def setup_function():
    """Reset in-memory storages before each test."""
    users.clear()
    orders.clear()


def test_health_endpoints():
    """Every service should answer liveness checks."""
    user_health = user_healthcheck()
    assert user_health["status"] == "ok"
    assert user_health["auth_mode"] == "bcrypt+jwt"
    product_health = product_healthcheck()
    assert product_health["status"] == "ok"
    assert "storage_backend" in product_health
    assert order_healthcheck() == {"status": "ok"}
    notification_health = notification_healthcheck()
    assert notification_health["status"] == "ok"
    assert "notification_backend" in notification_health


def test_user_registration_duplicate_login_and_listing():
    """User service should support full auth/listing flow."""
    user = User(email="test@example.com", password="Password123")

    register_result = register(user)
    assert register_result["status"] == "registered"

    with pytest.raises(HTTPException) as duplicate_error:
        register(user)
    assert duplicate_error.value.status_code == 409

    login_result = login(user)
    assert login_result["status"] == "authorized"
    assert isinstance(login_result["access_token"], str)
    assert len(login_result["access_token"]) > 10
    assert login_result["token_type"] == "bearer"
    assert login_result["expires_in"] > 0

    users_listing = get_users()
    assert len(users_listing) == 1
    assert users_listing[0]["email"] == "test@example.com"
    assert users_listing[0]["last_login_at"] is not None


def test_order_validation_creation_filtering_and_status_updates():
    """Order service should validate and support status scenario changes."""
    with pytest.raises(ValidationError):
        Order(product_id=0, quantity=1)

    created = create_order(Order(product_id=1, quantity=2))
    assert created["status"] == "order created"
    assert created["order"]["status"] == OrderStatus.created.value

    listing = get_orders(status_filter=OrderStatus.created, offset=0, limit=10)
    assert listing["total"] == 1
    assert len(listing["items"]) == 1

    updated = update_order_status(order_id=1, new_status=OrderStatus.paid)
    assert updated["status"] == "updated"
    assert updated["order"]["status"] == OrderStatus.paid.value


def test_product_filters_sorting_pagination_and_notification_events():
    """Product and notification services should support broad usage scenarios."""
    kitchen_products = get_products(category="Кухня", sort_by="price", order="desc", offset=0, limit=3)
    assert kitchen_products["total"] >= 1
    assert len(kitchen_products["items"]) <= 3
    assert "storage_backend" in kitchen_products

    in_stock_products = get_products(in_stock=True, min_price=1000, max_price=90000)
    assert in_stock_products["total"] >= 1

    with pytest.raises(HTTPException) as bad_price_range_error:
        get_products(min_price=1000, max_price=500)
    assert bad_price_range_error.value.status_code == 400

    notification = notify(event="order_paid")
    assert notification["event"] == "order_paid"
    assert notification["notification"] == "Событие обработано"
    assert "created_at" in notification
    assert "delivery_mode" in notification
    assert "delivered" in notification
