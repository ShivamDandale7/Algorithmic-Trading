import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def analyze_nifty_drops(csv_file_path):
    """
    Analyze NIFTY50 data to find dates with significant drops (>1%)
    
    Parameters:
    csv_file_path (str): Path to the CSV file containing NIFTY50 OHLC data
    
    Returns:
    dict: Contains analysis results including dataframes and statistics
    """
    
    # Read the CSV file
    try:
        df = pd.read_csv(csv_file_path)
        print(f"Data loaded successfully. Shape: {df.shape}")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None
    
    # Display column names to help with identification
    print("\nColumn names in the dataset:")
    print(df.columns.tolist())
    
    # Common column name variations for NIFTY data
    date_cols = ['Date', 'date', 'DATE', 'Dates', 'Trading Date']
    close_cols = ['Close', 'close', 'CLOSE', 'Close Price', 'Closing Price']
    
    # Identify date and close columns
    date_col = None
    close_col = None
    
    for col in df.columns:
        if any(d in col for d in date_cols):
            date_col = col
            break
    
    for col in df.columns:
        if any(c in col for c in close_cols):
            close_col = col
            break
    
    if date_col is None or close_col is None:
        print("Please specify the correct column names:")
        print("Available columns:", df.columns.tolist())
        return None
    
    print(f"\nUsing columns - Date: '{date_col}', Close: '{close_col}'")
    
    # Prepare the data
    df_clean = df[[date_col, close_col]].copy()
    df_clean.columns = ['Date', 'Close']
    
    # Convert date column to datetime
    df_clean['Date'] = pd.to_datetime(df_clean['Date'])
    
    # Sort by date to ensure proper order
    df_clean = df_clean.sort_values('Date').reset_index(drop=True)
    
    # Calculate daily percentage change
    df_clean['Prev_Close'] = df_clean['Close'].shift(1)
    df_clean['Daily_Change'] = df_clean['Close'] - df_clean['Prev_Close']
    df_clean['Daily_Change_Pct'] = (df_clean['Daily_Change'] / df_clean['Prev_Close']) * 100
    
    # Filter for significant drops (>1% decrease)
    significant_drops = df_clean[df_clean['Daily_Change_Pct'] < -1.0].copy()
    
    # Add additional date information
    significant_drops['Day_of_Month'] = significant_drops['Date'].dt.day
    significant_drops['Month'] = significant_drops['Date'].dt.month
    significant_drops['Year'] = significant_drops['Date'].dt.year
    significant_drops['Weekday'] = significant_drops['Date'].dt.day_name()
    
    # Sort by percentage change (most significant drops first)
    significant_drops = significant_drops.sort_values('Daily_Change_Pct').reset_index(drop=True)
    
    print(f"\nFound {len(significant_drops)} trading days with drops greater than 1%")
    print(f"Date range: {df_clean['Date'].min().strftime('%Y-%m-%d')} to {df_clean['Date'].max().strftime('%Y-%m-%d')}")
    
    return {
        'full_data': df_clean,
        'significant_drops': significant_drops,
        'total_trading_days': len(df_clean) - 1,  # Exclude first day as it has no previous day
        'drop_days_count': len(significant_drops)
    }

def generate_insights(results):
    """Generate detailed insights from the analysis results"""
    
    if results is None:
        return
    
    drops_df = results['significant_drops']
    
    print("\n" + "="*60)
    print("DETAILED ANALYSIS RESULTS")
    print("="*60)
    
    # Basic statistics
    print(f"\nBASIC STATISTICS:")
    print(f"Total trading days analyzed: {results['total_trading_days']}")
    print(f"Days with drops >1%: {results['drop_days_count']}")
    print(f"Percentage of trading days: {(results['drop_days_count']/results['total_trading_days']*100):.2f}%")
    
    if len(drops_df) > 0:
        print(f"Average drop on significant drop days: {drops_df['Daily_Change_Pct'].mean():.2f}%")
        print(f"Largest single day drop: {drops_df['Daily_Change_Pct'].min():.2f}%")
        print(f"Smallest significant drop: {drops_df['Daily_Change_Pct'].max():.2f}%")
        
        # Top 10 worst drops
        print(f"\nTOP 10 WORST DROPS:")
        print("-" * 40)
        for i, row in drops_df.head(10).iterrows():
            print(f"{row['Date'].strftime('%Y-%m-%d')} ({row['Weekday'][:3]}): {row['Daily_Change_Pct']:.2f}%")
        
        # Day of month analysis
        print(f"\nDAY OF MONTH ANALYSIS:")
        print("-" * 40)
        day_counts = drops_df['Day_of_Month'].value_counts().sort_index()
        print("Most frequent days of month for significant drops:")
        for day, count in day_counts.head(10).items():
            print(f"Day {day}: {count} occurrences")
        
        # Monthly pattern
        print(f"\nMONTHLY PATTERN:")
        print("-" * 40)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_counts = drops_df['Month'].value_counts().sort_index()
        for month, count in month_counts.items():
            print(f"{month_names[month-1]}: {count} drops")
        
        # Weekday pattern
        print(f"\nWEEKDAY PATTERN:")
        print("-" * 40)
        weekday_counts = drops_df['Weekday'].value_counts()
        for day, count in weekday_counts.items():
            print(f"{day}: {count} drops")
        
        # Yearly breakdown
        print(f"\nYEARLY BREAKDOWN:")
        print("-" * 40)
        yearly_counts = drops_df['Year'].value_counts().sort_index()
        for year, count in yearly_counts.items():
            print(f"{year}: {count} drops")

