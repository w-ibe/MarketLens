from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm_summary import generate_market_summary, get_latest_metrics


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
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "marketlens_features.csv"


# ------------------------------------------------------------
# Shared chart styling
# ------------------------------------------------------------
CHART_COLORWAY = ["#1F4E79", "#5B7083", "#C08A2E", "#2E7D4F", "#B23B3B"]


def style_chart(fig: go.Figure, title: str) -> go.Figure:
    """Apply a consistent, restrained visual style to a chart."""
    fig.update_layout(
        title=title,
        template="simple_white",
        colorway=CHART_COLORWAY,
        height=420,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        font=dict(size=13),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB")
    return fig


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

    style_chart(fig, "SPY Close Price with Moving Averages")
    fig.update_layout(xaxis_title="Date", yaxis_title="Price")

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

    style_chart(fig, "SPY Cumulative Return vs DGS10 10-Year Treasury Yield")
    fig.update_layout(
        xaxis_title="Date",
        yaxis=dict(title="SPY Cumulative Return"),
        yaxis2=dict(
            title="DGS10 Yield",
            overlaying="y",
            side="right",
        ),
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
        "LLM Market Summary",
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
st.title(page)

st.caption(
    "Educational and portfolio demonstration only. "
    "This dashboard does not prove that any trading or investment strategy is profitable."
)

st.divider()


# ------------------------------------------------------------
# Latest metrics
# ------------------------------------------------------------
latest = filtered_data.dropna(subset=["close"]).iloc[-1]


# ------------------------------------------------------------
# Page: Market Overview
# ------------------------------------------------------------
if page == "Market Overview":
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            label="Latest Close",
            value=format_number(latest["close"]),
            delta=format_percent(latest["daily_return"]),
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

    with st.container(border=True):
        st.plotly_chart(make_price_chart(filtered_data), use_container_width=True)


# ------------------------------------------------------------
# Page: Price and Trend Charts
# ------------------------------------------------------------
elif page == "Price and Trend Charts":
    with st.container(border=True):
        st.plotly_chart(make_price_chart(filtered_data), use_container_width=True)

    with st.container(border=True):
        cumulative_return_chart = px.line(
            filtered_data,
            x="date",
            y="cumulative_return",
        )
        style_chart(cumulative_return_chart, "SPY Cumulative Return")
        cumulative_return_chart.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
        )

        st.plotly_chart(cumulative_return_chart, use_container_width=True)


# ------------------------------------------------------------
# Page: Risk Metrics
# ------------------------------------------------------------
elif page == "Risk Metrics":
    with st.container(border=True):
        drawdown_chart = px.line(
            filtered_data,
            x="date",
            y="drawdown",
        )
        style_chart(drawdown_chart, "SPY Drawdown")
        drawdown_chart.update_layout(xaxis_title="Date", yaxis_title="Drawdown")

        st.plotly_chart(drawdown_chart, use_container_width=True)

    risk_col1, risk_col2 = st.columns(2)

    with risk_col1:
        with st.container(border=True):
            volatility_chart = px.line(
                filtered_data,
                x="date",
                y="rolling_volatility_20",
            )
            style_chart(volatility_chart, "SPY 20-Day Rolling Volatility")
            volatility_chart.update_layout(
                xaxis_title="Date",
                yaxis_title="Annualized Volatility",
            )

            st.plotly_chart(volatility_chart, use_container_width=True)

    with risk_col2:
        with st.container(border=True):
            rsi_chart = go.Figure()

            rsi_chart.add_trace(
                go.Scatter(
                    x=filtered_data["date"],
                    y=filtered_data["rsi_14"],
                    mode="lines",
                    name="RSI 14",
                )
            )

            rsi_chart.add_hrect(
                y0=70, y1=100,
                fillcolor="#B23B3B", opacity=0.08, line_width=0,
            )
            rsi_chart.add_hrect(
                y0=0, y1=30,
                fillcolor="#2E7D4F", opacity=0.08, line_width=0,
            )
            rsi_chart.add_hline(y=70, line_dash="dash", annotation_text="70")
            rsi_chart.add_hline(y=30, line_dash="dash", annotation_text="30")

            style_chart(rsi_chart, "SPY RSI 14")
            rsi_chart.update_layout(xaxis_title="Date", yaxis_title="RSI")

            st.plotly_chart(rsi_chart, use_container_width=True)


# ------------------------------------------------------------
# Page: Macro Comparison
# ------------------------------------------------------------
elif page == "Macro Comparison":
    with st.container(border=True):
        st.plotly_chart(
            make_macro_comparison_chart(filtered_data),
            use_container_width=True,
        )

    with st.container(border=True):
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
# Page: LLM Market Summary
# ------------------------------------------------------------
elif page == "LLM Market Summary":
    st.caption(
        "This page summarizes calculated dashboard metrics only. "
        "It does not generate forecasts, recommendations, or trading advice."
    )

    with st.container(border=True):
        latest_metrics = get_latest_metrics(filtered_data)

        st.subheader("Metrics Sent to Summary Tool")
        st.json(latest_metrics)

        use_llm = st.checkbox(
            "Use LLM API if available",
            value=False,
            help="Leave unchecked to use deterministic fallback mode. Check only if API quota is available "
            "for the configured provider (OpenAI by default, or NVIDIA if LLM_PROVIDER=nvidia).",
        )

        if st.button("Generate Market Summary"):
            try:
                summary_text, summary_mode = generate_market_summary(
                    latest_metrics,
                    use_llm=use_llm,
                )

                st.subheader("Summary Output")
                st.write(summary_text)

                st.info(f"Summary mode: {summary_mode}")

            except Exception as error:
                st.error("Market summary could not be generated.")
                st.exception(error)

# ------------------------------------------------------------
# Page: Data Table
# ------------------------------------------------------------
elif page == "Data Table":
    with st.container(border=True):
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