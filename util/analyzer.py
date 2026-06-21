from util.indicators import calc_rsi

RSI_PERIOD = 14
SIGNAL_PERIOD = 6


def judge_signal(close, ma20, ma60, rsi, signal, volume, avg_volume):
    if rsi > signal and close > ma20 and ma20 > ma60 and volume > avg_volume:
        return "🟢 강매수"
    elif rsi > signal and close > ma20:
        return "🟡 매수관심"
    elif rsi < signal and close < ma20 and ma20 < ma60:
        return "⚫ 하락추세"
    elif rsi < signal and close < ma20:
        return "🔴 약세전환"
    else:
        return "🟠 관망"


def score_stock(close, ma20, ma60, rsi, signal, volume, avg_volume, recent_buy):
    score = 0

    if close > ma20:
        score += 20
    if ma20 > ma60:
        score += 20
    if rsi > signal:
        score += 20
    if volume > avg_volume:
        score += 20
    if recent_buy:
        score += 20

    return score


def analyze_df(df):
    close = df["Close"]
    volume = df["Volume"]

    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    avg_volume = volume.rolling(20).mean()

    rsi = calc_rsi(close, RSI_PERIOD)
    signal = rsi.rolling(SIGNAL_PERIOD).mean()

    buy_signal = (rsi.shift(1) < signal.shift(1)) & (rsi >= signal)
    sell_signal = (rsi.shift(1) > signal.shift(1)) & (rsi <= signal)

    buy_dates = close[buy_signal].index
    sell_dates = close[sell_signal].index

    latest_buy = buy_dates[-1].strftime("%Y-%m-%d") if len(buy_dates) > 0 else "-"
    latest_sell = sell_dates[-1].strftime("%Y-%m-%d") if len(sell_dates) > 0 else "-"

    recent_buy = False
    if len(buy_dates) > 0:
        recent_buy = (close.index[-1] - buy_dates[-1]).days <= 10

    latest = {
        "close": close.iloc[-1],
        "ma20": ma20.iloc[-1],
        "ma60": ma60.iloc[-1],
        "rsi": rsi.iloc[-1],
        "signal": signal.iloc[-1],
        "volume": volume.iloc[-1],
        "avg_volume": avg_volume.iloc[-1],
        "latest_buy": latest_buy,
        "latest_sell": latest_sell,
        "recent_buy": recent_buy,
    }

    latest["final"] = judge_signal(
        latest["close"],
        latest["ma20"],
        latest["ma60"],
        latest["rsi"],
        latest["signal"],
        latest["volume"],
        latest["avg_volume"],
    )

    latest["score"] = score_stock(
        latest["close"],
        latest["ma20"],
        latest["ma60"],
        latest["rsi"],
        latest["signal"],
        latest["volume"],
        latest["avg_volume"],
        latest["recent_buy"],
    )

    return close, volume, ma20, ma60, rsi, signal, buy_signal, sell_signal, latest