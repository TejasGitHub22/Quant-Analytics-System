import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

def hedge_ratio(x, y):
    return np.cov(x, y)[0,1] / np.var(x)

def compute_spread(df1, df2):
    # Align the two dataframes on their index (timestamp)
    # This ensures they have the same length and matching timestamps
    aligned = pd.DataFrame({
        'price1': df1["price"],
        'price2': df2["price"]
    }).dropna()  # Remove rows where either price is missing
    
    if len(aligned) < 2:
        # Not enough data points for hedge ratio calculation
        return pd.Series(dtype=float), 0.0
    
    # Extract aligned price series
    price1 = aligned["price1"].values
    price2 = aligned["price2"].values
    
    # Compute hedge ratio
    beta = hedge_ratio(price1, price2)
    
    # Compute spread on aligned data
    spread_values = price2 - beta * price1
    spread = pd.Series(spread_values, index=aligned.index)
    
    return spread, beta

def zscore(series, window=30):
    mean = series.rolling(window).mean()
    std = series.rolling(window).std()
    return (series - mean) / std

def rolling_corr(df1, df2, window=30):
    # Align the two dataframes on their index
    aligned = pd.DataFrame({
        'price1': df1["price"],
        'price2': df2["price"]
    }).dropna()
    
    if len(aligned) < window:
        return pd.Series(dtype=float, index=aligned.index)
    
    return aligned["price1"].rolling(window).corr(aligned["price2"])

def adf_test(series):
    cleaned = series.dropna()
    if len(cleaned) < 10:  # Need minimum data points for ADF test
        return {
            "adf_stat": None,
            "p_value": None,
            "error": "Insufficient data points for ADF test (need at least 10)"
        }
    try:
        result = adfuller(cleaned)
        return {
            "adf_stat": result[0],
            "p_value": result[1]
        }
    except (ValueError, IndexError) as e:
        return {
            "adf_stat": None,
            "p_value": None,
            "error": f"ADF test failed: {str(e)}"
        }

