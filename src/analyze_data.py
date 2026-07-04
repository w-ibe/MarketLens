from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def add_return_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add daily and cumulative return features."""
    df = df.copy()

    df["daily_return"] = df["close"].pct_change()
    df["cumulative_return"] = (1 + df["daily_return"].fillna(0)).cumprod() - 1

    return df


def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Add 20-day and 50-day moving averages."""
    df = df.copy()

    df["moving_average_20"] = df["close"].rolling(window=20).mean()
    df["moving_average_50"] = df["close"].rolling(window=50).mean()

    return df


def add_rolling_volatility(df: pd.DataFrame) -> pd.DataFrame:
    """Add 20-day annualized rolling volatility."""
    df = df.copy()

    trading_days_per_year = 252

    df["rolling_volatility_20"] = (
        df["daily_return"]
        .rolling(window=20)
        .std()
        * np.sqrt(trading_days_per_year)
    )

    return df


def add_rsi(df: pd.DataFrame, rsi_period: int = 14) -> pd.DataFrame:
    """Add simple 14-period RSI calculation."""
    df = df.copy()

    price_change = df["close"].diff()

    gain = price_change.clip(lower=0)
    loss = -price_change.clip(upper=0)

    avg_gain = gain.rolling(window=rsi_period).mean()
    avg_loss = loss.rolling(window=rsi_period).mean()

    rs = avg_gain / avg_loss

    df["rsi_14"] = 100 - (100 / (1 + rs))

    return df


def add_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    """Add running maximum close and drawdown."""
    df = df.copy()

    df["running_max_close"] = df["close"].cummax()
    df["drawdown"] = (df["close"] / df["running_max_close"]) - 1

    return df


def add_trend_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add trend status based on the 50-day moving average."""
    df = df.copy()

    conditions = [
        df["close"] > df["moving_average_50"],
        df["close"] < df["moving_average_50"],
    ]

    choices = [
        "Above 50-day average",
        "Below 50-day average",
    ]

    df["trend_status"] = np.select(
        conditions,
        choices,
        default="Insufficient data",
    )

    return df


def create_feature_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create the full MarketLens feature dataset."""
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")

    df = df.dropna(subset=["date", "close"])
    df = df.sort_values("date").reset_index(drop=True)

    df = add_return_features(df)
    df = add_moving_averages(df)
    df = add_rolling_volatility(df)
    df = add_rsi(df)
    df = add_drawdown(df)
    df = add_trend_status(df)

    return df


def main() -> None:
    """Run financial feature engineering workflow."""
    input_path = PROCESSED_DIR / "marketlens_dataset.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Missing file: {input_path}")

    df = pd.read_csv(input_path)

    features = create_feature_dataset(df)

    output_path = PROCESSED_DIR / "marketlens_features.csv"
    features.to_csv(output_path, index=False)

    print(f"Feature dataset saved to: {output_path}")
    print(f"Rows: {len(features)}")
    print(f"Columns: {features.columns.tolist()}")
    print("Missing values:")
    print(features.isna().sum())


if __name__ == "__main__":
    main()