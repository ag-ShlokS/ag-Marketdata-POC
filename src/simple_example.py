import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def main():
    # Get stock data for Apple
    symbol = 'MSFT'
    print(f"\nFetching data for {symbol}...")
    
    # Fetch data
    stock = yf.Ticker(symbol)
    df = stock.history(period='1mo')
    
    # Print basic information
    print(f"\n{symbol} Stock Information:")
    print(f"Current Price: ${df['Close'].iloc[-1]:.2f}")
    print(f"52 Week High: ${df['High'].max():.2f}")
    print(f"52 Week Low: ${df['Low'].min():.2f}")
    print(f"Average Volume: {df['Volume'].mean():.0f}")
    
    # Print recent price changes
    print("\nRecent Price Changes:")
    recent_changes = df['Close'].pct_change().tail(5)
    for date, change in recent_changes.items():
        print(f"{date.date()}: {change*100:.2f}%")
    
    # Calculate and print some basic statistics
    print("\nBasic Statistics:")
    print(f"Average Daily Return: {df['Close'].pct_change().mean()*100:.2f}%")
    print(f"Daily Return Volatility: {df['Close'].pct_change().std()*100:.2f}%")
    print(f"Total Return (1 month): {(df['Close'].iloc[-1]/df['Close'].iloc[0] - 1)*100:.2f}%")

if __name__ == "__main__":
    main() 