#!/usr/bin/env python3
"""
Convert GeoPackage layers to TIFF raster files.

This script reads a GeoPackage file and converts each attribute layer
to a separate TIFF raster file using rasterio and geopandas.
"""

import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_bounds
import numpy as np
import os
import sys
from pathlib import Path
import argparse


def get_gpkg_layers(gpkg_path):
    """
    Get all layers from a GeoPackage file.
    
    Args:
        gpkg_path (str): Path to the GeoPackage file
        
    Returns:
        list: List of layer names
    """
    try:
        # Read the main layer
        gdf = gpd.read_file(gpkg_path)
        print(f"Found main layer with {len(gdf)} features")
        print(f"Columns: {gdf.columns.tolist()}")
        print(f"CRS: {gdf.crs}")
        return gdf
    except Exception as e:
        print(f"Error reading GeoPackage: {e}")
        return None


def create_raster_from_layer(gdf, column_name, output_path, resolution=0.01):
    """
    Convert a GeoDataFrame column to a TIFF raster.
    
    Args:
        gdf (GeoDataFrame): Input GeoDataFrame
        column_name (str): Name of the column to rasterize
        output_path (str): Output TIFF file path
        resolution (float): Pixel resolution in degrees
    """
    try:
        # Get bounds of the entire dataset
        bounds = gdf.total_bounds
        minx, miny, maxx, maxy = bounds
        
        # Calculate raster dimensions
        width = int((maxx - minx) / resolution)
        height = int((maxy - miny) / resolution)
        
        # Create transform
        transform = from_bounds(minx, miny, maxx, maxy, width, height)
        
        # Prepare geometries and values for rasterization
        geometries = gdf.geometry
        values = gdf[column_name].fillna(0)  # Fill NaN values with 0
        
        # Rasterize the geometries
        raster = rasterize(
            zip(geometries, values),
            out_shape=(height, width),
            transform=transform,
            fill=0,  # Fill value for areas without data
            dtype=rasterio.float64
        )
        
        # Write the raster
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=rasterio.float64,
            crs=gdf.crs,
            transform=transform,
            compress='lzw'  # Add compression to reduce file size
        ) as dst:
            dst.write(raster, 1)
            
        print(f"Created raster: {output_path}")
        print(f"  Size: {width}x{height} pixels")
        print(f"  Resolution: {resolution} degrees")
        print(f"  Value range: {np.nanmin(raster):.2f} to {np.nanmax(raster):.2f}")
        
    except Exception as e:
        print(f"Error creating raster for {column_name}: {e}")


def create_year_groups(gdf, num_groups=3):
    """
    Split years into groups for separate raster creation.
    
    Args:
        gdf (GeoDataFrame): Input GeoDataFrame with Year column
        num_groups (int): Number of year groups to create
        
    Returns:
        list: List of tuples (group_name, year_range, gdf_subset)
    """
    years = sorted(gdf['Year'].unique())
    print(f"Found {len(years)} unique years: {years[0]} - {years[-1]}")
    
    # Calculate years per group
    years_per_group = len(years) // num_groups
    remainder = len(years) % num_groups
    
    year_groups = []
    start_idx = 0
    
    for i in range(num_groups):
        # Add one extra year to first few groups if there's a remainder
        group_size = years_per_group + (1 if i < remainder else 0)
        end_idx = start_idx + group_size
        
        group_years = years[start_idx:end_idx]
        group_name = f"Period_{group_years[0]}_{group_years[-1]}"
        
        # Filter data for this year group
        gdf_subset = gdf[gdf['Year'].isin(group_years)].copy()
        
        year_groups.append((group_name, group_years, gdf_subset))
        print(f"  {group_name}: {len(group_years)} years, {len(gdf_subset)} features")
        
        start_idx = end_idx
    
    return year_groups


