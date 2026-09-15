import pandas as pd
class DataQualityEngine:
    def __init__(self, max_ret=0.50, min_ret=-0.50):
        self.max_ret = max_ret
        self.min_ret = min_ret
    def validate_dataset(self, df: pd.DataFrame):
        results = {
            'row_count_ok': len(df) > 0,
            'columns_ok': {'timestamp', 'price', 'return'}.issubset(df.columns),
            'price_greater_than_zero': (df['price'] > 0).all() if 'price' in df.columns else False,
            'no_nulls': df.notnull().all().all()
        }
        if 'return' in df.columns:
            results['returns_within_bounds'] = df['return'].between(self.min_ret, self.max_ret).all()
        return results
