import pandas as pd
import os
import re
from pathlib import Path

def extract_year_from_filename(filename):
    """Extract year from filename using regex pattern"""
    # Look for 4-digit year in the filename
    year_match = re.search(r'(\d{4})', filename)
    if year_match:
        return year_match.group(1)
    return None

def combine_csv_files():
    """Combine all CSV files and restructure with years as columns, provinces as rows"""
    
    # Define paths
    csv_folder = Path("csvs")
    output_file = "rice_production_by_province_and_year.csv"
    
    # Check if csvs folder exists
    if not csv_folder.exists():
        print(f"Error: {csv_folder} folder not found!")
        return
    
    # Get all CSV files in the folder
    csv_files = list(csv_folder.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in the csvs folder!")
        return
    
    print(f"Found {len(csv_files)} CSV files to process...")
    
    # Dictionary to store data by year
    yearly_data = {}
    
    # Process each CSV file
    for csv_file in csv_files:
        print(f"Processing: {csv_file.name}")
        
        # Extract year from filename
        year = extract_year_from_filename(csv_file.name)
        
        if year is None:
            print(f"Warning: Could not extract year from {csv_file.name}, skipping...")
            continue
        
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Clean the data - remove rows with empty or invalid data
            # Remove rows where Provinsi is empty or contains notes
            df = df[df['Provinsi'].notna()]
            df = df[~df['Provinsi'].str.contains('Catatan|Kualitas|Indonesia', na=False)]
            df = df[df['Provinsi'] != '']
            
            # Select only the columns we need: Provinsi and Beras production
            # The Beras column is the second column (index 1)
            beras_column = df.columns[1]  # This should be the Beras production column
            df_clean = df[['Provinsi', beras_column]].copy()
            df_clean.columns = ['Provinsi', f'Beras (ton) {year}']
            
            yearly_data[year] = df_clean
            print(f"  - Added {len(df_clean)} provinces for year {year}")
            
        except Exception as e:
            print(f"Error processing {csv_file.name}: {str(e)}")
            continue
    
    if not yearly_data:
        print("No valid data found to combine!")
        return
    
    # Start with the first year's data
    years = sorted(yearly_data.keys())
    print(f"\nYears found: {years}")
    
    # Start with the first year
    combined_df = yearly_data[years[0]].copy()
    
    # Merge with other years
    for year in years[1:]:
        print(f"Merging data for year {year}...")
        combined_df = pd.merge(combined_df, yearly_data[year], on='Provinsi', how='outer')
    
    # Sort by province name
    combined_df = combined_df.sort_values('Provinsi')
    
    # Save to output file
    combined_df.to_csv(output_file, index=False)
    
    print(f"\nSuccessfully created pivot table with {len(combined_df)} provinces")
    print(f"Years covered: {years}")
    print(f"Output file: {output_file}")
    
    # Display first few rows
    print(f"\nFirst 5 rows of combined data:")
    print(combined_df.head())
    
    # Display column names
    print(f"\nColumn names:")
    for col in combined_df.columns:
        print(f"  - {col}")
    
    return combined_df

if __name__ == "__main__":
    print("Starting CSV combination process...")
    combined_data = combine_csv_files()
    print("Process completed!")
