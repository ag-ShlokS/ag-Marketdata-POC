import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class StockDataFetcher:
    def __init__(self):
        self.cache = {}

    def get_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Fetch stock data for a given symbol.
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL' for Apple)
            period (str): Time period to fetch (e.g., '1d', '5d', '1mo', '3mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval (str): Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            pd.DataFrame: DataFrame containing stock data
        """
        try:
            # Create cache key
            cache_key = f"{symbol}_{period}_{interval}"
            
            # Check cache first
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Fetch data
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            # Cache the result
            self.cache[cache_key] = df
            
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_multiple_stocks(self, symbols: list, period: str = "1mo", interval: str = "1d") -> dict:
        """
        Fetch data for multiple stock symbols.
        
        Args:
            symbols (list): List of stock symbols
            period (str): Time period to fetch
            interval (str): Data interval
        
        Returns:
            dict: Dictionary of DataFrames with symbols as keys
        """
        return {symbol: self.get_stock_data(symbol, period, interval) for symbol in symbols}

    def get_stock_info(self, symbol: str) -> dict:
        """
        Get basic information about a stock.
        
        Args:
            symbol (str): Stock symbol
        
        Returns:
            dict: Dictionary containing stock information
        """
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0)
            }
        except Exception as e:
            print(f"Error fetching info for {symbol}: {str(e)}")
            return {} 