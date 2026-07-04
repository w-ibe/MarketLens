from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"

RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_spy_from_yfinance(start_date: str = "2018-01-01") -> pd.DataFrame:
    """Fetch SPY price data from Yahoo Finance through yfinance."""
    ticker = "SPY"

    spy = yf.download(
        ticker,
        start=start_date,
        progress=False,
        auto_adjust=False,
    )

    if spy.empty:
        raise ValueError("No SPY data returned from yfinance.")

    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)

    spy = spy.reset_index()
    spy.columns = [str(col).lower().replace(" ", "_") for col in spy.columns]

    required_cols = ["date", "open", "high", "low", "close", "adj_close", "volume"]
    available_cols = [col for col in required_cols if col in spy.columns]

    spy = spy[available_cols]

    return spy


def fetch_spy_from_stooq(start_date: str = "2018-01-01") -> pd.DataFrame:
    """Fetch SPY price data from Stooq as a fallback."""
    stooq_url = "https://stooq.com/q/d/l/?s=spy.us&i=d"

    spy = pd.read_csv(stooq_url)

    if spy.empty:
        raise ValueError("No SPY data returned from Stooq.")

    spy.columns = [str(col).lower().replace(" ", "_") for col in spy.columns]
    spy["date"] = pd.to_datetime(spy["date"], errors="coerce")
    spy = spy.dropna(subset=["date"])
    spy = spy[spy["date"] >= pd.to_datetime(start_date)]

    return spy


def fetch_spy_prices(start_date: str = "2018-01-01") -> pd.DataFrame:
    """Fetch SPY price data, using Stooq fallback if yfinance fails."""
    try:
        spy = fetch_spy_from_yfinance(start_date=start_date)
        source = "yfinance"
    except Exception as yfinance_error:
        print("yfinance failed. Trying Stooq fallback.")
        print(f"yfinance error: {yfinance_error}")

        spy = fetch_spy_from_stooq(start_date=start_date)
        source = "stooq"

    output_path = RAW_DIR / "spy_prices.csv"
    spy.to_csv(output_path, index=False)

    print(f"SPY source: {source}")
    print(f"Saved SPY data to: {output_path}")
    print(f"SPY rows: {len(spy)}")

    return spy


def fetch_dgs10_from_fred(start_date: str = "2018-01-01") -> pd.DataFrame:
    """Fetch DGS10 10-Year Treasury yield data from FRED."""
    load_dotenv()

    fred_key = os.getenv("FRED_API_KEY")

    if not fred_key or fred_key == "PASTE_YOUR_FRED_KEY_HERE":
        raise ValueError("FRED_API_KEY is missing. Add it to .env before running this script.")

    params = {
        "series_id": "DGS10",
        "api_key": fred_key,
        "file_type": "json",
        "observation_start": start_date,
    }

    url = "https://api.stlouisfed.org/fred/series/observations"

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if "observations" not in data:
        raise ValueError("FRED response does not contain observations.")

    dgs10 = pd.DataFrame(data["observations"])

    if dgs10.empty:
        raise ValueError("No DGS10 data returned from FRED.")

    dgs10 = dgs10[["date", "value"]].copy()
    dgs10["date"] = pd.to_datetime(dgs10["date"], errors="coerce")
    dgs10["value"] = pd.to_numeric(dgs10["value"], errors="coerce")
    dgs10 = dgs10.rename(columns={"value": "dgs10"})

    output_path = RAW_DIR / "dgs10_yield.csv"
    dgs10.to_csv(output_path, index=False)

    print(f"Saved DGS10 data to: {output_path}")
    print(f"DGS10 rows: {len(dgs10)}")

    return dgs10


def main() -> None:
    """Run raw data collection."""
    start_date = "2018-01-01"

    fetch_spy_prices(start_date=start_date)
    fetch_dgs10_from_fred(start_date=start_date)

    print("Data fetch completed.")


if __name__ == "__main__":
    main()