import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pandas_market_calendars as mcal

class StockAnalyzer:
    def __init__(self):
        self.data = None
        self.exchange_suffixes = {
            'NSE': '.NS',
            'BSE': '.BO'
        }
        # Initialize market calendars
        self.nse_calendar = mcal.get_calendar('NSE')
        self.bse_calendar = mcal.get_calendar('BSE')

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a stock symbol exists"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return bool(info.get('regularMarketPrice'))
        except:
            return False

    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None, 
                      period: str = None) -> pd.DataFrame:
        """Fetch stock data based on date range or period"""
        try:
            if start_date and end_date:
                data = yf.download(symbol, start=start_date, end=end_date)
            else:
                data = yf.download(symbol, period=period or '1mo')
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_previous_business_day(self, date: datetime, exchange: str) -> datetime:
        """Get the previous business day for the given exchange"""
        calendar = self.nse_calendar if exchange == 'NSE' else self.bse_calendar
        schedule = calendar.schedule(start_date=date - timedelta(days=10), end_date=date)
        valid_dates = schedule.index.tolist()
        valid_dates = [d for d in valid_dates if d < date]
        return valid_dates[-1] if valid_dates else None

    def calculate_statistics(self, data: pd.DataFrame, exchange: str) -> dict:
        """Calculate various statistics from the stock data"""
        if data.empty:
            return {}

        current = data.iloc[-1]
        current_date = current.name
        
        # Get previous business day
        prev_business_day = self.get_previous_business_day(current_date, exchange)
        if prev_business_day is None:
            return {}
            
        # Get previous business day data
        previous = data.loc[data.index <= prev_business_day].iloc[-1]
        
        # Calculate returns
        daily_return = ((current['Close'] - previous['Close']) / previous['Close']) * 100
        total_return = ((current['Close'] - data.iloc[0]['Close']) / data.iloc[0]['Close']) * 100
        
        # Calculate volatility
        volatility = data['Close'].pct_change().std() * 100
        
        # Extract values from pandas Series and round them
        return {
            'current_price': round(float(current['Close']), 2),
            'previous_close': round(float(previous['Close']), 2),
            'open': round(float(current['Open']), 2),
            'high': round(float(current['High']), 2),
            'low': round(float(current['Low']), 2),
            'volume': int(float(current['Volume'])),
            'daily_return': round(float(daily_return), 2),
            'total_return': round(float(total_return), 2),
            'volatility': round(float(volatility), 2),
            'period_high': round(float(data['High'].max()), 2),
            'period_low': round(float(data['Low'].min()), 2),
            'avg_volume': int(float(data['Volume'].mean())),
            # Previous business day statistics
            'prev_date': previous.name.strftime('%Y-%m-%d'),
            'prev_open': round(float(previous['Open']), 2),
            'prev_high': round(float(previous['High']), 2),
            'prev_low': round(float(previous['Low']), 2),
            'prev_close': round(float(previous['Close']), 2),
            'prev_volume': int(float(previous['Volume']))
        }

    def create_stock_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create an interactive stock chart"""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.03, row_heights=[0.7, 0.3])

        # Add candlestick chart
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'].astype(float),
            high=data['High'].astype(float),
            low=data['Low'].astype(float),
            close=data['Close'].astype(float),
            name='Price'
        ), row=1, col=1)

        # Add volume bars
        colors = ['red' if close < open else 'green' 
                 for close, open in zip(data['Close'].astype(float), data['Open'].astype(float))]
        
        fig.add_trace(go.Bar(
            x=data.index,
            y=data['Volume'].astype(float),
            name='Volume',
            marker_color=colors
        ), row=2, col=1)

        # Update layout
        fig.update_layout(
            title=f'{symbol} Stock Price Chart',
            yaxis_title='Price',
            yaxis2_title='Volume',
            xaxis_rangeslider_visible=False,
            height=800
        )

        return fig

def get_date_range() -> tuple:
    """Get date range from user input"""
    print("\nSelect date range:")
    print("1. Last week")
    print("2. Last month")
    print("3. Last 3 months")
    print("4. Last 6 months")
    print("5. Last year")
    print("6. Custom date range")
    print("7. Year to date")

    choice = input("\nEnter your choice (1-7): ")
    today = datetime.now()

    if choice == '6':
        while True:
            try:
                start = input("\nEnter start date (YYYY-MM-DD): ")
                end = input("Enter end date (YYYY-MM-DD) or press Enter for today: ")
                
                start_date = datetime.strptime(start, '%Y-%m-%d')
                end_date = datetime.strptime(end, '%Y-%m-%d') if end else today
                
                if start_date > end_date:
                    print("Start date cannot be after end date!")
                    continue
                    
                if end_date > today:
                    print("End date cannot be in the future!")
                    continue
                    
                return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            except ValueError:
                print("Invalid date format! Please use YYYY-MM-DD")
    
    elif choice == '7':
        return datetime(today.year, 1, 1).strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    
    else:
        days_map = {'1': 7, '2': 30, '3': 90, '4': 180, '5': 365}
        days = days_map.get(choice, 30)  # Default to 30 days if invalid choice
        start_date = today - timedelta(days=days)
        return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')

def main():
    analyzer = StockAnalyzer()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n=== Stock Market Analysis Tool ===")
        
        # Get exchange
        print("\nSelect Exchange:")
        print("1. NSE (National Stock Exchange)")
        print("2. BSE (Bombay Stock Exchange)")
        
        exchange_map = {'1': 'NSE', '2': 'BSE'}
        exchange_choice = input("\nEnter choice (1-2): ")
        exchange = exchange_map.get(exchange_choice, 'NSE')
        suffix = analyzer.exchange_suffixes[exchange]
        
        # Get stock symbols
        symbols_input = input("\nEnter stock symbols (comma-separated, e.g., RELIANCE,TCS,HDFCBANK): ")
        symbols = [s.strip().upper() + suffix for s in symbols_input.split(',') if s.strip()]
        
        # Validate symbols
        valid_symbols = []
        print("\nValidating symbols...")
        for symbol in symbols:
            if analyzer.validate_symbol(symbol):
                valid_symbols.append(symbol)
                print(f"✓ {symbol} is valid")
            else:
                print(f"✗ {symbol} is not valid")
        
        if not valid_symbols:
            print("\nNo valid symbols found!")
            if input("\nTry again? (y/n): ").lower() != 'y':
                break
            continue
        
        # Get date range
        start_date, end_date = get_date_range()
        
        # Fetch and analyze data
        print(f"\nFetching data from {start_date} to {end_date}...")
        
        for symbol in valid_symbols:
            try:
                # Get data
                data = analyzer.get_stock_data(symbol, start_date, end_date)
                if data.empty:
                    print(f"\nNo data available for {symbol}")
                    continue
                
                # Calculate statistics
                stats = analyzer.calculate_statistics(data, exchange)
                
                # Display results
                print(f"\n{'=' * 50}")
                print(f"Analysis for {symbol}")
                print(f"{'=' * 50}")
                print(f"Current Price: ₹{stats['current_price']}")
                print(f"Previous Close: ₹{stats['previous_close']}")
                print(f"\nToday's Trading:")
                print(f"Open: ₹{stats['open']}")
                print(f"High: ₹{stats['high']}")
                print(f"Low: ₹{stats['low']}")
                print(f"Volume: {stats['volume']:,}")
                print(f"\nPrevious Business Day ({stats['prev_date']}):")
                print(f"Open: ₹{stats['prev_open']}")
                print(f"High: ₹{stats['prev_high']}")
                print(f"Low: ₹{stats['prev_low']}")
                print(f"Close: ₹{stats['prev_close']}")
                print(f"Volume: {stats['prev_volume']:,}")
                print(f"\nPerformance:")
                print(f"Daily Return: {stats['daily_return']}%")
                print(f"Total Return: {stats['total_return']}%")
                print(f"Volatility: {stats['volatility']}%")
                print(f"\nPeriod Statistics ({start_date} to {end_date}):")
                print(f"Highest Price: ₹{stats['period_high']}")
                print(f"Lowest Price: ₹{stats['period_low']}")
                print(f"Average Daily Volume: {stats['avg_volume']:,}")
                
                # Create and save chart
                fig = analyzer.create_stock_chart(data, symbol)
                filename = f"{symbol}_chart.html"
                fig.write_html(filename)
                print(f"\nInteractive chart saved as {filename}")
                
            except Exception as e:
                print(f"\nError analyzing {symbol}: {str(e)}")
        
        if input("\nAnalyze more stocks? (y/n): ").lower() != 'y':
            break
    
    print("\nThank you for using the Stock Market Analysis Tool!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}") 