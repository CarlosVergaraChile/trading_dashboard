import pandas as pd
import yaml
def load_settings():
    try:
        with open("config/settings.yaml", "r") as f: return yaml.safe_load(f)
    except: return {"volatility_thresholds": {"max_return": 0.5, "min_return": -0.5}}
def load_trades(): return pd.read_csv("data/trades.csv")
def load_algorithms(): return pd.read_csv("data/algorithms.csv")
