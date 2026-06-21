import streamlit as st
import yfinance as yf
import pandas as pd

@st.cache_data(ttl=60 * 60)
def load_yf_data(ticker, period="1y"):
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)

    if df.empty:
        return pd.DataFrame()

    close = df["Close"]
    volume = df["Volume"]

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    return pd.DataFrame({"Close": close, "Volume": volume}).dropna()