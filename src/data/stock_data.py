# import yfinance as yf
# import pandas as pd
# from datetime import datetime, timedelta
# import time
# import pandas_market_calendars as mcal

# class StockDataFetcher:
#     def __init__(self):
#         self.cache = {}
#         self.market_suffix = '.NS'  # Default to NSE (National Stock Exchange)
#         self.rate_limit_delay = 1  # Delay between API calls in seconds

#     def set_market(self, market: str = 'NSE'):
#         """Set the market to fetch data from (NSE or BSE)"""
#         self.market_suffix = '.NS' if market.upper() == 'NSE' else '.BO'

#     def check_symbol_availability(self, symbol: str) -> bool:
#         """
#         Check if a stock symbol is available and valid.
        
#         Args:
#             symbol (str): Stock symbol to check
            
#         Returns:
#             bool: True if symbol is valid and available, False otherwise
#         """
#         try:
#             # Add market suffix if not present
#             if not symbol.endswith(('.NS', '.BO')):
#                 symbol = f"{symbol}{self.market_suffix}"
            
#             # Try to fetch basic info
#             stock = yf.Ticker(symbol)
#             info = stock.info
            
#             # Check if we got valid data
#             return bool(info.get('regularMarketPrice'))
#         except Exception as e:
#             print(f"Symbol {symbol} is not available: {str(e)}")
#             return False

#     def validate_symbols(self, symbols: list, max_symbols: int = 50) -> list:
#         """
#         Validate a list of symbols and return only the valid ones.
        
#         Args:
#             symbols (list): List of stock symbols to validate
#             max_symbols (int): Maximum number of symbols to process
            
#         Returns:
#             list: List of valid symbols
#         """
#         if len(symbols) > max_symbols:
#             print(f"Warning: Limiting to first {max_symbols} symbols")
#             symbols = symbols[:max_symbols]
        
#         valid_symbols = []
#         for symbol in symbols:
#             if self.check_symbol_availability(symbol):
#                 valid_symbols.append(symbol)
#             time.sleep(self.rate_limit_delay)  # Respect rate limits
        
#         return valid_symbols

#     def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None, 
#                       period: str = None, interval: str = "1d") -> pd.DataFrame:
#         """
#         Fetch stock data for a given symbol.
        
#         Args:
#             symbol (str): Stock symbol (e.g., 'RELIANCE' for Reliance Industries)
#             start_date (str): Start date in 'YYYY-MM-DD' format
#             end_date (str): End date in 'YYYY-MM-DD' format
#             period (str): Time period to fetch (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
#             interval (str): Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
#         Returns:
#             pd.DataFrame: DataFrame containing stock data
#         """
#         try:
#             # Add market suffix if not present
#             if not symbol.endswith(('.NS', '.BO')):
#                 symbol = f"{symbol}{self.market_suffix}"
            
#             # Create cache key
#             cache_key = f"{symbol}_{start_date}_{end_date}_{period}_{interval}"
            
#             # Check cache first
#             if cache_key in self.cache:
#                 return self.cache[cache_key]
            
#             # Fetch data
#             stock = yf.Ticker(symbol)
            
#             if start_date and end_date:
#                 df = stock.history(start=start_date, end=end_date, interval=interval)
#             elif period:
#                 df = stock.history(period=period, interval=interval)
#             else:
#                 # Default to 1 month if no dates or period specified
#                 df = stock.history(period='1mo', interval=interval)
            
#             # Cache the result
#             self.cache[cache_key] = df
            
#             return df
#         except Exception as e:
#             print(f"Error fetching data for {symbol}: {str(e)}")
#             return pd.DataFrame()

#     def get_multiple_stocks(self, symbols: list, start_date: str = None, end_date: str = None,
#                           period: str = None, interval: str = "1d", max_symbols: int = 50) -> dict:
#         """
#         Fetch data for multiple stock symbols.
        
