import pandas as pd
import yfinance as yf
from stock_visualizer import StockVisualizer

def main():
    # Create a StockVisualizer instance
    visualizer = StockVisualizer()
    
    # Download sample stock data for HDFC Bank (HDFCBANK.NS)
    stock_symbol = "HDFCBANK.NS"  # HDFC Bank stock on NSE
    df = yf.download(stock_symbol, period="1mo")  # Get 1 month of data
    
    # Get previous day's statistics
    prev_day_stats = visualizer.get_previous_day_stats(df)
    
    print("\nPrevious Business Day Statistics for HDFC Bank:")
    print(f"Date: {prev_day_stats['date'].strftime('%Y-%m-%d')}")
    print(f"Opening Price: ₹{prev_day_stats['open']:.2f}")
    print(f"Highest Price: ₹{prev_day_stats['high']:.2f}")
    print(f"Lowest Price: ₹{prev_day_stats['low']:.2f}")
    print(f"Closing Price: ₹{prev_day_stats['close']:.2f}")
    print(f"Trading Volume: {prev_day_stats['volume']:,}")
    
    # Create and show the candlestick chart
    fig = visualizer.create_candlestick_chart(df, title=f"{stock_symbol} Stock Price")
    fig.show()

if __name__ == "__main__":
    main() 