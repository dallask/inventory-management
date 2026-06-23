"""
Tests for reports API endpoints (/api/reports/quarterly and /api/reports/monthly-trends).
"""
import pytest


class TestQuarterlyReports:
    """Test suite for the /api/reports/quarterly endpoint."""

    # ── Structure ────────────────────────────────────────────────────────────

    def test_get_quarterly_report(self, client):
        """Test that the quarterly report returns a non-empty list."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_quarterly_required_fields(self, client):
        """Test that each quarterly entry has all required fields."""
        data = client.get("/api/reports/quarterly").json()

        required = [
            "quarter", "total_orders", "total_revenue",
            "delivered_orders", "avg_order_value", "fulfillment_rate",
        ]
        for entry in data:
            for field in required:
                assert field in entry, f"Quarterly entry missing field: {field}"

    def test_quarterly_data_types(self, client):
        """Test that quarterly report fields have correct data types."""
        data = client.get("/api/reports/quarterly").json()

        for entry in data:
            assert isinstance(entry["quarter"], str)
            assert isinstance(entry["total_orders"], int)
            assert isinstance(entry["total_revenue"], (int, float))
            assert isinstance(entry["delivered_orders"], int)
            assert isinstance(entry["avg_order_value"], (int, float))
            assert isinstance(entry["fulfillment_rate"], (int, float))

    # ── Business logic ───────────────────────────────────────────────────────

    def test_quarterly_all_four_quarters_present(self, client):
        """Test that all four 2025 quarters appear in the report."""
        data = client.get("/api/reports/quarterly").json()
        quarters = {entry["quarter"] for entry in data}

        for q in {"Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"}:
            assert q in quarters, f"Missing quarter: {q}"

    def test_quarterly_sorted_ascending(self, client):
        """Test that quarters are returned in chronological order."""
        data = client.get("/api/reports/quarterly").json()
        quarters = [entry["quarter"] for entry in data]
        assert quarters == sorted(quarters), f"Quarters not sorted: {quarters}"

    def test_quarterly_revenue_positive(self, client):
        """Test that every quarter has positive total revenue."""
        data = client.get("/api/reports/quarterly").json()
        for entry in data:
            assert entry["total_revenue"] > 0, \
                f"{entry['quarter']} has non-positive revenue: {entry['total_revenue']}"

    def test_quarterly_delivered_lte_total(self, client):
        """Test that delivered_orders never exceeds total_orders."""
        data = client.get("/api/reports/quarterly").json()
        for entry in data:
            assert entry["delivered_orders"] <= entry["total_orders"], (
                f"{entry['quarter']}: delivered={entry['delivered_orders']} "
                f"> total={entry['total_orders']}"
            )

    def test_quarterly_avg_order_value_calculation(self, client):
        """Test that avg_order_value = total_revenue / total_orders."""
        data = client.get("/api/reports/quarterly").json()
        for entry in data:
            expected_avg = entry["total_revenue"] / entry["total_orders"]
            assert abs(entry["avg_order_value"] - expected_avg) < 0.02, (
                f"{entry['quarter']}: avg={entry['avg_order_value']}, "
                f"expected={expected_avg:.2f}"
            )

    def test_quarterly_fulfillment_rate_range(self, client):
        """Test that fulfillment_rate is between 0 and 100."""
        data = client.get("/api/reports/quarterly").json()
        for entry in data:
            assert 0 <= entry["fulfillment_rate"] <= 100, \
                f"{entry['quarter']} fulfillment_rate out of range: {entry['fulfillment_rate']}"

    def test_quarterly_fulfillment_rate_calculation(self, client):
        """Test fulfillment_rate = (delivered_orders / total_orders) * 100."""
        data = client.get("/api/reports/quarterly").json()
        for entry in data:
            expected = (entry["delivered_orders"] / entry["total_orders"]) * 100
            assert abs(entry["fulfillment_rate"] - expected) < 0.2, (
                f"{entry['quarter']}: rate={entry['fulfillment_rate']}, "
                f"expected={expected:.1f}"
            )

    def test_quarterly_quarter_label_format(self, client):
        """Test that quarter labels follow the Q[1-4]-YYYY format."""
        import re
        data = client.get("/api/reports/quarterly").json()
        pattern = re.compile(r"^Q[1-4]-\d{4}$")
        for entry in data:
            assert pattern.match(entry["quarter"]), \
                f"Unexpected quarter format: {entry['quarter']}"

    def test_quarterly_cross_validates_with_orders(self, client):
        """Test that Q1 total_orders matches raw order count for Q1-2025."""
        all_orders = client.get("/api/orders?month=Q1-2025").json()
        quarterly = client.get("/api/reports/quarterly").json()

        q1 = next((e for e in quarterly if e["quarter"] == "Q1-2025"), None)
        assert q1 is not None, "Q1-2025 not in quarterly report"
        assert q1["total_orders"] == len(all_orders), (
            f"Q1 total_orders={q1['total_orders']}, raw count={len(all_orders)}"
        )

    # ── Filters ──────────────────────────────────────────────────────────────

    def test_quarterly_warehouse_filter(self, client):
        """Test that warehouse filter reduces total order counts."""
        all_data = client.get("/api/reports/quarterly").json()
        sf_data = client.get("/api/reports/quarterly?warehouse=San Francisco").json()

        all_total = sum(e["total_orders"] for e in all_data)
        sf_total = sum(e["total_orders"] for e in sf_data)
        assert sf_total < all_total, "Warehouse filter should reduce order count"
        assert sf_total > 0

    def test_quarterly_category_filter(self, client):
        """Test that category filter returns a valid report."""
        response = client.get("/api/reports/quarterly?category=Sensors")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_quarterly_unknown_warehouse_returns_empty(self, client):
        """Test that an unknown warehouse filter returns an empty list."""
        response = client.get("/api/reports/quarterly?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []


class TestMonthlyTrends:
    """Test suite for the /api/reports/monthly-trends endpoint."""

    # ── Structure ────────────────────────────────────────────────────────────

    def test_get_monthly_trends(self, client):
        """Test that monthly-trends returns a non-empty list."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_monthly_trends_required_fields(self, client):
        """Test that each monthly entry has all required fields."""
        data = client.get("/api/reports/monthly-trends").json()

        required = ["month", "order_count", "revenue", "delivered_count"]
        for entry in data:
            for field in required:
                assert field in entry, f"Monthly entry missing field: {field}"

    def test_monthly_trends_data_types(self, client):
        """Test that monthly-trends fields have correct data types."""
        data = client.get("/api/reports/monthly-trends").json()

        for entry in data:
            assert isinstance(entry["month"], str)
            assert isinstance(entry["order_count"], int)
            assert isinstance(entry["revenue"], (int, float))
            assert isinstance(entry["delivered_count"], int)

    # ── Business logic ───────────────────────────────────────────────────────

    def test_monthly_trends_12_months_present(self, client):
        """Test that all 12 months of 2025 appear in the report."""
        data = client.get("/api/reports/monthly-trends").json()
        months_in_report = {entry["month"] for entry in data}

        expected = {f"2025-{m:02d}" for m in range(1, 13)}
        assert expected == months_in_report, \
            f"Missing months: {expected - months_in_report}"

    def test_monthly_trends_sorted_chronologically(self, client):
        """Test that months are returned in chronological order."""
        data = client.get("/api/reports/monthly-trends").json()
        months = [entry["month"] for entry in data]
        assert months == sorted(months), f"Months not sorted: {months}"

    def test_monthly_trends_revenue_positive(self, client):
        """Test that every month has positive revenue."""
        data = client.get("/api/reports/monthly-trends").json()
        for entry in data:
            assert entry["revenue"] > 0, \
                f"{entry['month']} has non-positive revenue: {entry['revenue']}"

    def test_monthly_trends_delivered_lte_order_count(self, client):
        """Test that delivered_count never exceeds order_count."""
        data = client.get("/api/reports/monthly-trends").json()
        for entry in data:
            assert entry["delivered_count"] <= entry["order_count"], (
                f"{entry['month']}: delivered={entry['delivered_count']} "
                f"> orders={entry['order_count']}"
            )

    def test_monthly_trends_order_count_positive(self, client):
        """Test that every month has at least one order."""
        data = client.get("/api/reports/monthly-trends").json()
        for entry in data:
            assert entry["order_count"] > 0, \
                f"{entry['month']} has zero orders"

    def test_monthly_month_label_format(self, client):
        """Test that month labels are in YYYY-MM format."""
        import re
        data = client.get("/api/reports/monthly-trends").json()
        pattern = re.compile(r"^\d{4}-\d{2}$")
        for entry in data:
            assert pattern.match(entry["month"]), \
                f"Unexpected month format: {entry['month']}"

    def test_monthly_cross_validates_with_orders(self, client):
        """Test that March 2025 order_count matches raw orders for that month."""
        raw_march = client.get("/api/orders?month=2025-03").json()
        trends = client.get("/api/reports/monthly-trends").json()

        march = next((e for e in trends if e["month"] == "2025-03"), None)
        assert march is not None, "2025-03 not found in monthly trends"
        assert march["order_count"] == len(raw_march), (
            f"monthly trend count={march['order_count']}, raw={len(raw_march)}"
        )

    def test_total_orders_across_months_matches_full_list(self, client):
        """Test that summing order_count across all months equals total orders."""
        trends = client.get("/api/reports/monthly-trends").json()
        total_from_trends = sum(e["order_count"] for e in trends)

        all_orders = client.get("/api/orders").json()
        assert total_from_trends == len(all_orders), (
            f"Trend sum={total_from_trends}, actual total={len(all_orders)}"
        )

    # ── Filters ──────────────────────────────────────────────────────────────

    def test_monthly_trends_warehouse_filter(self, client):
        """Test that warehouse filter reduces total order counts."""
        all_data = client.get("/api/reports/monthly-trends").json()
        tok_data = client.get("/api/reports/monthly-trends?warehouse=Tokyo").json()

        all_total = sum(e["order_count"] for e in all_data)
        tok_total = sum(e["order_count"] for e in tok_data)
        assert tok_total < all_total
        assert tok_total > 0

    def test_monthly_trends_category_filter(self, client):
        """Test that category filter returns a valid, reduced dataset."""
        response = client.get("/api/reports/monthly-trends?category=Circuit Boards")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        total = sum(e["order_count"] for e in data)
        assert total > 0

    def test_monthly_trends_unknown_warehouse_returns_empty(self, client):
        """Test that a non-existent warehouse returns an empty list."""
        response = client.get("/api/reports/monthly-trends?warehouse=Atlantis")
        assert response.status_code == 200
        assert response.json() == []
