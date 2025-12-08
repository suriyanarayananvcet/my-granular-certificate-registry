"""
Generate sample hourly generation data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(total_mwh=1000.0, year=2024, source_type='solar', output_file='sample_data.csv'):
    """Generate 8760 hours of sample generation data"""
    
    start = datetime(year, 1, 1, 0, 0, 0)
    hours = []
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Base MWh per hour (uniform)
    base_mwh = total_mwh / 8760
    
    # Generate variations
    variations = np.random.normal(1.0, 0.2, 8760)
    variations = np.clip(variations, 0.1, 2.0)  # Keep within reasonable bounds
    
    for i in range(8760):
        ts = start + timedelta(hours=i)
        
        # Day of year factor (seasonal variation)
        day_of_year = ts.timetuple().tm_yday
        day_factor = 1.0 + 0.3 * np.sin(2 * np.pi * day_of_year / 365)
        
        # Hour of day factor (diurnal variation for solar)
        hour = ts.hour
        if source_type == 'solar':
            # Solar peaks during day
            if 6 <= hour <= 18:
                hour_factor = 0.3 + 0.7 * max(0, np.sin(np.pi * (hour - 6) / 12))
            else:
                hour_factor = 0.1
        else:
            # Other sources more uniform
            hour_factor = 0.8 + 0.2 * np.sin(2 * np.pi * hour / 24)
        
        # Calculate MWh for this hour
        mwh = base_mwh * variations[i] * day_factor * hour_factor
        
        hours.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'mwh': round(mwh, 6),
            'source_type': source_type
        })
    
    # Normalize to exact total
    df = pd.DataFrame(hours)
    current_total = df['mwh'].sum()
    scale_factor = total_mwh / current_total
    df['mwh'] = df['mwh'] * scale_factor
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"Generated {len(df)} hours of sample data")
    print(f"Total MWh: {df['mwh'].sum():.4f}")
    print(f"Average MWh per hour: {df['mwh'].mean():.4f}")
    print(f"Min MWh: {df['mwh'].min():.4f}")
    print(f"Max MWh: {df['mwh'].max():.4f}")
    print(f"Saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    # Generate sample data
    generate_sample_data(
        total_mwh=1000.0,
        year=2024,
        source_type='solar',
        output_file='sample_data.csv'
    )

