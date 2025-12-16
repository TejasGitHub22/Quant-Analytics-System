import pandas as pd
from backend.ingest import ticks

def get_df():
    if not ticks:
        return pd.DataFrame()
    
    # Make a copy of the ticks list to avoid race conditions
    # The WebSocket thread might be modifying ticks while we read it
    # Using list slice for fast shallow copy
    try:
        ticks_copy = ticks[:]  # Fast shallow copy
    except:
        return pd.DataFrame()
    
    if not ticks_copy:
        return pd.DataFrame()
    
    # Ensure all dictionaries have the same keys to avoid length mismatch
    # Filter out any incomplete entries
    required_keys = {"timestamp", "symbol", "price", "qty"}
    valid_ticks = [
        tick for tick in ticks_copy 
        if isinstance(tick, dict) and required_keys.issubset(tick.keys())
    ]
    
    if not valid_ticks:
        return pd.DataFrame()
    
    # Create DataFrame with explicit column order
    try:
        df = pd.DataFrame(valid_ticks, columns=["timestamp", "symbol", "price", "qty"])
        return df
    except (ValueError, KeyError) as e:
        # Fallback: create DataFrame row by row if there are still issues
        rows = []
        for tick in valid_ticks:
            try:
                rows.append({
                    "timestamp": tick.get("timestamp"),
                    "symbol": tick.get("symbol"),
                    "price": float(tick.get("price", 0)),
                    "qty": float(tick.get("qty", 0))
                })
            except (ValueError, TypeError):
                continue
        
        if rows:
            return pd.DataFrame(rows)
        return pd.DataFrame()

def resample(df, timeframe):
    if df.empty:
        return df

    df = df.set_index("timestamp")

    rule = {
        "1s": "1S",
        "1m": "1T",
        "5m": "5T"
    }[timeframe]

    return df.resample(rule).agg({
        "price": "last",
        "qty": "sum"
    }).dropna()

