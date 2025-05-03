from data.stock_data import StockDataFetcher
from visualization.stock_visualizer import StockVisualizer
import plotly.io as pio

def main():
    # Initialize our classes
    fetcher = StockDataFetcher()
    visualizer = StockVisualizer()

    # Example: Fetch data for Apple and Microsoft
    symbols = ['AAPL', 'MSFT']
    period = '1mo'
    
    # Get stock data
    stock_data = fetcher.get_multiple_stocks(symbols, period=period)
    
    # Create and save visualizations
    for symbol in symbols:
        # Create candlestick chart
        candlestick_fig = visualizer.create_candlestick_chart(
            stock_data[symbol],
            title=f"{symbol} Stock Price - Last {period}"
        )
        pio.write_html(candlestick_fig, f"{symbol}_candlestick.html")
        
        # Get and print stock info
        info = fetcher.get_stock_info(symbol)
        print(f"\n{symbol} Stock Information:")
        for key, value in info.items():
            print(f"{key}: {value}")

    # Create comparison chart
    comparison_fig = visualizer.create_comparison_chart(
        stock_data,
        title=f"Stock Comparison - Last {period}"
    )
    pio.write_html(comparison_fig, "stock_comparison.html")

if __name__ == "__main__":
    main() 