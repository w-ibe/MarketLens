from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def clean_spy_data(spy: pd.DataFrame) -> pd.DataFrame:
    """Clean raw SPY price data."""
    spy_clean = spy.copy()

    spy_clean.columns = [str(col).lower().replace(" ", "_") for col in spy_clean.columns]

    if "date" not in spy_clean.columns:
        raise ValueError("SPY data must contain a date column.")

    spy_clean["date"] = pd.to_datetime(spy_clean["date"], errors="coerce")
    spy_clean = spy_clean.dropna(subset=["date"])
    spy_clean = spy_clean.sort_values("date").reset_index(drop=True)

    numeric_cols = ["open", "high", "low", "close", "adj_close", "volume"]

    for col in numeric_cols:
        if col in spy_clean.columns:
            spy_clean[col] = pd.to_numeric(spy_clean[col], errors="coerce")

    keep_cols = [
        col
        for col in ["date", "open", "high", "low", "close", "adj_close", "volume"]
        if col in spy_clean.columns
    ]

    spy_clean = spy_clean[keep_cols]

    if "close" not in spy_clean.columns:
        raise ValueError("SPY data must contain a close column.")

    spy_clean = spy_clean.dropna(subset=["close"])

    return spy_clean


def clean_dgs10_data(dgs10: pd.DataFrame) -> pd.DataFrame:
    """Clean raw DGS10 data."""
    dgs10_clean = dgs10.copy()

    dgs10_clean.columns = [str(col).lower().replace(" ", "_") for col in dgs10_clean.columns]

    if "date" not in dgs10_clean.columns:
        raise ValueError("DGS10 data must contain a date column.")

    if "dgs10" not in dgs10_clean.columns:
        raise ValueError("DGS10 data must contain a dgs10 column.")

    dgs10_clean["date"] = pd.to_datetime(dgs10_clean["date"], errors="coerce")
    dgs10_clean["dgs10"] = pd.to_numeric(dgs10_clean["dgs10"], errors="coerce")

    dgs10_clean = dgs10_clean.dropna(subset=["date"])
    dgs10_clean = dgs10_clean.sort_values("date").reset_index(drop=True)

    return dgs10_clean


def merge_market_macro_data(spy_clean: pd.DataFrame, dgs10_clean: pd.DataFrame) -> pd.DataFrame:
    """Merge SPY market data with DGS10 macro data."""
    marketlens = pd.merge(
        spy_clean,
        dgs10_clean,
        on="date",
        how="left",
    )

    marketlens["dgs10"] = marketlens["dgs10"].ffill()

    marketlens = marketlens.dropna(subset=["close"])
    marketlens = marketlens.sort_values("date").reset_index(drop=True)

    duplicate_dates = marketlens["date"].duplicated().sum()

    if duplicate_dates > 0:
        marketlens = marketlens.drop_duplicates(subset=["date"], keep="last")

    return marketlens


def main() -> None:
    """Run clean and merge workflow."""
    spy_path = RAW_DIR / "spy_prices.csv"
    dgs10_path = RAW_DIR / "dgs10_yield.csv"

    if not spy_path.exists():
        raise FileNotFoundError(f"Missing file: {spy_path}")

    if not dgs10_path.exists():
        raise FileNotFoundError(f"Missing file: {dgs10_path}")

    spy = pd.read_csv(spy_path)
    dgs10 = pd.read_csv(dgs10_path)

    spy_clean = clean_spy_data(spy)
    dgs10_clean = clean_dgs10_data(dgs10)

    marketlens = merge_market_macro_data(spy_clean, dgs10_clean)

    output_path = PROCESSED_DIR / "marketlens_dataset.csv"
    marketlens.to_csv(output_path, index=False)

    print(f"Processed dataset saved to: {output_path}")
    print(f"Rows: {len(marketlens)}")
    print(f"Columns: {marketlens.columns.tolist()}")
    print(f"Duplicate dates: {marketlens['date'].duplicated().sum()}")
    print("Missing values:")
    print(marketlens.isna().sum())


if __name__ == "__main__":
    main()