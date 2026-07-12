# MarketLens

MarketLens is a financial market intelligence dashboard built as a recruiter-ready portfolio project.

It collects market and macroeconomic data from APIs, cleans and merges the data in Python, calculates financial indicators, visualizes the results in a Streamlit dashboard, and includes an LLM-ready market summary workflow with deterministic fallback mode.

## Live Project Links

- Live dashboard: https://marketlens-financial-dashboard.streamlit.app/
- GitHub repository: https://github.com/w-ibe/MarketLens

## What This Project Demonstrates

| Requirement | How MarketLens Demonstrates It |
|---|---|
| A script that cleans, merges, or analyzes data | Python scripts fetch, clean, merge, and analyze SPY and DGS10 data |
| A dashboard or data visualization | Streamlit dashboard with interactive Plotly charts |
| A simple website or web page | Public Streamlit web dashboard |
| A workflow that connects two tools | GitHub Actions runs the Python data pipeline automatically |
| Something that uses an API | FRED API and yfinance data access |
| A chatbot or tool that uses another LLM | LLM-ready market summary module with fallback mode |
| Something else | Financial feature engineering, risk metrics, and automation workflow |

## Project Overview

MarketLens analyzes SPY market data together with the DGS10 10-Year Treasury yield.

The dashboard includes:

- Market overview metrics
- Price and moving average charts
- Cumulative return chart
- Drawdown chart
- Rolling volatility chart
- RSI chart
- Macro comparison with DGS10
- Correlation table
- LLM-ready market summary page
- Downloadable filtered data table

## Current Verified Status

Completed and verified:

- Local Jupyter development workflow
- API data collection
- Data cleaning and merging
- Feature engineering
- Streamlit dashboard
- GitHub repository publishing
- GitHub Actions automation
- Streamlit public deployment
- Fallback market summary mode

Current limitation:

- Live OpenAI API summary generation is blocked by account quota.
- The dashboard uses a deterministic fallback summary mode when OpenAI API quota is unavailable.

## Tech Stack

- Python
- pandas
- NumPy
- yfinance
- FRED API
- Plotly
- Streamlit
- python-dotenv
- OpenAI Python SDK
- GitHub Actions
- GitHub

## Project Structure

```text
MarketLens/
├── .github/
│   └── workflows/
│       └── update_data.yml
├── dashboard/
│   └── app.py
├── data/
│   └── processed/
│       ├── marketlens_dataset.csv
│       └── marketlens_features.csv
├── notebooks/
├── reports/
├── src/
│   ├── fetch_data.py
│   ├── clean_data.py
│   ├── analyze_data.py
│   ├── llm_summary.py
│   └── utils.py
├── website/
├── .gitignore
├── README.md
└── requirements.txt
```

## Data Pipeline

```text
API data collection
        ↓
Raw market and macro data
        ↓
Data cleaning and merging
        ↓
Feature engineering
        ↓
Processed dashboard dataset
        ↓
Streamlit dashboard
        ↓
Automated refresh through GitHub Actions
```

## Data Sources

MarketLens uses:

- SPY market data through yfinance
- DGS10 10-Year Treasury yield from FRED

Raw data files are not committed to the repository.

Processed dashboard-ready files are committed because the deployed Streamlit app reads them directly.

## Features Created

The feature dataset includes:

- Daily return
- Cumulative return
- 20-day moving average
- 50-day moving average
- 20-day annualized rolling volatility
- RSI 14
- Running maximum close
- Drawdown
- Trend status
- DGS10 10-Year Treasury yield

## Dashboard Pages

### Market Overview

Shows latest SPY close, daily return, cumulative return, DGS10, volatility, RSI, drawdown, and trend status.

### Price and Trend Charts

Shows SPY close price, 20-day moving average, 50-day moving average, and cumulative return.

### Risk Metrics

Shows drawdown, rolling volatility, and RSI 14.

### Macro Comparison

Shows SPY cumulative return vs DGS10 and a correlation table.

### LLM Market Summary

Shows calculated metrics and a controlled summary output.

The summary feature is designed to avoid unsupported claims, forecasts, trading recommendations, or profitability claims.

### Data Table

Shows the filtered dataset and a CSV download button.

## Automation

The GitHub Actions workflow is located at:

```text
.github/workflows/update_data.yml
```

It can:

- Run manually
- Run weekly
- Install dependencies
- Fetch updated data
- Clean and merge data
- Rebuild features
- Commit updated processed data if changes exist

Required GitHub repository secret:

```text
FRED_API_KEY
```

## How to Run Locally

Clone the repository:

```powershell
git clone https://github.com/w-ibe/MarketLens.git
cd MarketLens
```

Create and activate the environment:

```powershell
conda create -n marketlens python=3.11 -y
conda activate marketlens
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a local `.env` file:

```text
FRED_API_KEY=your_fred_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

By default the LLM summary page uses OpenAI. To use an NVIDIA-hosted model instead (e.g. if OpenAI quota is unavailable), set:

```text
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=your_nvidia_api_key_here
NVIDIA_MODEL=meta/llama-3.1-8b-instruct
```

`NVIDIA_MODEL` is optional and defaults to `meta/llama-3.1-8b-instruct`. If `LLM_PROVIDER` is unset or set to `openai`, `OPENAI_API_KEY`/`OPENAI_MODEL` are used as before.

Run the data pipeline:

```powershell
python src/fetch_data.py
python src/clean_data.py
python src/analyze_data.py
```

Run the dashboard:

```powershell
streamlit run dashboard/app.py
```

## Recruiter Summary

MarketLens is a financial data intelligence dashboard that demonstrates end-to-end data product development. It uses Python to collect financial and macroeconomic data from APIs, cleans and merges the data, calculates financial indicators, visualizes insights in a Streamlit dashboard, includes an LLM-ready market summary workflow, and automates data updates with GitHub Actions.

## Disclaimer

This project is for educational and portfolio demonstration only.

It does not prove that any trading or investment strategy is profitable.

It does not provide investment advice, financial advice, or trading recommendations.