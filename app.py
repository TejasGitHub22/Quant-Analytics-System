import streamlit as st
import threading
import time
from datetime import datetime
import pandas as pd
from backend.ingest import start_ws, ticks
from backend.storage import get_df, resample
from backend.analytics import compute_spread, zscore, rolling_corr, adf_test
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("Quant Analytics Dashboard")
st.caption("Real-time Binance Futures Monitoring")

# Sidebar controls
st.sidebar.header("User Controls")

# 2.1 Symbol Selection
st.sidebar.subheader("Symbol Selection")
symbols = st.sidebar.multiselect(
    "Select Trading Pairs",
    ["btcusdt", "ethusdt"],
    default=["btcusdt", "ethusdt"],
    help="Select multiple products to analyze"
)

# 2.2 Timeframe Selector
st.sidebar.subheader("Timeframe Selector")
timeframe = st.sidebar.selectbox(
    "Resampling Timeframe",
    ["1s", "1m", "5m"],
    help="Controls backend aggregation logic"
)

# 2.3 Rolling Window Selector
st.sidebar.subheader("Rolling Window Selector")
window = st.sidebar.slider(
    "Rolling Window",
    10, 100, 30,
    help="Controls z-score and correlation calculations"
)

# 2.4 Alert Threshold
st.sidebar.subheader("Alert Threshold")
alert_threshold = st.sidebar.slider(
    "Z-score Alert Threshold",
    1.0, 3.0, 2.0,
    step=0.1,
    help="Threshold for triggering alerts"
)

# 2.5 Start / Stop Stream
st.sidebar.subheader("Stream Control")
if "streaming" not in st.session_state:
    st.session_state.streaming = False

col_start, col_stop = st.sidebar.columns(2)

with col_start:
    if st.button("Start Stream", use_container_width=True):
        if symbols:
            threading.Thread(target=start_ws, args=(symbols,), daemon=True).start()
            st.session_state.streaming = True
            st.success("Streaming started")
        else:
            st.warning("Please select at least one symbol")

with col_stop:
    if st.button("Stop Stream", use_container_width=True):
        st.session_state.streaming = False
        st.info("Stream stopped")

if st.session_state.streaming:
    st.sidebar.success("🟢 Streaming Active")
else:
    st.sidebar.info("⚪ Stream Inactive")

# OHLC Data Upload (Optional)
st.sidebar.divider()
st.sidebar.subheader("OHLC Data Upload (Optional)")
uploaded_file = st.sidebar.file_uploader(
    "Upload OHLC CSV File",
    type=['csv'],
    help="Optional: Upload historical OHLC data. App works without this."
)

if uploaded_file is not None:
    try:
        ohlc_df = pd.read_csv(uploaded_file)
        # Validate required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close']
        if all(col in ohlc_df.columns for col in required_cols):
            st.sidebar.success(f"✅ OHLC data loaded: {len(ohlc_df)} rows")
            if 'ohlc_data' not in st.session_state:
                st.session_state.ohlc_data = ohlc_df
            else:
                st.session_state.ohlc_data = pd.concat([st.session_state.ohlc_data, ohlc_df])
        else:
            st.sidebar.error("❌ CSV must contain: timestamp, open, high, low, close")
    except Exception as e:
        st.sidebar.error(f"Error loading file: {str(e)}")

time.sleep(2)

df = get_df()

# Main Dashboard - Visual Analytics
st.header("Main Dashboard")

if df.empty:
    st.info("No data available. Please start the stream and wait for data collection.")
elif len(symbols) < 2:
    st.warning("Please select exactly 2 symbols to view analytics.")
