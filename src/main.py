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
                # Add one day to end_date to ensure we get the latest data
                end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                data = yf.download(symbol, start=start_date, end=end_date_dt.strftime('%Y-%m-%d'))
            else:
                data = yf.download(symbol, period=period or '1mo')
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_previous_business_day(self, data: pd.DataFrame, current_date: datetime) -> datetime:
        """Get the previous business day from the actual trading data"""
        if data.empty or len(data) < 2:
            return None
            
        # Get all dates before the current date
        previous_dates = data.index[data.index < current_date]
        if len(previous_dates) == 0:
            return None
            
        # Return the most recent date that's not the current date
        return previous_dates[-1] if previous_dates[-1] != current_date else previous_dates[-2] if len(previous_dates) > 1 else None

    def calculate_statistics(self, data: pd.DataFrame, exchange: str) -> dict:
        """Calculate various statistics from the stock data"""
        if data.empty:
            return {}

        current = data.iloc[-1]
        current_date = current.name
        
        # Get previous business day from the data
        prev_business_day = self.get_previous_business_day(data, current_date)
        if prev_business_day is None:
            return {}
            
        # Get previous business day data
        previous = data.loc[prev_business_day]
        
        # Convert Series to scalar values
        current_close = current['Close'].item()
        previous_close = previous['Close'].item()
        first_close = data.iloc[0]['Close'].item()
        
        # Calculate returns
        daily_return = ((current_close - previous_close) / previous_close) * 100
        total_return = ((current_close - first_close) / first_close) * 100
        
        # Calculate volatility - convert to scalar value using iloc[0]
        volatility = data['Close'].pct_change().std() * 100
        volatility = float(volatility.iloc[0]) if isinstance(volatility, pd.Series) else float(volatility)
        
        # Calculate period statistics using iloc[0]
        period_high = float(data['High'].max().iloc[0]) if isinstance(data['High'].max(), pd.Series) else float(data['High'].max())
        period_low = float(data['Low'].min().iloc[0]) if isinstance(data['Low'].min(), pd.Series) else float(data['Low'].min())
        avg_volume = float(data['Volume'].mean().iloc[0]) if isinstance(data['Volume'].mean(), pd.Series) else float(data['Volume'].mean())
        
        # Extract values from pandas Series using item() for scalar values
        return {
            'current_price': round(float(current['Close'].item()), 2),
            'previous_close': round(float(previous['Close'].item()), 2),
            'open': round(float(current['Open'].item()), 2),
            'high': round(float(current['High'].item()), 2),
            'low': round(float(current['Low'].item()), 2),
            'volume': int(float(current['Volume'].item())),
            'daily_return': round(float(daily_return), 2),
            'total_return': round(float(total_return), 2),
            'volatility': round(volatility, 2),
            'period_high': round(period_high, 2),
            'period_low': round(period_low, 2),
            'avg_volume': int(avg_volume),
            # Previous business day statistics
            'prev_date': previous.name.strftime('%Y-%m-%d'),
            'prev_open': round(float(previous['Open'].item()), 2),
            'prev_high': round(float(previous['High'].item()), 2),
            'prev_low': round(float(previous['Low'].item()), 2),
            'prev_close': round(float(previous['Close'].item()), 2),
            'prev_volume': int(float(previous['Volume'].item()))
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

    def get_previous_business_day_data(self, symbol: str, current_date: str = None) -> dict:
        """
        Get previous business day data for a stock
        
        Args:
            symbol (str): Stock symbol
            current_date (str): Current date in YYYY-MM-DD format. If None, uses today's date
            
        Returns:
            dict: Dictionary containing stock name, previous business day data and record date
        """
        try:
            # Set current date if not provided
            if current_date is None:
                current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get data for the last 5 business days
            end_date = datetime.strptime(current_date, '%Y-%m-%d')
            start_date = end_date - timedelta(days=5)
            
            data = self.get_stock_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if data.empty:
                return {
                    'stock_name': symbol,
                    'previous_business_day': None,
                    'record_date': None
                }
            
            # Get previous business day
            prev_business_day = self.get_previous_business_day(data, end_date)
            
            if prev_business_day is None:
                return {
                    'stock_name': symbol,
                    'previous_business_day': None,
                    'record_date': None
                }
            
            # Get previous business day data
            prev_data = data.loc[prev_business_day]
            
            return {
                'stock_name': symbol,
                'previous_business_day': {
                    'open': round(float(prev_data['Open'].item()), 2),
                    'high': round(float(prev_data['High'].item()), 2),
                    'low': round(float(prev_data['Low'].item()), 2),
                    'close': round(float(prev_data['Close'].item()), 2),
                    'volume': int(float(prev_data['Volume'].item()))
                },
                'record_date': prev_business_day.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            return {
                'stock_name': symbol,
                'previous_business_day': None,
                'record_date': None
            }

    def get_stock_related_data(self, symbol: str) -> dict:
        """
        Get stock related data including previous business day information
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Dictionary containing stock related data
        """
        try:
            # Get data for the last 5 business days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)
            
            data = self.get_stock_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if data.empty:
                return {
                    'stock_name': symbol,
                    'previous_business_day_data': None,
                    'record_date': None
                }
            
            # Get previous business day
            prev_business_day = self.get_previous_business_day(data, end_date)
            
            if prev_business_day is None:
                return {
                    'stock_name': symbol,
                    'previous_business_day_data': None,
                    'record_date': None
                }
            
            # Get previous business day data
            prev_data = data.loc[prev_business_day]
            
            return {
                'stock_name': symbol,
                'previous_business_day_data': {
                    'open': round(float(prev_data['Open'].item()), 2),
                    'high': round(float(prev_data['High'].item()), 2),
                    'low': round(float(prev_data['Low'].item()), 2),
                    'close': round(float(prev_data['Close'].item()), 2),
                    'volume': int(float(prev_data['Volume'].item()))
                },
                'record_date': prev_business_day.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            return {
                'stock_name': symbol,
                'previous_business_day_data': None,
                'record_date': None
            }

    def sendDataToDatabase(self, symbol: str) -> dict:
        """
        Fetch and prepare stock data for database storage
        
        Args:
            symbol (str): Stock symbol (e.g., 'RELIANCE.NS' for NSE or 'RELIANCE.BO' for BSE)
            
        Returns:
            dict: Dictionary containing stock data ready for database storage with the following keys:
                - stock_name: Name of the stock
                - record_date: Previous business day date
                - open_price: Opening price
                - high_price: Highest price
                - low_price: Lowest price
                - close_price: Closing price
                - volume: Trading volume
                - created_at: Timestamp of data creation
        """
        try:
            # Step 1: Determine the exchange (NSE or BSE) from the symbol suffix
            # .NS indicates NSE, .BO indicates BSE
            exchange = 'NSE' if symbol.endswith('.NS') else 'BSE' if symbol.endswith('.BO') else 'NSE'
            
            # Step 2: Select the appropriate market calendar based on exchange
            # Each exchange has its own trading calendar with specific holidays and trading days
            calendar = self.nse_calendar if exchange == 'NSE' else self.bse_calendar
            
            # Step 3: Calculate the previous business day
            # Get current date and look back 5 days to ensure we find a trading day
            current_date = datetime.now().date()
            schedule = calendar.schedule(start_date=current_date - timedelta(days=5), end_date=current_date)
            
            # Step 4: Validate if we found any trading days
            # If no trading days found, return None as we can't proceed
            if schedule.empty:
                print(f"No trading days found for {exchange}")
                return None
                
            # Step 5: Find the most recent trading day before current date
            # This ensures we get the last actual trading day, not just the previous calendar day
            trading_days = schedule.index.date
            prev_business_day = max(day for day in trading_days if day < current_date)
            
            # Step 6: Fetch the stock data for the symbol
            # This gets the actual trading data including OHLCV (Open, High, Low, Close, Volume)
            stock_data = self.get_stock_related_data(symbol)
            
            # Step 7: Validate if we got valid stock data
            # If no data available, return None as we can't proceed
            if stock_data['previous_business_day_data'] is None:
                print(f"No data available for {symbol}")
                return None
                
            # Step 8: Prepare the database record
            # Structure the data in a format suitable for database storage
            db_data = {
                'stock_name': stock_data['stock_name'],  # Stock identifier
                'record_date': prev_business_day.strftime('%Y-%m-%d'),  # Previous business day in YYYY-MM-DD format
                'open_price': stock_data['previous_business_day_data']['open'],  # Opening price
                'high_price': stock_data['previous_business_day_data']['high'],  # Highest price
                'low_price': stock_data['previous_business_day_data']['low'],    # Lowest price
                'close_price': stock_data['previous_business_day_data']['close'], # Closing price
                'volume': stock_data['previous_business_day_data']['volume'],     # Trading volume
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')       # Current timestamp
            }
            
            # Step 9: Display the prepared data for verification
            # This helps in debugging and manual verification of the data
            print("\n" + "="*50)
            print(f"Data prepared for database storage - {symbol}")
            print("="*50)
            print(f"Stock Name: {db_data['stock_name']}")
            print(f"Record Date: {db_data['record_date']} (Previous Business Day)")
            print("\nPrevious Business Day Details:")
            print(f"Open Price: ₹{db_data['open_price']}")
            print(f"High Price: ₹{db_data['high_price']}")
            print(f"Low Price: ₹{db_data['low_price']}")
            print(f"Close Price: ₹{db_data['close_price']}")
            print(f"Volume: {db_data['volume']:,}")
            print(f"\nCreated At: {db_data['created_at']}")
            print("="*50)
            
            # Step 10: Return the prepared data
            # This data is ready to be inserted into the database
            return db_data
            
        except Exception as e:
            # Step 11: Error handling
            # Catch any unexpected errors and provide meaningful error message
            print(f"Error preparing data for database: {str(e)}")
            return None

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
                
                # Display database-ready data
                print(f"\n{'=' * 50}")
                print(f"Database-Ready Data for {symbol}")
                print(f"{'=' * 50}")
                db_data = analyzer.sendDataToDatabase(symbol)
                if db_data:
                    print("\nData successfully prepared for database storage")
                else:
                    print("\nFailed to prepare data for database storage")
                
            except Exception as e:
                print(f"\nError analyzing {symbol}: {str(e)}")
        
        print("\n" + "="*80)  # Add a separator between analyses
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