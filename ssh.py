import yfinance as ydatas
import pandas as pd
import ta
ticker = input("Enter code of stock(for example: THYAO): ").strip().upper()

df = ydatas.download(f"{ticker}.IS", period="6mo", auto_adjust=True, progress=False)

if df.empty:
    print(f"{ticker} no data found for this.")
else:
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

    adx = round(float(df["ADX"].iloc[-1]),2)
    rsi = round(float(df["RSI"].iloc[-1]),2) 

    no_trend=adx <20
    rsi_flat =40 <=rsi <=60
    print(f"ADX:{adx} →{'There is no trend,stock is squeezed' if adx <20 else 'A trend exists'}")
    print(f"RSI: {rsi} → {'Squeeze band' if rsi_flat else 'Not squeezed'}")

    if no_trend and rsi_flat:
        print("\n Squeeze is detected!")
    else:
        print("\n No squeeze.")
    # --- Last month's squeeze history --- #0
    last_month = df[df.index >= df.index[-1] - pd.Timedelta(days=30)]
    print(f"\n--- Last month's squeeze history ---") #0
    squeeze_count = 0 #0
    for date, row in last_month.iterrows(): #0
        adx_d = round(float(row["ADX"]), 2) #0
        rsi_d = round(float(row["RSI"]), 2) #0
        is_squeeze = adx_d < 20 and 40 <= rsi_d <= 60 #0
        if is_squeeze: #0
            squeeze_count += 1 #0
            print(f"{date.strftime('%d.%m.%Y')}: Squeeze  RSI: {rsi_d}  ADX: {adx_d}") #0
    print(f"\nTotal {squeeze_count} days squeezed.") #0
