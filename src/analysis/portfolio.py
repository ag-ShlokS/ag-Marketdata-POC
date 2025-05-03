import pandas as pd
import numpy as np
from typing import Dict, List

class PortfolioAnalyzer:
    def __init__(self, initial_investment: float = 10000.0):
        self.initial_investment = initial_investment

    def calculate_portfolio_value(self, stock_data: Dict[str, pd.DataFrame], 
                                weights: Dict[str, float]) -> pd.DataFrame:
        """
        Calculate portfolio value over time based on stock data and weights.
        
        Args:
            stock_data: Dictionary of stock symbols and their price data
            weights: Dictionary of stock symbols and their portfolio weights
        
        Returns:
            DataFrame with portfolio value over time
        """
        # Ensure weights sum to 1
        total_weight = sum(weights.values())
        if not np.isclose(total_weight, 1.0):
            weights = {k: v/total_weight for k, v in weights.items()}
        
        # Calculate individual stock values
        portfolio_values = pd.DataFrame()
        for symbol, df in stock_data.items():
            if symbol in weights:
                stock_value = df['Close'] * (self.initial_investment * weights[symbol] / df['Close'].iloc[0])
                portfolio_values[symbol] = stock_value
        
        # Calculate total portfolio value
        portfolio_values['Total'] = portfolio_values.sum(axis=1)
        return portfolio_values

    def calculate_returns(self, portfolio_values: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate portfolio returns.
        
        Args:
            portfolio_values: DataFrame with portfolio values over time
        
        Returns:
            Dictionary with return metrics
        """
        total_return = (portfolio_values['Total'].iloc[-1] / self.initial_investment - 1) * 100
        
        # Calculate daily returns
        daily_returns = portfolio_values['Total'].pct_change()
        
        # Calculate metrics
        annualized_return = (1 + total_return/100) ** (252/len(portfolio_values)) - 1
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annualized_return / (volatility/100)) if volatility != 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return * 100,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio
        }

    def calculate_drawdown(self, portfolio_values: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate maximum drawdown.
        
        Args:
            portfolio_values: DataFrame with portfolio values over time
        
        Returns:
            Dictionary with drawdown metrics
        """
        portfolio_values['Peak'] = portfolio_values['Total'].cummax()
        portfolio_values['Drawdown'] = (portfolio_values['Total'] - portfolio_values['Peak']) / portfolio_values['Peak'] * 100
        
        max_drawdown = portfolio_values['Drawdown'].min()
        avg_drawdown = portfolio_values['Drawdown'].mean()
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown
        } 