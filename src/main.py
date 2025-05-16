import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import pandas_market_calendars as mcal
import psycopg2
from psycopg2.extras import execute_values
from typing import Optional, List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalyzer:
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        self.data = None
        self.exchange_suffixes = {
            'NSE': '.NS',
            'BSE': '.BO'
        }
        # Initialize market calendars
        self.nse_calendar = mcal.get_calendar('NSE')
        self.bse_calendar = mcal.get_calendar('BSE')
        
        # Database configuration
        self.db_config = db_config or {
            'dbname': os.getenv('DB_NAME', 'Market_DataBase_25'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'rootroot'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        
        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database connection and create necessary tables"""
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # Check if stockCallActuals table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'stockCallActuals'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                if not table_exists:
                    logger.info("Creating stockCallActuals table...")
                    cur.execute("""
                        CREATE TABLE "stockCallActuals" (
                            id SERIAL PRIMARY KEY,
                            stock_call_id INTEGER NOT NULL,
                            openPrice DECIMAL(10,2) NOT NULL,
                            closePrice DECIMAL(10,2) NOT NULL,
                            highPrice DECIMAL(10,2) NOT NULL,
                            lowPrice DECIMAL(10,2) NOT NULL,
                            recordDate DATE NOT NULL,
                            hitOrMiss VARCHAR(10) DEFAULT 'HIT',
                            hitOrMissReason TEXT,
                            active BOOLEAN DEFAULT TRUE,
                            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(stock_call_id, recordDate)
                        );
                    """)
                else:
                    # Check if unique constraint exists
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conrelid = 'stockCallActuals'::regclass
                            AND conname = 'stockcallactuals_stock_call_id_recorddate_key'
                        );
                    """)
                    constraint_exists = cur.fetchone()[0]
                    
                    if not constraint_exists:
                        logger.info("Adding unique constraint to stockCallActuals table...")
                        cur.execute("""
                            ALTER TABLE "stockCallActuals"
                            ADD CONSTRAINT stockcallactuals_stock_call_id_recorddate_key
                            UNIQUE (stock_call_id, recordDate);
                        """)
                
                conn.commit()
                logger.info("Database initialization completed successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

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
                'open_price': stock_data['previous_business_day_data']['open'],  # Opening price
                'close_price': stock_data['previous_business_day_data']['close'], # Closing price
                'high_price': stock_data['previous_business_day_data']['high'],  # Highest price
                'low_price': stock_data['previous_business_day_data']['low'],    # Lowest price
                'record_date': prev_business_day.strftime('%Y-%m-%d'),  # Previous business day in YYYY-MM-DD format
               # 'volume': stock_data['previous_business_day_data']['volume'],     # Trading volume
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

    def get_stock_call_id(self, stock_name: str) -> Optional[int]:
        """
        Get the stock_call_id from stockCalls table for a given stock name
        
        Args:
            stock_name (str): Stock name (e.g., 'RELIANCE')
            
        Returns:
            Optional[int]: stock_call_id if found, None otherwise
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM stockCalls 
                    WHERE stockName = %s AND active = TRUE
                    ORDER BY createdAt DESC LIMIT 1
                """, (stock_name,))
                result = cur.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting stock_call_id: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def get_stock_call_date_range(self, stock_name: str) -> tuple:
        """
        Get the date range for a stock call from stockCalls and stockCallActuals tables
        
        Args:
            stock_name (str): Stock name (e.g., 'RELIANCE')
            
        Returns:
            tuple: (start_date, end_date) in YYYY-MM-DD format, or (None, None) if not found
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cur:
                # First, get the most recent active stock call
                cur.execute("""
                    SELECT id, calldate, stockname
                    FROM stockCalls
                    WHERE stockname = %s 
                    AND active = TRUE
                    ORDER BY calldate DESC
                    LIMIT 1
                """, (stock_name,))
                stock_call = cur.fetchone()
                
                if not stock_call:
                    logger.error(f"No active stock call found for {stock_name}")
                    return None, None
                
                stock_call_id, call_date, stock_name = stock_call
                
                if call_date is None:
                    logger.error(f"No call date found for {stock_name}")
                    return None, None
                
                # Now get the duration from stockCallActuals
                cur.execute("""
                    SELECT call_duration_in_days
                    FROM stockCallActuals
                    WHERE stock_call_id = %s
                    AND active = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (stock_call_id,))
                duration_result = cur.fetchone()
                
                # If no duration found in stockCallActuals, use default duration
                if not duration_result or duration_result[0] is None or duration_result[0] == 0:
                    logger.info(f"No valid duration found for {stock_name} in stockCallActuals, using default duration of 30 days")
                    duration = 30
                else:
                    duration = int(duration_result[0])
                    logger.info(f"Found duration of {duration} days in stockCallActuals")
                
                # Calculate end date by adding duration days to call date
                start_date = call_date
                end_date = start_date + timedelta(days=duration)
                
                # Format dates as strings
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                logger.info(f"Date range for {stock_name}:")
                logger.info(f"Start date (Call Date): {start_date_str}")
                logger.info(f"Duration: {duration} days")
                logger.info(f"End date: {end_date_str}")
                
                return start_date_str, end_date_str
                
        except Exception as e:
            logger.error(f"Error getting stock call date range: {str(e)}")
            return None, None
        finally:
            if conn:
                conn.close()

    def store_historical_data(self, stock_name: str, start_date: str = None, end_date: str = None) -> bool:
        """
        Store historical stock data in stockCallActuals table for the given date range
        
        Args:
            stock_name (str): Stock name (e.g., 'RELIANCE')
            start_date (str, optional): Start date in YYYY-MM-DD format. If None, uses callDate from stockCalls
            end_date (str, optional): End date in YYYY-MM-DD format. If None, uses current date
            
        Returns:
            bool: True if data was stored successfully, False otherwise
        """
        try:
            # If dates are not provided, get them from the database
            target_end_date = None
            if start_date is None or end_date is None:
                start_date, calculated_end_date = self.get_stock_call_date_range(stock_name)
                if start_date is None or calculated_end_date is None:
                    logger.error("Could not determine date range from database")
                    return False
                
                # Store the target end date before potentially modifying it
                target_end_date = calculated_end_date
                
                # Use current date as end date if calculated end date is in the future
                today = datetime.now().date()
                calculated_end_dt = datetime.strptime(calculated_end_date, '%Y-%m-%d').date()
                end_date = today.strftime('%Y-%m-%d') if calculated_end_dt > today else calculated_end_date
            
            # Validate dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            today = datetime.now()
            
            if start_dt > today:
                logger.error("Cannot fetch data for future start date")
                return False
            
            # If end date is in future, use today's date
            if end_dt > today:
                end_date = today.strftime('%Y-%m-%d')
                end_dt = today
            
            # Calculate actual duration in days
            duration_days = (end_dt.date() - start_dt.date()).days
            
            # Calculate remaining days using the target end date
            if target_end_date:
                target_end_dt = datetime.strptime(target_end_date, '%Y-%m-%d').date()
                total_duration = (target_end_dt - start_dt.date()).days
                remaining_days = (target_end_dt - today.date()).days if target_end_dt > today.date() else 0
                logger.info(f"Target end date: {target_end_date}")
                logger.info(f"Total duration: {total_duration} days")
                logger.info(f"Remaining days: {remaining_days} days")
            else:
                # If no target end date (custom date range), use the provided end date
                remaining_days = (end_dt.date() - today.date()).days if end_dt.date() > today.date() else 0
                logger.info(f"Using provided end date: {end_date}")
            
            logger.info(f"Attempting to store data for {stock_name} from {start_date} to {end_date}")
            logger.info(f"Duration in days: {duration_days}")
            
            # Get stock_call_id first
            stock_call_id = self.get_stock_call_id(stock_name)
            if not stock_call_id:
                logger.error(f"No active stock call found for {stock_name}")
                return False
            
            logger.info(f"Found stock_call_id: {stock_call_id}")
            
            # Update call_duration_in_days in stockCallActuals with remaining days
            try:
                conn = psycopg2.connect(**self.db_config)
                with conn.cursor() as cur:
                    # Update call_duration_in_days for all records of this stock call
                    cur.execute("""
                        UPDATE stockCallActuals 
                        SET call_duration_in_days = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE stock_call_id = %s
                        AND record_date >= %s
                    """, (remaining_days, stock_call_id, start_date))
                    conn.commit()
                    logger.info(f"Updated call_duration_in_days to {remaining_days} (remaining days) for stock_call_id {stock_call_id}")
            except Exception as e:
                logger.error(f"Error updating call_duration_in_days: {str(e)}")
                if conn:
                    conn.rollback()
            finally:
                if conn:
                    conn.close()
            
            # Add exchange suffix to stock name for fetching data
            symbol = f"{stock_name}.NS"  # Default to NSE
            
            # Get market calendar for business days
            calendar = self.nse_calendar
            schedule = calendar.schedule(start_date=start_dt.date(), end_date=end_dt.date())
            
            if schedule.empty:
                logger.error(f"No trading days found between {start_date} and {end_date}")
                return False
            
            # Get list of business days
            business_days = set(schedule.index.date)  # Convert to set for faster lookups
            
            # Fetch historical data
            logger.info("Fetching stock data...")
            data = self.get_stock_data(symbol, start_date, end_date)
            if data.empty:
                logger.error(f"No data available for {stock_name} between {start_date} and {end_date}")
                return False
            
            # Filter data to only include business days
            business_day_data = []
            for date, row in data.iterrows():
                if date.date() in business_days:
                    business_day_data.append((date, row))
            
            if not business_day_data:
                logger.error(f"No business day data available for {stock_name} between {start_date} and {end_date}")
                return False
            
            # Prepare data for database insertion
            records = []
            for date, row in business_day_data:
                # Calculate hit_or_miss based on your business logic
                hit_or_miss = 'HIT'  # or 'MISS' based on your criteria
                hit_or_miss_reason = None  # Add your reason if needed
                
                # Calculate remaining days for this specific record
                if target_end_date:
                    record_remaining_days = (target_end_dt - date.date()).days if target_end_dt > date.date() else 0
                else:
                    record_remaining_days = remaining_days
                
                record = (
                    stock_call_id,
                    float(row['Open'].item()),
                    float(row['Close'].item()),
                    float(row['High'].item()),
                    float(row['Low'].item()),
                    date.strftime('%Y-%m-%d'),
                    hit_or_miss,
                    hit_or_miss_reason,
                    True,  # active
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # created_at
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # updated_at
                    record_remaining_days  # Store remaining days for this specific record
                )
                records.append(record)
            
            logger.info(f"Preparing to store {len(records)} business day records in database...")

            # Connect to database and insert data
            try:
                conn = psycopg2.connect(**self.db_config)
                with conn.cursor() as cur:
                    # Use execute_values for efficient bulk insertion
                    execute_values(cur, """
                        INSERT INTO stockCallActuals 
                        (stock_call_id, open_price, close_price, high_price, low_price, 
                        record_date, hit_or_miss, hit_or_miss_reason, active, created_at, updated_at, call_duration_in_days)
                        VALUES %s
                        ON CONFLICT (stock_call_id, record_date) 
                        DO UPDATE SET
                            open_price = EXCLUDED.open_price,
                            close_price = EXCLUDED.close_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            hit_or_miss = EXCLUDED.hit_or_miss,
                            hit_or_miss_reason = EXCLUDED.hit_or_miss_reason,
                            active = EXCLUDED.active,
                            updated_at = EXCLUDED.updated_at,
                            call_duration_in_days = EXCLUDED.call_duration_in_days
                    """, records)
                
                conn.commit()
                logger.info(f"Successfully stored {len(records)} business day records for {stock_name}")
                return True

            except Exception as e:
                logger.error(f"Error during database operation: {str(e)}")
                if conn:
                    conn.rollback()
                return False
            finally:
                if conn:
                    conn.close()

        except Exception as e:
            logger.error(f"Unexpected error storing historical data for {stock_name}: {str(e)}")
            return False

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
        print("\n1. Analyze Stock Data")
        print("2. Store Historical Data")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
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
        
        elif choice == '2':
            # Get stock name
            stock_name = input("\nEnter stock name (e.g., RELIANCE): ").strip().upper()
            
            # Ask if user wants to use custom date range
            use_custom_dates = input("\nUse custom date range? (y/n): ").lower() == 'y'
            
            if use_custom_dates:
                # Get custom date range
                print("\nEnter date range for historical data:")
                start_date = input("Start date (YYYY-MM-DD): ")
                end_date = input("End date (YYYY-MM-DD) or press Enter for today: ")
                
                if not end_date:
                    end_date = datetime.now().strftime('%Y-%m-%d')
                
                # Store historical data with custom dates
                success = analyzer.store_historical_data(stock_name, start_date, end_date)
            else:
                # Store historical data using dates from database
                success = analyzer.store_historical_data(stock_name)
            
            if success:
                print(f"\nSuccessfully stored historical data for {stock_name}")
            else:
                print(f"\nFailed to store historical data for {stock_name}")
        
        elif choice == '3':
            break
        else:
            print("\nInvalid choice! Please try again.")
    
    print("\nThank you for using the Stock Market Analysis Tool!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {str(e)}") 