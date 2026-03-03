import yfinance as ydatas
import pandas as pd
import ta
import time

def run_scan():
    with open("tickers.txt","r")as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
        
    squeeze_now_list =[]
    squeezed_last_month_list=[]
    failed_tickers = []
    for ticker in tickers:
        try:
            df=ydatas.download(f"{ticker}.IS",period="6mo",auto_adjust=True,progress=False)
            if df.empty:
                print(f"{ticker} -> Unable to process")
                failed_tickers.append(ticker)
                continue
        
            #If MultiIndex exists,fix.
            if isinstance(df.columns,pd.MultiIndex):
                df.columns= df.columns.get_level_values(0)

            #Get only needed columns defined below:
            df =df[["Open","High","Low","Close","Volume"]]
            #Clear NaNs
            df.dropna(inplace=True)

            #ADX 
            df["ADX"]=ta.trend.ADXIndicator(df["High"],df["Low"],df["Close"],window=14).adx()
            #RSI
            df["RSI"]=ta.momentum.RSIIndicator(df["Close"],window=14).rsi()
            
            #EMA-10 Based Bollinger Band.
            ema=df["Close"].ewm(span=10,adjust=False).mean()
            std=df["Close"].rolling(window=20).std()
            df["BB_Upper"]=ema +2 * std
            df["BB_Lower"]=ema -2 * std

            #ATR:Needed for Keltner
            df["ATR"]=ta.volatility.AverageTrueRange(df["High"],df["Low"],df["Close"],window=14).average_true_range()

            #Keltner
            kc_mid=df["Close"].ewm(span=20,adjust=False).mean()
            df["KC_Upper"]=kc_mid +1.5 *df["ATR"]
            df["KC_Lower"]=kc_mid -1.5 *df["ATR"]
            df.dropna(inplace=True)
            if df.empty:
                continue

            adx = round(float(df["ADX"].iloc[-1]),2)
            rsi = round(float(df["RSI"].iloc[-1]),2) 
            bb =df["BB_Upper"].iloc[-1] < df["KC_Upper"].iloc[-1] and \
                df["BB_Lower"].iloc[-1] > df["KC_Lower"].iloc[-1]

            no_trend=adx <20
            rsi_flat =40 <=rsi <=60
            
            squeeze_now = no_trend and rsi_flat and bb

            # Last 30 days
            cutoff = df.index[-1] - pd.Timedelta(days=30)

            squeeze_cond = (
                (df["ADX"] < 20) &
                (df["RSI"].between(40, 60)) &
                (df["BB_Upper"] < df["KC_Upper"]) &
                (df["BB_Lower"] > df["KC_Lower"])
            )

            squeeze_count = int(squeeze_cond.loc[df.index >= cutoff].sum())

            if squeeze_now and squeeze_count >= 3:
                squeeze_now_list.append({"Ticker": ticker, "ADX": adx, "RSI": rsi, "30d Squeeze Days": squeeze_count})

            if squeeze_count >= 3:
                squeezed_last_month_list.append({"Ticker": ticker, "ADX": adx, "RSI": rsi, "30d Squeeze Days": squeeze_count})

            print(f"{ticker} → Now:{squeeze_now} | 30d squeeze days:{squeeze_count}")

            
        except Exception as e:
            print(f"{ticker} → {e} Unable to process")
            failed_tickers.append(ticker)
            continue    
        time.sleep(0.05)
    return squeeze_now_list,squeezed_last_month_list,failed_tickers