def create_visualizations(results):
    """Create visualizations for the analysis"""
    
    if results is None or len(results['significant_drops']) == 0:
        print("No data available for visualization")
        return
    
    drops_df = results['significant_drops']
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('NIFTY50 Significant Drops Analysis (>1%)', fontsize=16, fontweight='bold')
    
    # 1. Day of month distribution
    day_counts = drops_df['Day_of_Month'].value_counts().sort_index()
    axes[0, 0].bar(day_counts.index, day_counts.values, color='red', alpha=0.7)
    axes[0, 0].set_title('Distribution by Day of Month')
    axes[0, 0].set_xlabel('Day of Month')
    axes[0, 0].set_ylabel('Number of Drops')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Monthly distribution
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_counts = drops_df['Month'].value_counts().sort_index()
    axes[0, 1].bar(range(1, 13), [month_counts.get(i, 0) for i in range(1, 13)], 
                   color='darkred', alpha=0.7)
    axes[0, 1].set_title('Distribution by Month')
    axes[0, 1].set_xlabel('Month')
    axes[0, 1].set_ylabel('Number of Drops')
    axes[0, 1].set_xticks(range(1, 13))
    axes[0, 1].set_xticklabels(month_names, rotation=45)
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Weekday distribution
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    weekday_counts = drops_df['Weekday'].value_counts()
    weekday_data = [weekday_counts.get(day, 0) for day in weekday_order]
    axes[1, 0].bar(weekday_order, weekday_data, color='maroon', alpha=0.7)
    axes[1, 0].set_title('Distribution by Weekday')
    axes[1, 0].set_xlabel('Weekday')
    axes[1, 0].set_ylabel('Number of Drops')
    axes[1, 0].tick_params(axis='x', rotation=45)
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Yearly distribution
    yearly_counts = drops_df['Year'].value_counts().sort_index()
    axes[1, 1].bar(yearly_counts.index, yearly_counts.values, color='crimson', alpha=0.7)
    axes[1, 1].set_title('Distribution by Year')
    axes[1, 1].set_xlabel('Year')
    axes[1, 1].set_ylabel('Number of Drops')
    axes[1, 1].tick_params(axis='x', rotation=45)
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    # Create a timeline plot
    plt.figure(figsize=(15, 8))
    plt.scatter(drops_df['Date'], drops_df['Daily_Change_Pct'], 
               c=drops_df['Daily_Change_Pct'], cmap='Reds', 
               s=50, alpha=0.7, edgecolors='black', linewidth=0.5)
    plt.colorbar(label='Drop Percentage (%)')
    plt.title('Timeline of Significant NIFTY50 Drops (>1%)', fontsize=14, fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Drop Percentage (%)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def save_results(results, output_file='nifty_significant_drops.csv'):
    """Save the results to a CSV file"""
    
    if results is None or len(results['significant_drops']) == 0:
        print("No results to save")
        return
    
    # Prepare data for saving
    save_df = results['significant_drops'][['Date', 'Close', 'Prev_Close', 
                                          'Daily_Change', 'Daily_Change_Pct', 
                                          'Day_of_Month', 'Month', 'Year', 'Weekday']].copy()
    
    # Format the data
    save_df['Date'] = save_df['Date'].dt.strftime('%Y-%m-%d')
    save_df['Close'] = save_df['Close'].round(2)
    save_df['Prev_Close'] = save_df['Prev_Close'].round(2)
    save_df['Daily_Change'] = save_df['Daily_Change'].round(2)
    save_df['Daily_Change_Pct'] = save_df['Daily_Change_Pct'].round(2)
    
    # Save to CSV
    save_df.to_csv(output_file, index=False)
    print(f"\nResults saved to '{output_file}'")
    print(f"Total records saved: {len(save_df)}")

# Main execution function
def main():
    """Main function to run the complete analysis"""
    
    print("NIFTY50 Significant Drop Analysis")
    print("=" * 40)
    
    # Specify your CSV file path here
    csv_file = "nifty_1d_data_3Y.csv"
    
    # If no path provided, use default name
    if not csv_file:
        csv_file = "nifty50_data.csv"
        print(f"Using default filename: {csv_file}")
    
    # Run the analysis
    results = analyze_nifty_drops(csv_file)
    
    if results is not None:
        # Generate insights
        generate_insights(results)
        
        # Create visualizations
        create_visualizations(results)
        
        # Save results
        save_results(results)
        
        # Return the results for further analysis if needed
        return results
    else:
        print("Analysis could not be completed. Please check your data file.")
        return None

# Run the analysis
if __name__ == "__main__":
    results = main()