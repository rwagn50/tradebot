import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt
import io

st.title("Enhanced Stock Trading Bot Simulation with Live Monitoring")

# Tabs for organization
tab1, tab2, tab3, tab4 = st.tabs(["Inputs & Control", "Live Data & Logs", "Charts & Reports", "Logic & Sources"])

with tab1:
    st.header("User Inputs")
    tickers_input = st.text_input("Enter up to 5 tickers (comma-separated)", "AAPL,MSFT")
    tickers = [t.strip() for t in tickers_input.split(',') if t.strip()][:5]
    capital = st.number_input("Starting Capital ($)", min_value=1000.0, value=10000.0)
    target_daily_return = st.number_input("Target Daily Return (%)", value=0.5)
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    end_date = st.date_input("End Date", datetime.now())
    short_window = st.number_input("Short MA Window", value=50)
    long_window = st.number_input("Long MA Window", value=200)
    run_button = st.button("Run Simulation")

with tab4:
    st.header("Strategy Logic & Data Sources")
    st.write("Strategy: Moving Average Crossover for signals, aiming for ~0.5% daily (adjusted via take-profit; note: unrealistic consistently, for simulation only).")
    st.write("Logic: Buy on short MA > long MA, sell on cross below or at target return.")
    st.write("Data Sources: yfinance for historical/intraday prices & news. Monitored for accuracy via timestamps.")
    st.write("Risk: Simulation only; real trading risks loss. Backtest results vary.")

def fetch_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end, interval="1d")
    return data

def moving_average_crossover(data, short_window, long_window):
    data = data.copy()
    data['Short_MA'] = data['Close'].rolling(window=short_window, min_periods=1).mean()
    data['Long_MA'] = data['Close'].rolling(window=long_window, min_periods=1).mean()
    data['Position'] = 0
    data.loc[data['Short_MA'] > data['Long_MA'], 'Position'] = 1
    data.loc[data['Short_MA'] < data['Long_MA'], 'Position'] = -1
    data['Position'] = data['Position'].shift(1).fillna(0)
    return data

def get_live_quote(ticker):
    try:
        quote = yf.Ticker(ticker).info
        return quote.get('regularMarketPrice', 'N/A'), quote.get('regularMarketChangePercent', 'N/A')
    except:
        return 'N/A', 'N/A'

def get_news(ticker):
    try:
        news = yf.Ticker(ticker).news[:5]
        return [n['title'] for n in news]
    except:
        return ["No news available"]

def enhanced_strategy(data, capital, ticker, target_return):
    data = moving_average_crossover(data, short_window, long_window)
    hold_position = 0
    shares = 0
    trades = []
    imminent = []
    entry_price = 0
    for i in range(len(data)):
        if data['Position'].iloc[i] == 1 and hold_position == 0:
            shares = capital / data['Close'].iloc[i]
            entry_price = data['Close'].iloc[i]
            capital = 0
            hold_position = 1
            trades.append(f"{ticker} Buy at {data.index[i]}: {entry_price:.2f}, shares: {shares:.2f}")
        elif hold_position == 1:
            current_return = (data['Close'].iloc[i] - entry_price) / entry_price
            if data['Position'].iloc[i] == -1 or current_return >= target_return / 100:
                trades.append(f"{ticker} Sell at {data.index[i]}: {data['Close'].iloc[i]:.2f}, return: {current_return*100:.2f}%")
                capital = shares * data['Close'].iloc[i]
                shares = 0
                hold_position = 0
        if i < len(data) - 1:
            next_pos = data['Position'].iloc[i+1]
            if next_pos == 1 and hold_position == 0:
                imminent.append(f"Prep buy {ticker} if MA cross soon")
            elif hold_position == 1 and ((data['Close'].iloc[i+1] - entry_price) / entry_price >= target_return / 100 or next_pos == -1):
                imminent.append(f"Prep sell {ticker} at target or cross")
    final_value = capital + (shares * data['Close'].iloc[-1] if hold_position else 0)
    return trades, final_value, imminent, data

def plot_chart(data, ticker):
    fig, ax = plt.subplots()
    ax.plot(data['Close'], label='Close')
    ax.plot(data['Short_MA'], label='Short MA')
    ax.plot(data['Long_MA'], label='Long MA')
    ax.legend()
    ax.set_title(f'{ticker} Chart')
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf

if 'simulation_data' not in st.session_state:
    st.session_state.simulation_data = {}
    st.session_state.running = False

if run_button:
    st.session_state.running = True
    st.session_state.simulation_data = {}
    total_final = 0
    per_cap = capital / len(tickers) if tickers else 0
    for ticker in tickers:
        data = fetch_data(ticker, start_date, end_date)
        trades, final, imminent, processed_data = enhanced_strategy(data, per_cap, ticker, target_daily_return)
        st.session_state.simulation_data[ticker] = {
            'trades': trades,
            'imminent': imminent,
            'data': processed_data,
            'final': final,
            'chart': plot_chart(processed_data, ticker)
        }
        total_final += final
    total_return = (total_final / capital - 1) * 100
    days = (end_date - start_date).days
    ann_return = (total_final / capital) ** (365 / days) * 100 - 100 if days > 0 else 0
    st.session_state.results = f"Total Return: {total_return:.2f}%\nAnnualized: {ann_return:.2f}%"

# Live monitoring loop
placeholder = st.empty()
stop_button = st.button("Stop Simulation")

if 'running' in st.session_state and st.session_state.running:
    while st.session_state.running:
        with placeholder.container():
            with tab2:
                st.header("Live Data, Logs & Reports")
                for ticker in tickers:
                    st.subheader(ticker)
                    price, change = get_live_quote(ticker)
                    st.metric("Current Price", f"${price}", f"{change}%")
                    st.write("News Feed:", ", ".join(get_news(ticker)))
                    if ticker in st.session_state.simulation_data:
                        st.dataframe(st.session_state.simulation_data[ticker]['data'].tail(10))
                        st.text_area("Trades Log", "\n".join(st.session_state.simulation_data[ticker]['trades']), height=150)
                        st.text_area("Imminent Trades", "\n".join(st.session_state.simulation_data[ticker]['imminent']), height=100)
                        st.write(f"Fetch Time: {datetime.now()}")
            with tab3:
                st.header("Charts & Performance")
                for ticker in tickers:
                    if ticker in st.session_state.simulation_data:
                        st.image(st.session_state.simulation_data[ticker]['chart'], caption=f"{ticker} Chart")
                if 'results' in st.session_state:
                    st.write(st.session_state.results)
        time.sleep(60)  # Update every minute
        if stop_button:
            st.session_state.running = False
            break
        st.rerun()
