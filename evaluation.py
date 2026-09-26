@dataclass(frozen=True)
class CostModel:
    commission_bps: float = 5.0
    slippage_bps: float = 2.0
    spread_bps: float = 1.0

def turnover(signal: pd.Series) -> pd.Series:
    pos = signal.shift(1).fillna(0)          # posición ejecutada
    return pos.diff().abs().fillna(pos.abs()).fillna(0.0)

def apply_costs(strategy_returns, signal, costs=DEFAULT_COSTS):
    return strategy_returns - turnover(signal) * costs.rate_per_trade