from backend.algorithms import ALGORITHMS
from backend.main import app
from backend.providers import MockMarketDataProvider


def test_mock_provider_is_deterministic_and_labelled():
    a = MockMarketDataProvider(seed=7).latest(bars=20)
    b = MockMarketDataProvider(seed=7).latest(bars=20)
    assert a.equals(b)
    assert set(a["source"]) == {"MOCK"}
    assert not a["is_synthetic"].any()


def test_algorithms_share_interface():
    data = MockMarketDataProvider(seed=7).latest(bars=50)
    for algorithm in ALGORITHMS:
        signals, returns = algorithm.evaluate(data)
        assert len(signals) == len(data)
        assert len(returns) == len(data)
        assert algorithm.metadata["demo_only"] is True


def test_health_endpoint_has_orders_disabled():
    from fastapi.testclient import TestClient
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["orders_enabled"] is False


def test_no_order_endpoint():
    from fastapi.testclient import TestClient
    response = TestClient(app).post("/api/orders")
    assert response.status_code == 404
