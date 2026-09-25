from backend.algorithms import ALGORITHMS
from backend.evaluation import daily_recommendation, metric_bundle
from backend.main import app
from backend.providers import MockMarketDataProvider
from src.data_quality import distribution_report, validate_synthetic_data
from src.generators import generate_scenario


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


def test_distribution_report_accepts_matching_distributions():
    scenario = generate_scenario("Sideways", n_observations=250, seed=11)
    report = distribution_report(scenario["Return"], scenario["Return"])
    assert report["reference_data_available"] is True
    assert report["ks_test_passed"] is True
    assert report["wasserstein_distance"] == 0.0


def test_validation_uses_supplied_reference_without_network():
    scenario = generate_scenario("Sideways", n_observations=100, seed=12)
    report = validate_synthetic_data(
        scenario,
        reference_returns=scenario["Return"],
    )
    assert report["reference_data_available"] is True
    assert report["ks_test_passed"] is True
    assert report["wasserstein_within_bounds"] is True


def test_metric_bundle_exposes_quantstats_metrics():
    scenario = generate_scenario("Bullish", n_observations=250, seed=13)
    metrics = metric_bundle(scenario["Return"])
    assert {"sharpe", "sortino", "cvar_95"}.issubset(metrics)
    assert all(isinstance(metrics[key], float) for key in ("sharpe", "sortino", "cvar_95"))


def test_daily_recommendation_thresholds():
    assert daily_recommendation({"max_drawdown": -0.15, "cvar_95": -0.01}) == "STOP"
    assert daily_recommendation({"max_drawdown": -0.05, "cvar_95": -0.03}) == "RETRAIN"
    assert daily_recommendation({"max_drawdown": -0.05, "cvar_95": -0.01}) == "CONTINUE"
