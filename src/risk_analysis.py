import numpy as np
def calculate_var(returns_series, confidence=0.95):
    return np.percentile(returns_series, (1 - confidence) * 100) if len(returns_series) > 0 else 0.0
def calculate_drawdown(prices):
    rolling_max = prices.cummax()
    return ((prices - rolling_max) / rolling_max).min() if len(prices) > 0 else 0.0
