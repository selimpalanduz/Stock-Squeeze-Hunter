import yfinance as ydatas

ticker = input("Hisse kodu girin (örn: THYAO): ").strip().upper()

df = ydatas.download(f"{ticker}.IS", period="6mo", auto_adjust=True, progress=False)

if df.empty:
    print(f"{ticker} için veri bulunamadı.")
else:
    #If MultiIndex exists,fix.
    if isinstance(df.columns,pd.MultiIndex):
        df.columns= df.columns.get_level_values(0)
    #Get only needed columns defined below:
    df =df[["Open","High","Low","Close","Volume"]]
    #Clear NaNs
    df.dropna(inplace=True)

    print(df.tail(10))