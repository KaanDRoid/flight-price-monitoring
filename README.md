# ✈️ Flight Price Monitoring with Time-Series Analysis

This project implements a comprehensive flight price monitoring system that tracks pricing changes across multiple Online Travel Agencies (OTAs) over time.

## 📊 Project Overview

This system fetches flight prices from multiple routes and OTAs, creating daily snapshots for time-series analysis of pricing patterns and competitive dynamics.

## 🏗️ System Architecture

### Data Collection Pipeline
- **Primary Script**: `fetch_prices.py` - Fetches current flight prices
- **Snapshot System**: Daily data collection with timestamp-based file naming
- **Routes Monitored**: 10 international routes across 4 continents

### Analysis Components
1. **Static Analysis**: Current pricing patterns (`flight_analysis_duckdb.ipynb`)
2. **Time Series Analysis**: Daily price change monitoring (`price_comparison_analysis.py`)
3. **Competitive Intelligence**: OTA pricing strategy insights

## 📁 File Structure

```
├── fetch_prices.py              # Main data collection script
├── price_comparison_analysis.py  # Daily comparison analysis
├── flight_analysis_duckdb.ipynb # Static analysis notebook
├── snapshots/                   # Daily snapshot storage
│   ├── 20250618/               # First snapshot (baseline)
│   │   ├── all_routes.csv
│   │   └── route_breakdown/
│   └── 20250619/               # Second snapshot
│       ├── all_routes.csv
│       └── route_breakdown/
└── analysis_results/           # Generated insights and visualizations
```

## 💾 Data Management

The system now uses a clean, organized file structure:

- **Snapshot System**: All flight data is stored in timestamped snapshot directories (`snapshots/YYYYMMDD/`)
- **No Duplicates**: CSV files are saved only in their respective snapshot directories, avoiding clutter in the main project folder
- **Organized Storage**: Each snapshot contains:
  - `all_routes.csv`: Combined data from all routes
  - `route_breakdown/`: Individual CSV files for each route
  - `snapshot_summary.json`: Metadata and summary statistics
- **Clean Workspace**: The main project directory contains only code files and configuration

## 🔄 Daily Monitoring Workflow

1. **00:00 UTC**: Automated data collection via `fetch_prices.py`
2. **Data Storage**: Timestamped snapshots in organized directories
3. **Comparison Analysis**: Price change detection and competitive analysis
4. **Insights Generation**: Automated reports on pricing trends

## 📈 Key Metrics Tracked

- **Price Volatility**: Daily price changes by route and OTA
- **Competitive Positioning**: Market share and pricing strategies
- **Seasonal Trends**: Long-term pricing patterns
- **Route Performance**: Most/least competitive routes

## 🎯 Business Value

- **Market Intelligence**: Real time competitive pricing insights
- **Dynamic Pricing**: Data driven pricing strategy recommendations
- **Customer Value**: Optimal booking timing recommendations
- **Trend Analysis**: Seasonal and market pattern identification

## 🚀 Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env`
4. Run initial snapshot: `python fetch_prices.py`
5. Schedule daily runs for continuous monitoring

## 📊 Analysis Examples

### Daily Price Changes
```python
# Compare today vs yesterday (It can be extend of course)
python price_comparison_analysis.py --date1 20250618 --date2 20250619
```

### Competitive Analysis
```python
# Analyze OTA pricing strategies
python price_comparison_analysis.py --mode ota_analysis
```

## 🎯 Project Goals

- Monitor market conditions and competitive pricing shifts
- Identify optimal booking windows for different routes
- Track OTA pricing strategies and market positioning
- Provide actionable insights for pricing decisions
