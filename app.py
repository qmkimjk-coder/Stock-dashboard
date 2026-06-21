import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="주식 투자 대시보드",
    layout="wide"
)

st.title("📈 주식 투자 대시보드")

WATCHLIST = {
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "KT": "030200.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "현대차": "005380.KS",
    "SOXL": "SOXL",
    "NVDA": "NVDA",
    "PLTR": "PLTR"
}


def calc_rsi(close, period=14):

    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1/period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1/period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi


def get_signal(
    close,
    ma20,
    ma60,
    rsi,
    signal,
    volume,
    avg_volume
):

    if (
        rsi > signal
        and close > ma20
        and ma20 > ma60
        and volume > avg_volume
    ):
        return "🟢 강매수"

    elif (
        rsi > signal
        and close > ma20
    ):
        return "🟡 매수관심"

    elif (
        rsi < signal
        and close < ma20
        and ma20 < ma60
        and volume > avg_volume
    ):
        return "⚫ 강매도"

    elif (
        rsi < signal
        and close < ma20
    ):
        return "🔴 매도주의"

    return "🟠 관망"


# --------------------------
# 전체 종목 현황판
# --------------------------

st.subheader("📋 전체 종목 현황판")

summary = []

for stock_name, ticker in WATCHLIST.items():

    try:

        df = yf.download(
            ticker,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if len(df) < 100:
            continue

        close = df["Close"]
        volume = df["Volume"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        if isinstance(volume, pd.DataFrame):
            volume = volume.iloc[:, 0]

        ma20 = close.rolling(20).mean()
        ma60 = close.rolling(60).mean()

        rsi = calc_rsi(close)
        signal = rsi.rolling(6).mean()

        avg_volume = volume.rolling(20).mean()

        status = get_signal(
            close.iloc[-1],
            ma20.iloc[-1],
            ma60.iloc[-1],
            rsi.iloc[-1],
            signal.iloc[-1],
            volume.iloc[-1],
            avg_volume.iloc[-1]
        )

        summary.append({
            "종목": stock_name,
            "상태": status,
            "RSI": round(rsi.iloc[-1], 1)
        })

    except:
        pass

summary_df = pd.DataFrame(summary)

st.dataframe(
    summary_df,
    use_container_width=True
)

st.divider()

# --------------------------
# 상세 분석
# --------------------------

name = st.selectbox(
    "종목 선택",
    list(WATCHLIST.keys())
)

ticker = WATCHLIST[name]

period = st.selectbox(
    "조회 기간",
    ["6mo", "1y", "2y", "5y"],
    index=1
)

data = yf.download(
    ticker,
    period=period,
    auto_adjust=True,
    progress=False
)

close = data["Close"]
volume = data["Volume"]

if isinstance(close, pd.DataFrame):
    close = close.iloc[:, 0]

if isinstance(volume, pd.DataFrame):
    volume = volume.iloc[:, 0]

ma20 = close.rolling(20).mean()
ma60 = close.rolling(60).mean()

avg_volume = volume.rolling(20).mean()

rsi = calc_rsi(close)

signal = rsi.rolling(6).mean()

buy_signal = (
    (rsi.shift(1) < signal.shift(1))
    & (rsi >= signal)
)

sell_signal = (
    (rsi.shift(1) > signal.shift(1))
    & (rsi <= signal)
)

latest_close = close.iloc[-1]
latest_ma20 = ma20.iloc[-1]
latest_ma60 = ma60.iloc[-1]

latest_rsi = rsi.iloc[-1]
latest_signal = signal.iloc[-1]

latest_volume = volume.iloc[-1]
latest_avg_volume = avg_volume.iloc[-1]

final_signal = get_signal(
    latest_close,
    latest_ma20,
    latest_ma60,
    latest_rsi,
    latest_signal,
    latest_volume,
    latest_avg_volume
)

buy_dates = close[buy_signal].index
sell_dates = close[sell_signal].index

latest_buy = (
    buy_dates[-1].strftime("%Y-%m-%d")
    if len(buy_dates) > 0
    else "-"
)

latest_sell = (
    sell_dates[-1].strftime("%Y-%m-%d")
    if len(sell_dates) > 0
    else "-"
)

st.subheader(f"🔍 {name} 상세 분석")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "현재가",
    f"{latest_close:,.0f}"
)

c2.metric(
    "20일선",
    f"{latest_ma20:,.0f}"
)

c3.metric(
    "60일선",
    f"{latest_ma60:,.0f}"
)

c4.metric(
    "RSI(14)",
    f"{latest_rsi:.2f}"
)

c5.metric(
    "Signal(6)",
    f"{latest_signal:.2f}"
)

c6, c7, c8, c9 = st.columns(4)

c6.metric(
    "거래량",
    f"{latest_volume:,.0f}"
)

c7.metric(
    "평균거래량",
    f"{latest_avg_volume:,.0f}"
)

c8.metric(
    "최근 매수신호",
    latest_buy
)

c9.metric(
    "최근 매도신호",
    latest_sell
)

st.success(
    f"종합판정 : {final_signal}"
)

# --------------------------
# 가격 차트
# --------------------------

fig_price = go.Figure()

fig_price.add_trace(
    go.Scatter(
        x=close.index,
        y=close,
        name="종가",
        line=dict(width=3)
    )
)

fig_price.add_trace(
    go.Scatter(
        x=ma20.index,
        y=ma20,
        name="20일선"
    )
)

fig_price.add_trace(
    go.Scatter(
        x=ma60.index,
        y=ma60,
        name="60일선"
    )
)

fig_price.add_trace(
    go.Scatter(
        x=close[buy_signal].index,
        y=close[buy_signal],
        mode="markers",
        name="매수",
        marker=dict(
            symbol="triangle-up",
            size=14
        )
    )
)

fig_price.add_trace(
    go.Scatter(
        x=close[sell_signal].index,
        y=close[sell_signal],
        mode="markers",
        name="매도",
        marker=dict(
            symbol="triangle-down",
            size=14
        )
    )
)

fig_price.update_layout(
    height=500,
    hovermode="x unified"
)

st.plotly_chart(
    fig_price,
    use_container_width=True
)

# --------------------------
# RSI 차트
# --------------------------

fig_rsi = go.Figure()

fig_rsi.add_trace(
    go.Scatter(
        x=rsi.index,
        y=rsi,
        name="RSI(14)"
    )
)

fig_rsi.add_trace(
    go.Scatter(
        x=signal.index,
        y=signal,
        name="Signal(6)"
    )
)

fig_rsi.add_hline(y=75)
fig_rsi.add_hline(y=50)
fig_rsi.add_hline(y=35)

fig_rsi.update_layout(
    height=450,
    yaxis=dict(range=[0, 100]),
    hovermode="x unified"
)

st.plotly_chart(
    fig_rsi,
    use_container_width=True
)
