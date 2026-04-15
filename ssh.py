import yfinance as ydatas
import pandas as pd
import ta
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

MAX_WORKERS = 10

def run_scan(progress_callback=None, mode="classic"):
    with open("tickers.txt","r") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]

    squeeze_now_list = []
    squeezed_last_month_list = []
    failed_tickers = []
    total = len(tickers)
    lock = Lock()
    counter = [0]

    def process_ticker(ticker):
        try:
            end = datetime.date.today()
            start = end - datetime.timedelta(days=180)
            
            ticker_obj = ydatas.Ticker(f"{ticker}.IS")
            df = ticker_obj.history(start=start, end=end)

            if df.empty:
                return ("failed", ticker)
            
            df.index = df.index.tz_localize(None)

           
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.dropna(inplace=True)
            


            df["ADX"] = ta.trend.ADXIndicator(df["High"],df["Low"],df["Close"],window=14).adx()
            df["RSI"] = ta.momentum.RSIIndicator(df["Close"],window=14).rsi()

            ema = df["Close"].ewm(span=10, adjust=False).mean()
            std = df["Close"].rolling(window=20).std()
            df["BB_Upper"] = ema + 2 * std
            df["BB_Lower"] = ema - 2 * std

            df["ATR"] = ta.volatility.AverageTrueRange(df["High"],df["Low"],df["Close"],window=14).average_true_range()

            kc_mid = df["Close"].ewm(span=20, adjust=False).mean()
            df["KC_Upper"] = kc_mid + 1.5 * df["ATR"]
            df["KC_Lower"] = kc_mid - 1.5 * df["ATR"]
            df.dropna(inplace=True)

            if df.empty:
                return ("skip", ticker)

            adx = round(float(df["ADX"].iloc[-1]), 2)
            rsi = round(float(df["RSI"].iloc[-1]), 2)
            bb = (df["BB_Upper"].iloc[-1] < df["KC_Upper"].iloc[-1] and
                  df["BB_Lower"].iloc[-1] > df["KC_Lower"].iloc[-1])

            no_trend = adx < 20
            rsi_flat = 40 <= rsi <= 60

            if mode == "percentile":
                range_series = df["High"] - df["Low"]
                last3_range = range_series.iloc[-3:].mean()
                threshold = range_series.iloc[-20:].quantile(0.25)
                squeeze_now = no_trend and rsi_flat and (last3_range < threshold)
            else:
                squeeze_now = no_trend and rsi_flat and bb

            cutoff = pd.Timestamp(datetime.date.today()) - pd.Timedelta(days=30)

            if mode == "percentile":
                range_series = df["High"] - df["Low"]
                threshold = range_series.iloc[-20:].quantile(0.25)
                squeeze_cond = (
                    (df["ADX"] < 20) &
                    (df["RSI"].between(40, 60)) &
                    ((df["High"] - df["Low"]) < threshold)
                )
            else:
                squeeze_cond = (
                    (df["ADX"] < 20) &
                    (df["RSI"].between(40, 60)) &
                    (df["BB_Upper"] < df["KC_Upper"]) &
                    (df["BB_Lower"] > df["KC_Lower"])
                )

            squeeze_count = int(squeeze_cond.loc[df.index >= cutoff].sum())
            print(f"{ticker} → Now:{squeeze_now} | 30d:{squeeze_count}")
            return ("ok", ticker, adx, rsi, squeeze_now, squeeze_count)

        except Exception as e:
            print(f"{ticker} → {e}")
            return ("failed", ticker)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_ticker, t): t for t in tickers}
        for future in as_completed(futures):
            with lock:
                counter[0] += 1
                if progress_callback:
                    progress_callback(futures[future], counter[0], total)

            result = future.result()

            if result[0] == "failed":
                failed_tickers.append(result[1])
                continue
            if result[0] == "skip":
                continue

            _, ticker, adx, rsi, squeeze_now, squeeze_count = result

            if squeeze_now and squeeze_count >= 3:
                squeeze_now_list.append({"Ticker": ticker, "ADX": adx, "RSI": rsi, "30d Squeeze Days": squeeze_count})
            if squeeze_count >= 3:
                squeezed_last_month_list.append({"Ticker": ticker, "ADX": adx, "RSI": rsi, "30d Squeeze Days": squeeze_count})

    return squeeze_now_list, squeezed_last_month_list, failed_tickers, total