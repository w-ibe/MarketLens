from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="MarketLens",
    page_icon="📊",
    layout="wide",
)


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "marketlens_features.csv"


# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    """Load the processed MarketLens feature dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    df = pd.read_csv(path)

    required_columns = [
        "date",
        "close",
        "daily_return",
        "cumulative_return",
        "moving_average_20",
        "moving_average_50",
        "rolling_volatility_20",
        "rsi_14",
        "drawdown",
        "trend_status",
        "dgs10",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "daily_return",
        "cumulative_return",
        "moving_average_20",
        "moving_average_50",
        "rolling_volatility_20",
        "rsi_14",
        "drawdown",
        "dgs10",
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "close"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def format_percent(value: float) -> str:
    """Format decimal values as percentages."""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.2f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Format numeric values."""
    if pd.isna(value):
        return "N/A"
    return f"{value:,.{decimals}f}"


def make_price_chart(df: pd.DataFrame) -> go.Figure:
    """Create price and moving average chart."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="SPY Close",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["moving_average_20"],
            mode="lines",
            name="20-Day Moving Average",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["moving_average_50"],
            mode="lines",
            name="50-Day Moving Average",
        )
    )

    fig.update_layout(
        title="SPY Close Price with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price",
        height=500,
    )

    return fig


def make_macro_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Create cumulative return and DGS10 comparison chart."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["cumulative_return"],
            mode="lines",
            name="SPY Cumulative Return",
            yaxis="y1",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["dgs10"],
            mode="lines",
            name="DGS10",
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="SPY Cumulative Return vs DGS10 10-Year Treasury Yield",
        xaxis_title="Date",
        yaxis=dict(title="SPY Cumulative Return"),
        yaxis2=dict(
            title="DGS10 Yield",
            overlaying="y",
            side="right",
        ),
        height=500,
    )

    return fig


# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
try:
    data = load_data(DATA_PATH)
except Exception as error:
    st.error("Dashboard data could not be loaded.")
    st.exception(error)
    st.stop()


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
st.sidebar.title("MarketLens")
st.sidebar.caption("Financial Market Intelligence Dashboard")

page = st.sidebar.radio(
    "Select page",
    [
        "Market Overview",
        "Price and Trend Charts",
        "Risk Metrics",
        "Macro Comparison",
        "Data Table",
    ],
)

min_date = data["date"].min().date()
max_date = data["date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_data = data[
        (data["date"].dt.date >= start_date)
        & (data["date"].dt.date <= end_date)
    ].copy()
else:
    filtered_data = data.copy()

if filtered_data.empty:
    st.warning("No data available for the selected date range.")
    st.stop()


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.title("MarketLens")
st.subheader("Financial Market Intelligence Dashboard")

st.caption(
    "Educational and portfolio demonstration only. "
    "This dashboard does not prove that any trading or investment strategy is profitable."
)


# ------------------------------------------------------------
# Latest metrics
# ------------------------------------------------------------
latest = filtered_data.dropna(subset=["close"]).iloc[-1]


# ------------------------------------------------------------
# Page: Market Overview
# ------------------------------------------------------------
if page == "Market Overview":
    st.header("Market Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label="Latest Close",
        value=format_number(latest["close"]),
    )

    col2.metric(
        label="Latest Daily Return",
        value=format_percent(latest["daily_return"]),
    )

    col3.metric(
        label="Cumulative Return",
        value=format_percent(latest["cumulative_return"]),
    )

    col4.metric(
        label="DGS10",
        value=format_number(latest["dgs10"]),
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        label="20-Day Volatility",
        value=format_percent(latest["rolling_volatility_20"]),
    )

    col6.metric(
        label="RSI 14",
        value=format_number(latest["rsi_14"]),
    )

    col7.metric(
        label="Drawdown",
        value=format_percent(latest["drawdown"]),
    )

    col8.metric(
        label="Trend Status",
        value=str(latest["trend_status"]),
    )

    st.plotly_chart(make_price_chart(filtered_data), use_container_width=True)


# ------------------------------------------------------------
# Page: Price and Trend Charts
# ------------------------------------------------------------
elif page == "Price and Trend Charts":
    st.header("Price and Trend Charts")

    st.plotly_chart(make_price_chart(filtered_data), use_container_width=True)

    cumulative_return_chart = px.line(
        filtered_data,
        x="date",
        y="cumulative_return",
        title="SPY Cumulative Return",
    )

    cumulative_return_chart.update_layout(
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        height=500,
    )

    st.plotly_chart(cumulative_return_chart, use_container_width=True)


# ------------------------------------------------------------
# Page: Risk Metrics
# ------------------------------------------------------------
elif page == "Risk Metrics":
    st.header("Risk Metrics")

    drawdown_chart = px.line(
        filtered_data,
        x="date",
        y="drawdown",
        title="SPY Drawdown",
    )

    drawdown_chart.update_layout(
        xaxis_title="Date",
        yaxis_title="Drawdown",
        height=500,
    )

    st.plotly_chart(drawdown_chart, use_container_width=True)

    volatility_chart = px.line(
        filtered_data,
        x="date",
        y="rolling_volatility_20",
        title="SPY 20-Day Rolling Volatility",
    )

    volatility_chart.update_layout(
        xaxis_title="Date",
        yaxis_title="Annualized Volatility",
        height=500,
    )

    st.plotly_chart(volatility_chart, use_container_width=True)

    rsi_chart = go.Figure()

    rsi_chart.add_trace(
        go.Scatter(
            x=filtered_data["date"],
            y=filtered_data["rsi_14"],
            mode="lines",
            name="RSI 14",
        )
    )

    rsi_chart.add_hline(y=70, line_dash="dash", annotation_text="70")
    rsi_chart.add_hline(y=30, line_dash="dash", annotation_text="30")

    rsi_chart.update_layout(
        title="SPY RSI 14",
        xaxis_title="Date",
        yaxis_title="RSI",
        height=500,
    )

    st.plotly_chart(rsi_chart, use_container_width=True)


# ------------------------------------------------------------
# Page: Macro Comparison
# ------------------------------------------------------------
elif page == "Macro Comparison":
    st.header("Macro Comparison")

    st.plotly_chart(
        make_macro_comparison_chart(filtered_data),
        use_container_width=True,
    )

    corr_cols = [
        "daily_return",
        "rolling_volatility_20",
        "rsi_14",
        "drawdown",
        "dgs10",
    ]

    available_corr_cols = [col for col in corr_cols if col in filtered_data.columns]

    correlation_table = filtered_data[available_corr_cols].corr().round(3)

    st.subheader("Correlation Table")
    st.dataframe(correlation_table, use_container_width=True)

    st.caption(
        "The correlation table is descriptive only. "
        "It does not establish causation or prove predictive power."
    )


# ------------------------------------------------------------
# Page: Data Table
# ------------------------------------------------------------
elif page == "Data Table":
    st.header("Data Table")

    st.write("Filtered dataset preview:")

    st.dataframe(
        filtered_data.sort_values("date", ascending=False),
        use_container_width=True,
    )

    st.download_button(
        label="Download filtered data as CSV",
        data=filtered_data.to_csv(index=False),
        file_name="marketlens_filtered_data.csv",
        mime="text/csv",
    )