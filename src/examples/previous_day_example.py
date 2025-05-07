# import yfinance as yf
# import pandas as pd
# from datetime import datetime, timedelta

# def get_previous_business_day_stats(symbol: str) -> dict:
#     """
#     Get detailed statistics for the previous business day.
    
#     Args:
#         symbol (str): Stock symbol (e.g., 'HDFCBANK.NS' for HDFC Bank)
        
#     Returns:
#         dict: Dictionary containing previous business day statistics
#     """
#     # Fetch last 5 days of data to ensure we have enough data
#     df = yf.download(symbol, period="5d")
    
#     if len(df) < 2:
#         raise ValueError("Not enough data available")
        
#     # Get the last two business days
#     last_day = df.iloc[-1]
#     previous_day = df.iloc[-2]
    
#     # Calculate price changes
#     price_change = float(last_day['Close'].iloc[0]) - float(previous_day['Close'].iloc[0])
#     price_change_pct = (price_change / float(previous_day['Close'].iloc[0])) * 100
    
#     return {
#         'date': df.index[-1].strftime('%Y-%m-%d'),
#         'open': round(float(last_day['Open'].iloc[0]), 2),
#         'high': round(float(last_day['High'].iloc[0]), 2),
#         'low': round(float(last_day['Low'].iloc[0]), 2),
#         'close': round(float(last_day['Close'].iloc[0]), 2),
#         'volume': int(float(last_day['Volume'].iloc[0])),
#         'change': round(price_change, 2),
#         'change_pct': round(price_change_pct, 2),
#         'previous_close': round(float(previous_day['Close'].iloc[0]), 2)
#     }

# def main():
#     # Example stocks to analyze
#     stocks = ["HDFCBANK.NS", "RELIANCE.NS", "TCS.NS"]
    
#     for symbol in stocks:
#         try:
#             print(f"\nAnalyzing {symbol}...")
#             stats = get_previous_business_day_stats(symbol)
            
#             print(f"Date: {stats['date']}")
#             print(f"Previous Close: ₹{stats['previous_close']:.2f}")
#             print(f"Open: ₹{stats['open']:.2f}")
#             print(f"High: ₹{stats['high']:.2f}")
#             print(f"Low: ₹{stats['low']:.2f}")
#             print(f"Close: ₹{stats['close']:.2f}")
#             print(f"Change: ₹{stats['change']:.2f} ({stats['change_pct']:.2f}%)")
#             print(f"Volume: {stats['volume']:,}")
#             print("-" * 50)
            
#         except Exception as e:
#             print(f"Error analyzing {symbol}: {str(e)}")

# if __name__ == "__main__":
#     main() 