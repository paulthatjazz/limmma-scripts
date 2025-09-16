# GeoPackage to Raster Converter

This script converts GeoPackage (.gpkg) files to TIFF raster files, creating separate rasters for each year and disaster category to avoid overlapping shapes.

## Features

- **Per-year per-category rasters**: Creates 3 rasters per year (one for each disaster type)
- **No overlapping shapes**: Each year is processed separately
- Converts disaster categories (Flood, Forest Fire, Landslide) to individual TIFF files
- Automatically handles coordinate reference systems (CRS)
- Configurable pixel resolution
- LZW compression to reduce file sizes
- Command-line interface with options
- Error handling and progress reporting

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

To convert the default `disaster_per_regency.gpkg` file with per-year per-category rasters:

```bash
python gkpg_to_raster.py
```

### Advanced Usage

```bash
python gkpg_to_raster.py <path_to_gpkg_file> [options]
```

#### Options

- `-o, --output`: Output directory for TIFF files (default: `rasters_by_year/` in same directory as input)
- `-r, --resolution`: Pixel resolution in degrees (default: 0.01)
- `-e, --exclude`: Columns to exclude from conversion (default: geometry, Year, KDPKAB)
- `--no-year-split`: Disable year splitting (use original overlapping method)

#### Examples

```bash
# Convert with per-year per-category rasters (default behavior)
python gkpg_to_raster.py disaster_per_regency.gpkg

# Convert with custom output directory
python gkpg_to_raster.py disaster_per_regency.gpkg -o output_rasters/

# Convert with higher resolution (smaller pixels)
python gkpg_to_raster.py disaster_per_regency.gpkg -r 0.005

# Disable year splitting (original overlapping method)
python gkpg_to_raster.py disaster_per_regency.gpkg --no-year-split
```

## Output

The script will create a `rasters_by_year/` directory (or your specified output directory) with subdirectories for each year:

```
rasters_by_year/
├── Year_2001/                 # Year 2001
│   ├── Num_Flood.tif
│   ├── Num_Forest_Fire.tif
│   └── Num_Land_Slide.tif
├── Year_2002/                 # Year 2002
│   ├── Num_Flood.tif
│   ├── Num_Forest_Fire.tif
│   └── Num_Land_Slide.tif
├── Year_2003/                 # Year 2003
│   ├── Num_Flood.tif
│   ├── Num_Forest_Fire.tif
│   └── Num_Land_Slide.tif
...
└── Year_2025/                 # Year 2025
    ├── Num_Flood.tif
    ├── Num_Forest_Fire.tif
    └── Num_Land_Slide.tif
```

Each TIFF file will have:
- Same coordinate reference system as the input GeoPackage
- Configurable pixel resolution
- LZW compression for smaller file sizes
- NoData values set to 0 for areas without features
- **No overlapping shapes** - each year is processed separately
- **Total output**: 75 rasters (25 years × 3 disaster categories)

## Data Structure

The `disaster_per_regency.gpkg` file contains:
- **12,850 features** representing Indonesian regencies
- **8 columns**: KDPKAB, Regency, Province, Year, Num_Flood, Num_Forest_Fire, Num_Land_Slide, geometry
- **CRS**: EPSG:4326 (WGS84)
- **Coverage**: Indonesian regencies with disaster data

## Notes

- The script automatically detects numeric columns suitable for rasterization
- Geometry columns are excluded by default
- Large GeoPackages may take several minutes to process
- Output rasters use the same extent as the input data
