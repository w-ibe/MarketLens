from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI, RateLimitError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "marketlens_features.csv"


def load_marketlens_features(path: Path = FEATURES_PATH) -> pd.DataFrame:
    """Load the MarketLens feature dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {path}")

    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    return df


def get_latest_metrics(df: pd.DataFrame) -> dict:
    """Extract latest dashboard metrics from the feature dataset."""
    latest = df.iloc[-1]

    return {
        "latest_date": str(latest["date"].date()),
        "latest_close": round(float(latest["close"]), 2),
        "latest_daily_return_percent": round(float(latest["daily_return"]) * 100, 2),
        "latest_cumulative_return_percent": round(float(latest["cumulative_return"]) * 100, 2),
        "latest_rolling_volatility_20_percent": round(float(latest["rolling_volatility_20"]) * 100, 2),
        "latest_rsi_14": round(float(latest["rsi_14"]), 2),
        "latest_drawdown_percent": round(float(latest["drawdown"]) * 100, 2),
        "latest_dgs10": round(float(latest["dgs10"]), 2),
        "latest_trend_status": str(latest["trend_status"]),
    }


def build_market_summary_prompt(metrics: dict) -> str:
    """Build a controlled prompt using only calculated metrics."""
    return f"""
You are generating a portfolio-project dashboard summary.

Use only the metrics provided below.
Do not invent causes, forecasts, recommendations, or trading advice.
Do not claim that the data proves profitability.
Use clear plain English.

Metrics:
- Latest date: {metrics["latest_date"]}
- Latest SPY close: {metrics["latest_close"]}
- Latest daily return: {metrics["latest_daily_return_percent"]}%
- Cumulative return from dataset start: {metrics["latest_cumulative_return_percent"]}%
- 20-day annualized rolling volatility: {metrics["latest_rolling_volatility_20_percent"]}%
- RSI 14: {metrics["latest_rsi_14"]}
- Current drawdown: {metrics["latest_drawdown_percent"]}%
- DGS10 10-Year Treasury yield: {metrics["latest_dgs10"]}
- Trend status: {metrics["latest_trend_status"]}

Write 4 short bullet points:
1. Price and trend
2. Return and drawdown
3. Volatility and RSI
4. Macro note from DGS10

End with this exact sentence:
This summary is descriptive only and is not investment advice.
""".strip()


def generate_fallback_summary(metrics: dict) -> str:
    """Generate a deterministic fallback summary from calculated metrics."""
    return f"""
- Price and trend: On {metrics["latest_date"]}, SPY closed at {metrics["latest_close"]}. The trend status is {metrics["latest_trend_status"]}.
- Return and drawdown: The latest daily return is {metrics["latest_daily_return_percent"]}%. The cumulative return from the dataset start is {metrics["latest_cumulative_return_percent"]}%, and the current drawdown is {metrics["latest_drawdown_percent"]}%.
- Volatility and RSI: The 20-day annualized rolling volatility is {metrics["latest_rolling_volatility_20_percent"]}%. The RSI 14 value is {metrics["latest_rsi_14"]}.
- Macro note from DGS10: The DGS10 10-Year Treasury yield value in the dataset is {metrics["latest_dgs10"]}.

This summary is descriptive only and is not investment advice.
""".strip()


def generate_market_summary(metrics: dict, use_llm: bool = True) -> tuple[str, str]:
    """
    Generate a market summary.

    Returns:
        tuple[str, str]: summary text and summary mode.
    """
    load_dotenv()

    if not use_llm:
        return generate_fallback_summary(metrics), "fallback_manual"

    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()

    if provider == "nvidia":
        api_key = os.getenv("NVIDIA_API_KEY")
        model = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
        base_url = "https://integrate.api.nvidia.com/v1"
        placeholder = "PASTE_YOUR_NVIDIA_KEY_HERE"
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-5.5")
        base_url = None
        placeholder = "PASTE_YOUR_OPENAI_KEY_HERE"

    if not api_key or api_key == placeholder:
        return generate_fallback_summary(metrics), "fallback_missing_api_key"

    try:
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        prompt = build_market_summary_prompt(metrics)

        if provider == "nvidia":
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content, "nvidia_api"

        response = client.responses.create(
            model=model,
            input=prompt,
        )

        return response.output_text, "openai_api"

    except RateLimitError:
        return generate_fallback_summary(metrics), "fallback_insufficient_quota"

    except AuthenticationError:
        return generate_fallback_summary(metrics), "fallback_authentication_error"

    except APIError:
        return generate_fallback_summary(metrics), "fallback_api_error"


if __name__ == "__main__":
    data = load_marketlens_features()
    latest_metrics = get_latest_metrics(data)
    summary, mode = generate_market_summary(latest_metrics)

    print(f"Summary mode: {mode}\n")
    print(summary)