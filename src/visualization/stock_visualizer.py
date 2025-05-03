import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class StockVisualizer:
    def __init__(self):
        self.colors = {
            'up': '#26a69a',
            'down': '#ef5350',
            'volume': '#90a4ae'
        }

    def create_candlestick_chart(self, df: pd.DataFrame, title: str = "Stock Price") -> go.Figure:
        """
        Create a candlestick chart with volume.
        
        Args:
            df (pd.DataFrame): DataFrame containing OHLCV data
            title (str): Chart title
        
        Returns:
            go.Figure: Plotly figure object
        """
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1, 
                           shared_xaxes=True,
                           vertical_spacing=0.03,
                           row_heights=[0.7, 0.3])

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add volume bar chart
        colors = [self.colors['up'] if row['Close'] >= row['Open'] else self.colors['down'] 
                 for _, row in df.iterrows()]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            title=title,
            yaxis_title='Price',
            yaxis2_title='Volume',
            xaxis_rangeslider_visible=False,
            height=800
        )

        return fig

    def create_line_chart(self, df: pd.DataFrame, column: str = 'Close', 
                         title: str = "Stock Price") -> go.Figure:
        """
        Create a simple line chart.
        
        Args:
            df (pd.DataFrame): DataFrame containing the data
            column (str): Column to plot
            title (str): Chart title
        
        Returns:
            go.Figure: Plotly figure object
        """
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[column],
                mode='lines',
                name=column
            )
        )

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title=column,
            height=600
        )

        return fig

    def create_comparison_chart(self, dfs: dict, column: str = 'Close', 
                              title: str = "Stock Comparison") -> go.Figure:
        """
        Create a comparison chart for multiple stocks.
        
        Args:
            dfs (dict): Dictionary of DataFrames with symbols as keys
            column (str): Column to plot
            title (str): Chart title
        
        Returns:
            go.Figure: Plotly figure object
        """
        fig = go.Figure()

        for symbol, df in dfs.items():
            # Normalize the data to start at 100
            normalized_data = df[column] / df[column].iloc[0] * 100
            
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=normalized_data,
                    mode='lines',
                    name=symbol
                )
            )

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Normalized Price (Base=100)',
            height=600
        )

        return fig 