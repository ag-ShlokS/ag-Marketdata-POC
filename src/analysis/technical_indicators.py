import pandas as pd
import numpy as np

class TechnicalIndicators:
    @staticmethod
    def calculate_sma(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Calculate Simple Moving Average"""
        return df['Close'].rolling(window=window).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['Close'].ewm(span=window, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2) -> tuple:
        """Calculate Bollinger Bands"""
        sma = df['Close'].rolling(window=window).mean()
        std = df['Close'].rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, sma, lower_band 