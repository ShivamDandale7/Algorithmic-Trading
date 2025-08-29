import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


df_data = pd.read_csv('nifty_Sarea_cal_5min.csv')
output_csv = df_data.copy()


class SupertrendAreaCalculator:
    def __init__(self):
        self.data = None
        self.supertrend1 = None
        self.supertrend2 = None
    
    def calculate_atr(self, high, low, close, period):
        """
        Calculate Average True Range (ATR)
        """
        # Calculate True Range
        tr_list = []
        for i in range(1, len(close)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr = max(tr1, tr2, tr3)
            tr_list.append(tr)
        
        # Add first TR as high-low
        tr_list.insert(0, high[0] - low[0])
        tr_array = np.array(tr_list)
        
        # Calculate ATR using Simple Moving Average
        atr = np.zeros(len(tr_array))
        atr[0] = tr_array[0]
        
        for i in range(1, len(tr_array)):
            if i < period:
                atr[i] = np.mean(tr_array[:i+1])
            else:
                atr[i] = np.mean(tr_array[i-period+1:i+1])
        
        return atr
    
    def calculate_supertrend(self, high, low, close, period, multiplier):
        """
        Calculate Supertrend indicator
        """
        # Calculate ATR (Average True Range)
        atr = self.calculate_atr(high, low, close, period)
        
        # Calculate HL2 (High + Low) / 2
        hl2 = (high + low) / 2
        
        # Calculate upper and lower bands
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # Initialize arrays
        final_upper_band = np.zeros(len(close))
        final_lower_band = np.zeros(len(close))
        supertrend = np.zeros(len(close))
        direction = np.ones(len(close))
        
        # Set initial values
        final_upper_band[0] = upper_band[0]
        final_lower_band[0] = lower_band[0]
        supertrend[0] = close[0]
        
        for i in range(1, len(close)):
            # Final Upper Band
            if upper_band[i] < final_upper_band[i-1] or close[i-1] > final_upper_band[i-1]:
                final_upper_band[i] = upper_band[i]
            else:
                final_upper_band[i] = final_upper_band[i-1]
            
            # Final Lower Band
            if lower_band[i] > final_lower_band[i-1] or close[i-1] < final_lower_band[i-1]:
                final_lower_band[i] = lower_band[i]
            else:
                final_lower_band[i] = final_lower_band[i-1]
            
            # Determine Supertrend direction and value
            if close[i] <= final_lower_band[i]:
                direction[i] = -1
                supertrend[i] = final_lower_band[i]
            elif close[i] >= final_upper_band[i]:
                direction[i] = 1
                supertrend[i] = final_upper_band[i]
            else:
                direction[i] = direction[i-1]
                if direction[i] == 1:
                    supertrend[i] = final_lower_band[i]
                else:
                    supertrend[i] = final_upper_band[i]
        
        return supertrend, direction
    
    def load_data(self, data_df):
        """
        Load OHLC data
        Expected columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        self.data = data_df.copy()
        return self
    
    def calculate_dual_supertrend(self, period1=21, multiplier1=1, period2=14, multiplier2=2):
        """
        Calculate two different Supertrend indicators
        """
        high = self.data['high'].values
        low = self.data['low'].values
        close = self.data['close'].values
        
        # Calculate first Supertrend
        self.supertrend1, _ = self.calculate_supertrend(high, low, close, period1, multiplier1)
        
        # Calculate second Supertrend
        self.supertrend2, _ = self.calculate_supertrend(high, low, close, period2, multiplier2)
        
        # Add to dataframe
        self.data['supertrend1'] = self.supertrend1
        self.data['supertrend2'] = self.supertrend2

        output_csv['supertrend1'] = self.data['supertrend1']
        output_csv['supertrend2'] = self.data['supertrend2']
        
        return self
    
    def calculate_area_between_supertrends(self, start_idx=None, end_idx=None):
        """
        Calculate area between two Supertrend lines
        Using trapezoidal rule for numerical integration
        """
        if self.supertrend1 is None or self.supertrend2 is None:
            raise ValueError("Please calculate Supertrends first using calculate_dual_supertrend()")
        
        # Set default boundaries if not provided
        if start_idx is None:
            start_idx = 0
        if end_idx is None:
            end_idx = len(self.data) - 1
        
        # Extract the segment
        st1_segment = self.supertrend1[start_idx:end_idx+1]
        st2_segment = self.supertrend2[start_idx:end_idx+1]
        
        # Calculate absolute difference between the two lines
        diff = np.abs(st1_segment - st2_segment)
        
        # Calculate area using trapezoidal rule
        # Each interval represents 5 minutes, so dx = 5/60 hours = 1/12 hours
        dx = 1  # Using 1 as unit interval (5-minute candles)
        area = np.trapz(diff, dx=dx)

        output_csv['area_betn_supertrend'] = area
        
        return {
            'total_area': area,
            'average_spread': np.mean(diff),
            'max_spread': np.max(diff),
            'min_spread': np.min(diff),
            'start_idx': start_idx,
            'end_idx': end_idx,
            'num_periods': len(diff)
        }
    
    def find_crossover_points(self):
        """
        Find points where the two Supertrend lines cross
        """
        if self.supertrend1 is None or self.supertrend2 is None:
            raise ValueError("Please calculate Supertrends first")
        
        # Calculate difference between supertrends
        diff = self.supertrend1 - self.supertrend2
        
        # Find sign changes (crossovers)
        sign_changes = np.diff(np.sign(diff))
        crossover_indices = np.where(sign_changes != 0)[0]
        
        crossover_points = []
        for idx in crossover_indices:
            crossover_points.append({
                'index': idx,
                'timestamp': self.data.iloc[idx]['timestamp'] if 'timestamp' in self.data.columns else idx,
                'supertrend1': self.supertrend1[idx],
                'supertrend2': self.supertrend2[idx],
                'close': self.data.iloc[idx]['close']
            })
        
        return crossover_points
    
    def plot_supertrends_with_area(self, start_idx=None, end_idx=None, figsize=(15, 8)):
        """
        Plot the chart with Supertrends and highlight the area between them
        """
        if self.supertrend1 is None or self.supertrend2 is None:
            raise ValueError("Please calculate Supertrends first")
        
        # Set default boundaries
        if start_idx is None:
            start_idx = 0
        if end_idx is None:
            end_idx = len(self.data) - 1
        
        # Create subplot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        
        # Plot data segment
        data_segment = self.data.iloc[start_idx:end_idx+1]
        x_range = range(len(data_segment))
        
        # Main chart
        ax1.plot(x_range, data_segment['close'], label='Close Price', color='black', linewidth=1)
        ax1.plot(x_range, self.supertrend1[start_idx:end_idx+1], label='Supertrend 1', color='red', linewidth=2)
        ax1.plot(x_range, self.supertrend2[start_idx:end_idx+1], label='Supertrend 2', color='green', linewidth=2)
        
        # Fill area between supertrends
        ax1.fill_between(x_range, 
                        self.supertrend1[start_idx:end_idx+1], 
                        self.supertrend2[start_idx:end_idx+1], 
                        alpha=0.3, color='blue', label='Area Between Supertrends')
        
        # Add vertical lines at boundaries
        ax1.axvline(x=0, color='black', linestyle='--', alpha=0.7, label='Start Boundary')
        ax1.axvline(x=len(data_segment)-1, color='black', linestyle='--', alpha=0.7, label='End Boundary')
        
        ax1.set_title('BankNifty with Supertrend Area Analysis')
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Spread chart
        spread = np.abs(self.supertrend1[start_idx:end_idx+1] - self.supertrend2[start_idx:end_idx+1])
        ax2.plot(x_range, spread, color='purple', linewidth=2, label='Spread')
        ax2.fill_between(x_range, spread, alpha=0.3, color='purple')
        ax2.set_title('Spread Between Supertrends')
        ax2.set_ylabel('Spread')
        ax2.set_xlabel('Time Periods')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        return fig

# Example usage and demonstration
def create_sample_data():
    """
    Create sample data for demonstration
    """
    np.random.seed(42)
    
    # Generate sample BankNifty-like data
    n_periods = 200
    initial_price = 57000
    
    # Generate price movements
    returns = np.random.normal(0, 0.002, n_periods)  # 0.2% volatility
    prices = [initial_price]
    
    for i in range(1, n_periods):
        price = prices[-1] * (1 + returns[i])
        prices.append(price)
    
    # Create OHLC data
    data = []
    for i in range(n_periods):
        base_price = prices[i]
        high = base_price * (1 + abs(np.random.normal(0, 0.001)))
        low = base_price * (1 - abs(np.random.normal(0, 0.001)))
        open_price = base_price + np.random.normal(0, 10)
        close_price = base_price
        
        data.append({
            'timestamp': pd.Timestamp('2024-07-01 09:15:00') + pd.Timedelta(minutes=5*i),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': np.random.randint(1000, 10000)
        })
    
    return pd.DataFrame(data)

# Example usage
if __name__ == "__main__":
    # Create sample data
    sample_data = pd.read_csv('nifty_Sarea_cal_5min.csv')
    
    # Initialize calculator
    calc = SupertrendAreaCalculator()
    
    # Load data and calculate supertrends
    calc.load_data(sample_data)
    calc.calculate_dual_supertrend(period1=10, multiplier1=3, period2=14, multiplier2=2)
    
    # Calculate area between specific boundaries (e.g., indices 50 to 150)
    area_result = calc.calculate_area_between_supertrends(start_idx=50, end_idx=150)

    # output csv 

    
    print("Area Calculation Results:")
    print(f"Total Area: {area_result['total_area']:.2f}")
    print(f"Average Spread: {area_result['average_spread']:.2f}")
    print(f"Max Spread: {area_result['max_spread']:.2f}")
    print(f"Min Spread: {area_result['min_spread']:.2f}")
    print(f"Number of Periods: {area_result['num_periods']}")
    
    # Find crossover points
    crossovers = calc.find_crossover_points()
    print(f"\nFound {len(crossovers)} crossover points")
    
    # Plot the results
    calc.plot_supertrends_with_area(start_idx=50, end_idx=150)

    output_csv.to_csv('output_area_betn_supertrend.csv')