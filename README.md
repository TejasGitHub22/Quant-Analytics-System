## Quant Developer Evaluation Assignment

### Overview
This application ingests real-time Binance Futures tick data via WebSocket, resamples it, computes quantitative analytics, and visualizes results live. The application starts aggregating and storing data immediately, with analytics features enabled progressively as sufficient data becomes available.

### Stack
- Backend: Python, WebSockets, Pandas
- Frontend: Streamlit + Plotly
- Analytics: OLS hedge ratio, spread, z-score, ADF test, rolling correlation

### Features
- **Real-time Data Ingestion**: WebSocket connection to Binance Futures for live trade ticks
- **Progressive Analytics**: Features enable automatically as required data points become available
- **Data Resampling**: 1s / 1m / 5m timeframes
- **Quantitative Analytics**:
  - Hedge ratio (β) calculation
  - Spread computation
  - Rolling z-score for mean reversion
  - Rolling correlation analysis
  - ADF test for stationarity (requires minimum 10 data points)
- **Real-time Alerts**: Z-score threshold alerts
- **Interactive Charts**: Price comparison, spread analysis, correlation plots
- **Data Export**: Download resampled data and analytics as CSV
- **OHLC Upload** (Optional): Upload historical OHLC data (app works without this)

### Key Requirements Met
✅ Works entirely with real-time data (no dummy data required)  
✅ Progressive feature enablement based on data availability  
✅ All analytics work with less than a day of data  
✅ Optional OHLC upload functionality  
✅ Real-time alerting system  
✅ Data aggregation and resampling  

### Run
```bash
pip install -r requirements.txt  
streamlit run app.py
```

### Usage
1. Select trading pairs (e.g., BTC/USDT, ETH/USDT)
2. Click "Start Stream" to begin real-time data collection
3. Wait 10-30 seconds for initial data
4. Analytics appear progressively as data becomes available
5. (Optional) Upload OHLC CSV file for additional analysis

### AI Usage Transparency
See [CHATGPT_USAGE.md](CHATGPT_USAGE.md) for detailed information about ChatGPT and Cursor usage during development.

### Architecture Diagram
The architecture diagram is available in `architecture.drawio`. To view it:
1. Open `architecture.drawio` in [draw.io](https://app.diagrams.net/)
2. Export as PNG to create `architecture.png` (optional)

