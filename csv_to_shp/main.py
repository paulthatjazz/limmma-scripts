import argparse
import pandas as pd
import geopandas as gpd


def main(csv_file, shp_file, csv_id_by, shp_id_by):
    df = pd.read_csv(csv_file)
    shp = gpd.read_file(shp_file)

    # check for matches first
    matches = shp[shp[shp_id_by].isin(df[csv_id_by])]

    not_matches = df[~df[csv_id_by].isin(matches[shp_id_by])]
    not_matches_shp = shp[~shp[shp_id_by].isin(matches[shp_id_by])]

    if len(not_matches) > 0:
        print(f"Found {len(not_matches)} not matches in CSV")
        print(not_matches)
        print('Not matches will be ignored. Would you like to continue? (y/n)')
        answer = input()
        if answer != 'y':
            return
    if len(not_matches_shp) > 0:
        print(f"Found {len(not_matches_shp)} not matches in Shp")
        print(not_matches_shp)
        print('Not matches will be ignored. Would you like to continue? (y/n)')
        answer = input()
        if answer != 'y':
            return

    # Create a copy of the original shapefile to preserve it
    result_shp = shp.copy()
    
    # Get all CSV columns except the ID column
    csv_columns = [col for col in df.columns if col != csv_id_by]
    
    # Initialize all CSV columns in the result shapefile with NaN
    for col in csv_columns:
        result_shp[col] = float('nan')
    
    # Add CSV data to matching shapefile records
    for idx, row in df.iterrows():
        csv_id = row[csv_id_by]
        # Find matching records in shapefile
        matching_mask = result_shp[shp_id_by] == csv_id
        if matching_mask.any():
            # Add all CSV columns for matching records
            for col in csv_columns:
                result_shp.loc[matching_mask, col] = row[col]
    
    # Create output filename in a subfolder named after the shapefile
    import os
    shp_base_name = os.path.basename(shp_file).replace('.shp', '')
    output_filename = f"{shp_base_name}_with_csv_data.shp"
    output_dir = os.path.join(os.path.dirname(__file__), f"{shp_base_name}_with_csv_data")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, output_filename)
    
    # Save the new shapefile
    result_shp.to_file(output_file)
    print(f"New shapefile created: {output_file}")
    print(f"Added {len(csv_columns)} CSV columns to shapefile")
    print(f"Total records: {len(result_shp)}")
    
    # Show summary of matches
    matched_count = len(result_shp[result_shp[csv_columns[0]].notna()])
    print(f"Records with CSV data: {matched_count}")
    print(f"Records with NaN values: {len(result_shp) - matched_count}")

    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV to Shp")
    parser.add_argument("--csv_file", type=str, help="The CSV file to convert")
    parser.add_argument("--shp_file", type=str, help="The Shp file to create")
    parser.add_argument('--csv_id_by', type=str, help="The column to use as the ID")
    parser.add_argument('--shp_id_by', type=str, help="The property to use as the ID")
    args = parser.parse_args()
    main(args.csv_file, args.shp_file, args.csv_id_by, args.shp_id_by)