else:
    df1 = resample(df[df.symbol == symbols[0]], timeframe)
    df2 = resample(df[df.symbol == symbols[1]], timeframe)

    if df1.empty or df2.empty:
        st.info("Waiting for data... Please ensure the stream is active.")
    else:
        spread, beta = compute_spread(df1, df2)
        
        # 3.1 Price Chart (MANDATORY)
        st.subheader("3.1 Price Chart")
        fig_prices = go.Figure()
        fig_prices.add_trace(go.Scatter(
            x=df1.index,
            y=df1["price"],
            name=symbols[0].upper(),
            line=dict(color='#1f77b4', width=2)
        ))
        fig_prices.add_trace(go.Scatter(
            x=df2.index,
            y=df2["price"],
            name=symbols[1].upper(),
            line=dict(color='#ff7f0e', width=2)
        ))
        fig_prices.update_layout(
            title="Price Comparison - Both Symbols",
            xaxis_title="Time",
            yaxis_title="Price (USDT)",
            hovermode='x unified',
            height=400
        )
        st.plotly_chart(fig_prices, use_container_width=True)

        if spread.empty or len(spread) < 2:
            st.info("Waiting for more data to align both symbols... Need at least 2 overlapping data points.")
        else:
            z = zscore(spread, window)
            corr = rolling_corr(df1, df2, window)

            # 3.2 Spread + Z-score Chart (MANDATORY)
            st.subheader("3.2 Spread & Z-score Chart")
            fig_spread = go.Figure()
            
            # Add Spread trace
            fig_spread.add_trace(go.Scatter(
                x=spread.index,
                y=spread,
                name="Spread",
                line=dict(color='#2ca02c', width=2),
                yaxis='y'
            ))
            
            # Add Z-score trace with secondary y-axis
            fig_spread.add_trace(go.Scatter(
                x=z.index,
                y=z,
                name="Z-score",
                line=dict(color='#d62728', width=2, dash='dash'),
                yaxis='y2'
            ))
            
            fig_spread.update_layout(
                title="Spread Trading Analysis",
                xaxis_title="Time",
                yaxis=dict(title="Spread", side='left', color='#2ca02c'),
                yaxis2=dict(title="Z-score", side='right', overlaying='y', color='#d62728'),
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig_spread, use_container_width=True)

            # 3.3 Rolling Correlation Plot (MANDATORY)
            st.subheader("3.3 Rolling Correlation Plot")
            fig_corr = go.Figure()
            fig_corr.add_trace(go.Scatter(
                x=corr.index,
                y=corr,
                name="Rolling Correlation",
                line=dict(color='#9467bd', width=2),
                fill='tozeroy',
                fillcolor='rgba(148, 103, 189, 0.2)'
            ))
            fig_corr.update_layout(
                title="Correlation vs Time",
                xaxis_title="Time",
                yaxis_title="Correlation",
                yaxis=dict(range=[-1, 1]),
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            # 4. Numerical Analytics Panel (VERY IMPORTANT)
            st.subheader("4. Numerical Analytics Panel")
            st.caption("Real-time computed metrics for trading decisions")
            
            # Calculate spread statistics
            spread_mean = spread.mean() if not spread.empty else 0.0
            spread_std = spread.std() if not spread.empty else 0.0
            
            # Get latest values safely
            latest_z = z.iloc[-1] if not z.empty and not pd.isna(z.iloc[-1]) else 0.0
            latest_corr = corr.iloc[-1] if not corr.empty and not pd.isna(corr.iloc[-1]) else 0.0
            
            # Metrics row
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Hedge Ratio (β)", f"{beta:.4f}" if not pd.isna(beta) else "N/A")
            
            with col2:
                st.metric("Latest Z-score", f"{latest_z:.2f}" if not pd.isna(latest_z) else "N/A")
            
            with col3:
                st.metric("Latest Correlation", f"{latest_corr:.4f}" if not pd.isna(latest_corr) else "N/A")
            
            with col4:
                st.metric("Spread Mean", f"{spread_mean:.4f}" if not pd.isna(spread_mean) else "N/A")
            
            with col5:
                st.metric("Spread Std Dev", f"{spread_std:.4f}" if not pd.isna(spread_std) else "N/A")
            
            # 5. ADF Test Output (MANDATORY)
            st.subheader("5. ADF Test Result")
            st.caption("Augmented Dickey-Fuller Test for Spread Stationarity")
            
            adf_result = adf_test(spread)
            
            # Check if ADF test was successful
            if adf_result.get("error") or adf_result.get("adf_stat") is None:
                st.warning(f"⚠️ **ADF Test Unavailable**: {adf_result.get('error', 'Insufficient data for ADF test')}")
                st.info("Please wait for more data to be collected (minimum 10 data points required)")
            else:
                # Display ADF results in a structured format
                col_adf1, col_adf2 = st.columns(2)
                
                with col_adf1:
                    st.metric("ADF Statistic", f"{adf_result['adf_stat']:.4f}")
                
                with col_adf2:
                    st.metric("p-value", f"{adf_result['p_value']:.4f}")
                
                # Interpretation
                st.divider()
                if adf_result["p_value"] < 0.05:
                    st.success("✓ **Stationary**: Spread is stationary (p < 0.05) - Suitable for mean reversion trading")
                else:
                    st.warning("⚠ **Non-Stationary**: Spread may not be stationary (p >= 0.05) - Mean reversion may not be reliable")
            
            # Raw JSON output for reference
            with st.expander("View Raw ADF Test Data"):
                st.json(adf_result)

            # 6. Alert Section (MANDATORY)
            st.divider()
            st.subheader("6. Alert Section")
            
            if pd.isna(latest_z):
                st.info("⏳ Waiting for sufficient data to calculate Z-score...")
            else:
                abs_z = abs(latest_z)
                if abs_z > alert_threshold:
                    st.error(f"⚠️ **Z-Score Alert Triggered**\n\n"
                            f"Current Z-score: {latest_z:.2f} | Threshold: {alert_threshold}\n"
                            f"Absolute value: {abs_z:.2f} exceeds threshold")
                else:
                    st.success(f"✓ Z-score within normal range: {latest_z:.2f} (Threshold: {alert_threshold})")

            # 7. Data Export (MANDATORY)
            st.divider()
            st.subheader("7. Data Export")
            
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                # Prepare resampled data for export
                resampled_data = pd.DataFrame({
                    'timestamp': df1.index,
                    f'{symbols[0]}_price': df1['price'].values,
                    f'{symbols[1]}_price': df2['price'].values,
                    'spread': spread.values,
                    'z_score': z.values,
                    'correlation': corr.values
                })
                csv_resampled = resampled_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Resampled CSV",
                    data=csv_resampled,
                    file_name=f"resampled_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col_export2:
                # Prepare analytics data for export
                adf_stat = adf_result.get('adf_stat', 'N/A')
                adf_pval = adf_result.get('p_value', 'N/A')
                analytics_data = pd.DataFrame({
                    'metric': ['Hedge Ratio (β)', 'Latest Z-score', 'Latest Correlation', 
                              'Spread Mean', 'Spread Std Dev', 'ADF Statistic', 'ADF p-value'],
                    'value': [
                        beta if not pd.isna(beta) else 'N/A',
                        latest_z if not pd.isna(latest_z) else 'N/A',
                        latest_corr if not pd.isna(latest_corr) else 'N/A',
                        spread_mean if not pd.isna(spread_mean) else 'N/A',
                        spread_std if not pd.isna(spread_std) else 'N/A',
                        adf_stat if adf_stat is not None else 'N/A',
                        adf_pval if adf_pval is not None else 'N/A'
                    ]
                })
                csv_analytics = analytics_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download Analytics CSV",
                    data=csv_analytics,
                    file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            # 8. Status / Footer (GOOD UX)
            st.divider()
            st.subheader("8. System Status")
            
            # Get status information
            tick_count = len(ticks)
            last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            col_status1, col_status2, col_status3 = st.columns(3)
            
            with col_status1:
                if st.session_state.get('streaming', False):
                    st.success("🟢 **Streaming Status:** Active")
                else:
                    st.info("⚪ **Streaming Status:** Inactive")
            
            with col_status2:
                st.metric("Ticks Received", f"{tick_count:,}")
            
            with col_status3:
                st.metric("Last Update", last_update)
            
            # Footer
            st.caption(f"Quant Analytics Dashboard | Data Source: Binance Futures | Last refreshed: {last_update}")