#         Args:
#             symbols (list): List of stock symbols
#             start_date (str): Start date in 'YYYY-MM-DD' format
#             end_date (str): End date in 'YYYY-MM-DD' format
#             period (str): Time period to fetch
#             interval (str): Data interval
#             max_symbols (int): Maximum number of symbols to process
        
#         Returns:
#             dict: Dictionary of DataFrames with symbols as keys
#         """
#         # Validate symbols first
#         valid_symbols = self.validate_symbols(symbols, max_symbols)
        
#         if not valid_symbols:
#             print("No valid symbols found!")
#             return {}
            
#         result = {}
#         for symbol in valid_symbols:
#             result[symbol] = self.get_stock_data(symbol, start_date, end_date, period, interval)
#             time.sleep(self.rate_limit_delay)  # Respect rate limits
            
#         return result

#     def get_stock_info(self, symbol: str) -> dict:
#         """
#         Get basic information about a stock.
        
#         Args:
#             symbol (str): Stock symbol
        
#         Returns:
#             dict: Dictionary containing stock information
#         """
#         try:
#             # Add market suffix if not present
#             if not symbol.endswith(('.NS', '.BO')):
#                 symbol = f"{symbol}{self.market_suffix}"
                
#             stock = yf.Ticker(symbol)
#             info = stock.info
            
#             # Get historical data for high/low prices
#             hist = stock.history(period='1mo')
#             high_price = round(float(hist['High'].max()), 2)
#             low_price = round(float(hist['Low'].min()), 2)
#             current_price = round(float(info.get('currentPrice', 0)), 2)
#             pe_ratio = round(float(info.get('trailingPE', 0)), 3)
#             dividend_yield = round(float(info.get('dividendYield', 0)), 2)
            
#             return {
#                 'name': info.get('longName', ''),
#                 'sector': info.get('sector', ''),
#                 'industry': info.get('industry', ''),
#                 'market_cap': info.get('marketCap', 0),
#                 'current_price': current_price,
#                 'high_price': high_price,
#                 'low_price': low_price,
#                 'pe_ratio': pe_ratio,
#                 'dividend_yield': dividend_yield
#             }
#         except Exception as e:
#             print(f"Error fetching info for {symbol}: {str(e)}")
#             return {}

#     def get_previous_business_day_stats(self, symbol: str) -> dict:
#         """
#         Get detailed statistics for the previous business day.
        
#         Args:
#             symbol (str): Stock symbol (e.g., 'HDFCBANK.NS' for HDFC Bank)
            
#         Returns:
#             dict: Dictionary containing previous business day statistics including:
#                 - date: Previous business day
#                 - open: Opening price
#                 - high: Highest price
#                 - low: Lowest price
#                 - close: Closing price
#                 - volume: Trading volume
#                 - change: Price change from previous day
#                 - change_pct: Percentage change from previous day
#         """
#         # Fetch last 5 days of data to ensure we have enough data
#         self.get_stock_data(symbol, period="5d")
        
#         if self.cache.get(f"{symbol}_5d_1d") is None or len(self.cache[f"{symbol}_5d_1d"]) < 2:
#             raise ValueError("Not enough data available")
            
#         # Get the last two business days
#         last_day = self.cache[f"{symbol}_5d_1d"].iloc[-1]
#         previous_day = self.cache[f"{symbol}_5d_1d"].iloc[-2]
        
#         # Calculate price changes
#         price_change = last_day['Close'] - previous_day['Close']
#         price_change_pct = (price_change / previous_day['Close']) * 100
        
#         return {
#             'date': self.cache[f"{symbol}_5d_1d"].index[-1].strftime('%Y-%m-%d'),
#             'open': round(last_day['Open'], 2),
#             'high': round(last_day['High'], 2),
#             'low': round(last_day['Low'], 2),
#             'close': round(last_day['Close'], 2),
#             'volume': int(last_day['Volume']),
#             'change': round(price_change, 2),
#             'change_pct': round(price_change_pct, 2),
#             'previous_close': round(previous_day['Close'], 2)
#         } 