from data.stock_data import StockDataFetcher
from visualization.stock_visualizer import StockVisualizer
from analysis.technical_indicators import TechnicalIndicators
from analysis.portfolio import PortfolioAnalyzer
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def main():
    # Initialize our classes
    fetcher = StockDataFetcher()
    visualizer = StockVisualizer()
    indicators = TechnicalIndicators()
    portfolio = PortfolioAnalyzer(initial_investment=10000.0)

    # Example: Fetch data for a tech portfolio
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    period = '1y'
    
    # Get stock data
    stock_data = fetcher.get_multiple_stocks(symbols, period=period)
    
    # 1. Technical Analysis Example (using AAPL)
    aapl_data = stock_data['AAPL']
    
    # Calculate indicators
    sma_20 = indicators.calculate_sma(aapl_data, window=20)
    ema_20 = indicators.calculate_ema(aapl_data, window=20)
    rsi = indicators.calculate_rsi(aapl_data)
    macd, signal = indicators.calculate_macd(aapl_data)
    upper_band, middle_band, lower_band = indicators.calculate_bollinger_bands(aapl_data)
    
    # Create technical analysis chart
    fig = make_subplots(rows=3, cols=1, 
                       shared_xaxes=True,
                       vertical_spacing=0.05,
                       row_heights=[0.6, 0.2, 0.2])

    # Price and Moving Averages
    fig.add_trace(go.Candlestick(x=aapl_data.index,
                                open=aapl_data['Open'],
                                high=aapl_data['High'],
                                low=aapl_data['Low'],
                                close=aapl_data['Close'],
                                name='Price'),
                  row=1, col=1)
    
    fig.add_trace(go.Scatter(x=aapl_data.index, y=sma_20,
                            name='SMA 20',
                            line=dict(color='blue')),
                  row=1, col=1)
    
    fig.add_trace(go.Scatter(x=aapl_data.index, y=ema_20,
                            name='EMA 20',
                            line=dict(color='orange')),
                  row=1, col=1)
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(x=aapl_data.index, y=upper_band,
                            name='Upper BB',
                            line=dict(color='gray', dash='dash')),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=aapl_data.index, y=lower_band,
                            name='Lower BB',
                            line=dict(color='gray', dash='dash')),
                  row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=aapl_data.index, y=rsi,
                            name='RSI',
                            line=dict(color='purple')),
                  row=2, col=1)
    
    # Add RSI levels
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=aapl_data.index, y=macd,
                            name='MACD',
                            line=dict(color='blue')),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=aapl_data.index, y=signal,
                            name='Signal',
                            line=dict(color='orange')),
                  row=3, col=1)

    fig.update_layout(
        title='AAPL Technical Analysis',
        yaxis_title='Price',
        yaxis2_title='RSI',
        yaxis3_title='MACD',
        height=1000
    )

    pio.write_html(fig, 'aapl_technical_analysis.html')

    # 2. Portfolio Analysis Example
    # Define portfolio weights
    weights = {
        'AAPL': 0.3,
        'MSFT': 0.3,
        'GOOGL': 0.2,
        'AMZN': 0.2
    }
    
    # Calculate portfolio values
    portfolio_values = portfolio.calculate_portfolio_value(stock_data, weights)
    
    # Calculate portfolio metrics
    returns = portfolio.calculate_returns(portfolio_values)
    drawdown = portfolio.calculate_drawdown(portfolio_values)
    
    # Print portfolio metrics
    print("\nPortfolio Performance Metrics:")
    print(f"Total Return: {returns['total_return']:.2f}%")
    print(f"Annualized Return: {returns['annualized_return']:.2f}%")
    print(f"Volatility: {returns['volatility']:.2f}%")
    print(f"Sharpe Ratio: {returns['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {drawdown['max_drawdown']:.2f}%")
    print(f"Average Drawdown: {drawdown['avg_drawdown']:.2f}%")
    
    # Create portfolio performance chart
    portfolio_fig = go.Figure()
    
    # Add individual stock values
    for symbol in symbols:
        portfolio_fig.add_trace(
            go.Scatter(
                x=portfolio_values.index,
                y=portfolio_values[symbol],
                name=symbol,
                mode='lines'
            )
        )
    
    # Add total portfolio value
    portfolio_fig.add_trace(
        go.Scatter(
            x=portfolio_values.index,
            y=portfolio_values['Total'],
            name='Total Portfolio',
            line=dict(color='black', width=2)
        )
    )
    
    portfolio_fig.update_layout(
        title='Portfolio Performance',
        xaxis_title='Date',
        yaxis_title='Value ($)',
        height=600
    )
    
    pio.write_html(portfolio_fig, 'portfolio_performance.html')

if __name__ == "__main__":
    main() 