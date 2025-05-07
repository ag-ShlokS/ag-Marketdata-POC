import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.stock_data import StockData

def main():
    # Create StockData instance
    stock_data = StockData()
    
    # Fetch HDFC Bank data
    symbol = "HDFCBANK.NS"
    print(f"\nFetching data for {symbol}...")
    df = stock_data.fetch_stock_data(symbol, period="6mo")
    
    # Get latest price
    latest_price = stock_data.get_latest_price()
    print("\nLatest Price Information:")
    print(f"Date: {latest_price['date'].strftime('%Y-%m-%d')}")
    print(f"Open: ₹{latest_price['open']:.2f}")
    print(f"High: ₹{latest_price['high']:.2f}")
    print(f"Low: ₹{latest_price['low']:.2f}")
    print(f"Close: ₹{latest_price['close']:.2f}")
    print(f"Volume: {latest_price['volume']:,}")
    
    # Get price changes
    price_change = stock_data.get_price_change(days=1)  # Changed to 1 day to get previous business day
    print("\nPrevious Business Day Comparison:")
    print(f"Current Price: ₹{price_change['current_price']:.2f}")
    print(f"Previous Day Price: ₹{price_change['previous_price']:.2f}")
    print(f"Day Change: ₹{price_change['price_change']:.2f}")
    print(f"Day Change %: {price_change['price_change_pct']:.2f}%")
    
    # Get trading summary for more details
    summary = stock_data.get_trading_summary()
    print("\nTrading Summary:")
    print(f"52-Week High: ₹{summary['high_52w']:.2f}")
    print(f"52-Week Low: ₹{summary['low_52w']:.2f}")
    print(f"Average Volume: {summary['avg_volume']:,.0f}")

if __name__ == "__main__":
    main() 