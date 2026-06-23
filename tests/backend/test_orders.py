"""
Tests for orders API endpoints.
"""
import pytest


class TestOrdersEndpoints:
    """Test suite for orders-related endpoints."""

    # ── Happy path ──────────────────────────────────────────────────────────

    def test_get_all_orders(self, client):
        """Test getting all orders returns a non-empty list."""
        response = client.get("/api/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_order_required_fields(self, client):
        """Test that every order contains all required fields."""
        response = client.get("/api/orders")
        data = response.json()

        required_fields = [
            "id", "order_number", "customer", "items",
            "status", "order_date", "expected_delivery", "total_value",
        ]
        for order in data:
            for field in required_fields:
                assert field in order, f"Order missing field: {field}"

    def test_order_data_types(self, client):
        """Test that order fields have correct data types."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            assert isinstance(order["id"], str)
            assert isinstance(order["order_number"], str)
            assert isinstance(order["customer"], str)
            assert isinstance(order["items"], list)
            assert isinstance(order["status"], str)
            assert isinstance(order["total_value"], (int, float))

    def test_order_status_values(self, client):
        """Test that all orders have a valid status."""
        response = client.get("/api/orders")
        data = response.json()

        valid_statuses = {"delivered", "shipped", "processing", "backordered"}
        for order in data:
            assert order["status"].lower() in valid_statuses, \
                f"Unexpected status: {order['status']}"

    def test_order_total_value_positive(self, client):
        """Test that all order total values are positive."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            assert order["total_value"] > 0, \
                f"Order {order['order_number']} has non-positive total_value"

    def test_order_date_format(self, client):
        """Test that order dates are ISO 8601 strings."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            assert "2025-" in order["order_date"], \
                f"order_date not in expected format: {order['order_date']}"
            assert "T" in order["expected_delivery"], \
                f"expected_delivery missing time component: {order['expected_delivery']}"

    # ── Items sub-structure ──────────────────────────────────────────────────

    def test_order_items_structure(self, client):
        """Test that order items contain required fields with correct types."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            assert len(order["items"]) > 0, \
                f"Order {order['order_number']} has no items"
            for item in order["items"]:
                assert "sku" in item
                assert "name" in item
                assert "quantity" in item
                assert "unit_price" in item
                assert isinstance(item["quantity"], int)
                assert isinstance(item["unit_price"], (int, float))
                assert item["quantity"] > 0
                assert item["unit_price"] > 0

    def test_order_total_value_matches_items(self, client):
        """Test that total_value equals sum of (quantity × unit_price) for each order."""
        response = client.get("/api/orders")
        data = response.json()

        for order in data:
            calculated = sum(
                item["quantity"] * item["unit_price"] for item in order["items"]
            )
            assert abs(order["total_value"] - calculated) < 0.02, (
                f"Order {order['order_number']}: total_value={order['total_value']}, "
                f"calculated={calculated:.2f}"
            )

    # ── Single-resource retrieval ────────────────────────────────────────────

    def test_get_order_by_id(self, client):
        """Test retrieving a specific order by ID."""
        all_orders = client.get("/api/orders").json()
        first_id = all_orders[0]["id"]

        response = client.get(f"/api/orders/{first_id}")
        assert response.status_code == 200

        order = response.json()
        assert order["id"] == first_id

    def test_get_nonexistent_order_returns_404(self, client):
        """Test that a missing order ID returns 404 with detail message."""
        response = client.get("/api/orders/nonexistent-order-xyz-999")
        assert response.status_code == 404

        body = response.json()
        assert "detail" in body
        assert "not found" in body["detail"].lower()

    # ── Warehouse filter ─────────────────────────────────────────────────────

    def test_filter_by_warehouse_san_francisco(self, client):
        """Test filtering orders to San Francisco warehouse only."""
        response = client.get("/api/orders?warehouse=San Francisco")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["warehouse"] == "San Francisco"

    def test_filter_by_warehouse_london(self, client):
        """Test filtering orders to London warehouse only."""
        response = client.get("/api/orders?warehouse=London")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["warehouse"] == "London"

    def test_filter_by_warehouse_tokyo(self, client):
        """Test filtering orders to Tokyo warehouse only."""
        response = client.get("/api/orders?warehouse=Tokyo")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["warehouse"] == "Tokyo"

    def test_warehouse_filter_excludes_other_warehouses(self, client):
        """Test that a warehouse filter returns no orders from other warehouses."""
        response = client.get("/api/orders?warehouse=London")
        data = response.json()

        warehouses_in_result = {order["warehouse"] for order in data}
        assert warehouses_in_result == {"London"}, \
            f"Expected only London, got: {warehouses_in_result}"

    def test_unknown_warehouse_returns_empty_list(self, client):
        """Test that a non-existent warehouse returns an empty list, not an error."""
        response = client.get("/api/orders?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    # ── Status filter ────────────────────────────────────────────────────────

    def test_filter_by_status_delivered(self, client):
        """Test filtering to Delivered orders only."""
        response = client.get("/api/orders?status=Delivered")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "delivered"

    def test_filter_by_status_processing(self, client):
        """Test filtering to Processing orders only."""
        response = client.get("/api/orders?status=Processing")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "processing"

    def test_filter_by_status_backordered(self, client):
        """Test filtering to Backordered orders only."""
        response = client.get("/api/orders?status=Backordered")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "backordered"

    def test_filter_by_status_shipped(self, client):
        """Test filtering to Shipped orders only."""
        response = client.get("/api/orders?status=Shipped")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert order["status"].lower() == "shipped"

    def test_unknown_status_returns_empty_list(self, client):
        """Test that an invalid status value returns an empty list."""
        response = client.get("/api/orders?status=Teleported")
        assert response.status_code == 200
        assert response.json() == []

    # ── Month / quarter filter ───────────────────────────────────────────────

    def test_filter_by_month(self, client):
        """Test filtering orders by a specific YYYY-MM month."""
        response = client.get("/api/orders?month=2025-03")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            assert "2025-03" in order["order_date"], \
                f"Order {order['order_number']} not in March 2025: {order['order_date']}"

    def test_filter_by_quarter_q1(self, client):
        """Test filtering orders with Q1-2025 quarter format."""
        response = client.get("/api/orders?month=Q1-2025")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for order in data:
            month_prefix = order["order_date"][:7]  # YYYY-MM
            assert month_prefix in {"2025-01", "2025-02", "2025-03"}, \
                f"Q1 order has unexpected month: {month_prefix}"

    def test_filter_by_quarter_q2(self, client):
        """Test Q2-2025 returns only April–June orders."""
        data = client.get("/api/orders?month=Q2-2025").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"][:7] in {"2025-04", "2025-05", "2025-06"}

    def test_filter_by_quarter_q3(self, client):
        """Test Q3-2025 returns only July–September orders."""
        data = client.get("/api/orders?month=Q3-2025").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"][:7] in {"2025-07", "2025-08", "2025-09"}

    def test_filter_by_quarter_q4(self, client):
        """Test Q4-2025 returns only October–December orders."""
        data = client.get("/api/orders?month=Q4-2025").json()
        assert len(data) > 0
        for order in data:
            assert order["order_date"][:7] in {"2025-10", "2025-11", "2025-12"}

    def test_each_quarter_returns_fewer_than_full_list(self, client):
        """Test that each quarter filter narrows the result relative to all orders."""
        total = len(client.get("/api/orders").json())
        for quarter in ("Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"):
            count = len(client.get(f"/api/orders?month={quarter}").json())
            assert 0 < count < total, \
                f"{quarter} returned {count} orders (total={total})"

    # ── Combined filters ─────────────────────────────────────────────────────

    def test_filter_warehouse_and_status(self, client):
        """Test combining warehouse and status filters."""
        response = client.get("/api/orders?warehouse=Tokyo&status=Delivered")
        assert response.status_code == 200

        data = response.json()
        for order in data:
            assert order["warehouse"] == "Tokyo"
            assert order["status"].lower() == "delivered"

    def test_filter_warehouse_and_month(self, client):
        """Test combining warehouse and month filters."""
        response = client.get("/api/orders?warehouse=London&month=2025-06")
        assert response.status_code == 200

        data = response.json()
        for order in data:
            assert order["warehouse"] == "London"
            assert "2025-06" in order["order_date"]

    def test_filter_all_params(self, client):
        """Test all four filters combined still returns a valid response."""
        response = client.get(
            "/api/orders?warehouse=San Francisco&category=Circuit Boards"
            "&status=Delivered&month=Q2-2025"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_all_filter_value_equals_no_filter(self, client):
        """Test that warehouse=all returns the same result as omitting the param."""
        resp_all = client.get("/api/orders?warehouse=all&status=all&month=all")
        resp_none = client.get("/api/orders")

        assert resp_all.status_code == 200
        assert len(resp_all.json()) == len(resp_none.json())

    # ── Cross-endpoint consistency ───────────────────────────────────────────

    def test_pending_orders_match_dashboard(self, client):
        """Test that pending order count matches the dashboard summary."""
        all_orders = client.get("/api/orders").json()
        pending_count = sum(
            1 for o in all_orders
            if o["status"].lower() in {"processing", "backordered"}
        )

        dashboard = client.get("/api/dashboard/summary").json()
        assert dashboard["pending_orders"] == pending_count

    def test_total_orders_split_by_warehouse(self, client):
        """Test that per-warehouse order counts sum to the full order count."""
        total = len(client.get("/api/orders").json())
        sf = len(client.get("/api/orders?warehouse=San Francisco").json())
        lon = len(client.get("/api/orders?warehouse=London").json())
        tok = len(client.get("/api/orders?warehouse=Tokyo").json())
        assert sf + lon + tok == total