def convert_gpkg_to_rasters_by_year(gpkg_path, output_dir=None, resolution=0.01, exclude_columns=None):
    """
    Convert GeoPackage to TIFF rasters, creating separate rasters for each year and disaster category.
    
    Args:
        gpkg_path (str): Path to the GeoPackage file
        output_dir (str): Output directory for TIFF files
        resolution (float): Pixel resolution in degrees
        exclude_columns (list): Columns to exclude from conversion
    """
    if exclude_columns is None:
        exclude_columns = ['geometry', 'Year', 'KDPKAB']
    
    # Create output directory
    if output_dir is None:
        output_dir = Path(gpkg_path).parent / "rasters_by_year"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Read the GeoPackage
    print(f"Reading GeoPackage: {gpkg_path}")
    gdf = get_gpkg_layers(gpkg_path)
    
    if gdf is None:
        print("Failed to read GeoPackage")
        return
    
    # Get unique years
    years = sorted(gdf['Year'].unique())
    print(f"\nFound {len(years)} unique years: {years[0]} - {years[-1]}")
    
    # Get disaster category columns (excluding geometry, Year, and other non-disaster columns)
    disaster_columns = [col for col in gdf.columns if col.startswith('Num_')]
    print(f"\nFound {len(disaster_columns)} disaster categories:")
    for col in disaster_columns:
        print(f"  - {col}")
    
    # Convert each disaster category to a raster for each year
    total_rasters = len(years) * len(disaster_columns)
    current_raster = 0
    
    for year in years:
        print(f"\n=== Processing Year {year} ===")
        year_dir = output_dir / f"Year_{year}"
        year_dir.mkdir(exist_ok=True)
        
        # Filter data for this year
        gdf_year = gdf[gdf['Year'] == year].copy()
        print(f"  Features for {year}: {len(gdf_year)}")
        
        for column in disaster_columns:
            current_raster += 1
            output_path = year_dir / f"{column}.tif"
            print(f"  [{current_raster}/{total_rasters}] Converting {column} for {year}...")
            create_raster_from_layer(gdf_year, column, str(output_path), resolution)
    
    print(f"\nConversion complete! Rasters saved to: {output_dir}")
    print(f"Created {total_rasters} rasters ({len(years)} years × {len(disaster_columns)} categories)")
    print("Each year has its own subdirectory with 3 disaster category rasters.")


def convert_gpkg_to_rasters(gpkg_path, output_dir=None, resolution=0.01, exclude_columns=None):
    """
    Convert all suitable columns in a GeoPackage to TIFF rasters.
    
    Args:
        gpkg_path (str): Path to the GeoPackage file
        output_dir (str): Output directory for TIFF files
        resolution (float): Pixel resolution in degrees
        exclude_columns (list): Columns to exclude from conversion
    """
    if exclude_columns is None:
        exclude_columns = ['geometry']
    
    # Create output directory
    if output_dir is None:
        output_dir = Path(gpkg_path).parent / "rasters"
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Read the GeoPackage
    print(f"Reading GeoPackage: {gpkg_path}")
    gdf = get_gpkg_layers(gpkg_path)
    
    if gdf is None:
        print("Failed to read GeoPackage")
        return
    
    # Get numeric columns (excluding geometry)
    numeric_columns = gdf.select_dtypes(include=[np.number]).columns.tolist()
    numeric_columns = [col for col in numeric_columns if col not in exclude_columns]
    
    print(f"\nFound {len(numeric_columns)} numeric columns to convert:")
    for col in numeric_columns:
        print(f"  - {col}")
    
    # Convert each numeric column to a raster
    for column in numeric_columns:
        output_path = output_dir / f"{column}.tif"
        print(f"\nConverting {column} to raster...")
        create_raster_from_layer(gdf, column, str(output_path), resolution)
    
    print(f"\nConversion complete! Rasters saved to: {output_dir}")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Convert GeoPackage layers to TIFF raster files"
    )
    parser.add_argument(
        "gpkg_path",
        help="Path to the GeoPackage file"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for TIFF files (default: rasters_by_year/ in same directory as input)"
    )
    parser.add_argument(
        "-r", "--resolution",
        type=float,
        default=0.01,
        help="Pixel resolution in degrees (default: 0.01)"
    )
    parser.add_argument(
        "-e", "--exclude",
        nargs="*",
        default=["geometry", "Year"],
        help="Columns to exclude from conversion (default: geometry, Year)"
    )
    parser.add_argument(
        "--no-year-split",
        action="store_true",
        help="Disable year splitting (use original overlapping method)"
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.gpkg_path):
        print(f"Error: File {args.gpkg_path} not found")
        sys.exit(1)
    
    # Convert the GeoPackage
    if args.no_year_split:
        convert_gpkg_to_rasters(
            args.gpkg_path,
            args.output,
            args.resolution,
            args.exclude
        )
    else:
        convert_gpkg_to_rasters_by_year(
            args.gpkg_path,
            args.output,
            args.resolution,
            args.exclude
        )


if __name__ == "__main__":
    # If run directly without arguments, use the disaster_per_regency.gpkg file
    if len(sys.argv) == 1:
        gpkg_file = "disaster_per_regency.gpkg"
        if os.path.exists(gpkg_file):
            print("No arguments provided, using default file: disaster_per_regency.gpkg")
            print("Creating separate rasters for each year and disaster category...")
            convert_gpkg_to_rasters_by_year(gpkg_file)
        else:
            print("Error: disaster_per_regency.gpkg not found in current directory")
            print("Usage: python gkpg_to_raster.py <path_to_gpkg_file>")
            sys.exit(1)
    else:
        main()