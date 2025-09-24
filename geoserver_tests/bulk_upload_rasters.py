#!/usr/bin/env python3
"""
Bulk Upload Raster Files to GeoServer
=====================================

This script uploads all raster files from the rasters_by_year folder
to GeoServer with the naming schema: {disaster_type}_{year}

Example:
- Num_Forest_Fire.tif from Year_2001 -> fire_2001
- Num_Flood.tif from Year_2002 -> flood_2002
- Num_Land_Slide.tif from Year_2003 -> landslide_2003
"""

import os
import re
import requests
import json
from geo.Geoserver import Geoserver

# GeoServer configuration
creds = {
    "url": "https://landscapes.wearepal.ai/geoserver/",
    "username": "admin",
    "password": "docker stack rm landscapes"
}

# Initialize GeoServer connection
gs = Geoserver(creds["url"], username=creds["username"], password=creds["password"])

def get_disaster_type_from_filename(filename):
    """Extract disaster type from filename"""
    filename_lower = filename.lower()
    
    if 'forest_fire' in filename_lower or 'fire' in filename_lower:
        return 'fire'
    elif 'flood' in filename_lower:
        return 'flood'
    elif 'land_slide' in filename_lower or 'landslide' in filename_lower:
        return 'landslide'
    else:
        return 'unknown'

def get_year_from_folder(folder_name):
    """Extract year from folder name (e.g., Year_2001 -> 2001)"""
    match = re.search(r'Year_(\d{4})', folder_name)
    if match:
        return match.group(1)
    return None

def create_coverage_layer_from_store(workspace, store_name, layer_name, disaster_type, year):
    """Create a coverage layer from an existing coverage store"""
    
    coverage_url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores/{store_name}/coverages"
    
    coverage_config = {
        "coverage": {
            "name": layer_name,
            "title": f"{disaster_type.title()} Data for {year}",
            "description": f"{disaster_type.title()} coverage data for year {year}",
            "enabled": True,
            "store": {
                "@class": "coverageStore",
                "name": store_name
            },
            "namespace": {
                "@class": "namespace",
                "name": workspace
            }
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(
        coverage_url,
        data=json.dumps(coverage_config),
        headers=headers,
        auth=(creds['username'], creds['password'])
    )
    
    return response

def upload_raster_file(file_path, disaster_type, year, workspace='ind'):
    """Upload a single raster file and create coverage store + layer"""
    
    # Create naming schema: {disaster_type}_{year}
    store_name = f"{disaster_type}_{year}"
    layer_name = f"{disaster_type}_{year}_layer"
    
    print(f"\n📁 Processing: {os.path.basename(file_path)}")
    print(f"   Disaster Type: {disaster_type}")
    print(f"   Year: {year}")
    print(f"   Store Name: {store_name}")
    print(f"   Layer Name: {layer_name}")
    
    try:
        # Step 1: Upload file and create coverage store
        print(f"   🔄 Uploading file...")
        gs.create_coveragestore(
            layer_name=store_name,
            workspace=workspace,
            path=file_path
        )
        print(f"   ✅ Coverage store '{store_name}' created successfully!")
        
        # Step 2: Create layer from coverage store
        print(f"   🔄 Creating layer...")
        layer_response = create_coverage_layer_from_store(
            workspace, store_name, layer_name, disaster_type, year
        )
        
        if layer_response.status_code == 201:
            print(f"   ✅ Layer '{layer_name}' created successfully!")
            return True, store_name, layer_name
        else:
            print(f"   ❌ Failed to create layer. Status: {layer_response.status_code}")
            print(f"   Response: {layer_response.text}")
            return False, store_name, None
            
    except Exception as e:
        print(f"   ❌ Error processing file: {e}")
        return False, store_name, None

def main():
    """Main function to process all raster files"""
    
    print("=" * 60)
    print("🌍 BULK UPLOAD RASTER FILES TO GEOSERVER")
    print("=" * 60)
    
    # Define the path to rasters_by_year folder
    rasters_folder = "../gpkg_to_raster/rasters_by_year"
    
    if not os.path.exists(rasters_folder):
        print(f"❌ Error: Rasters folder not found: {rasters_folder}")
        return
    
    print(f"📂 Scanning folder: {rasters_folder}")
    
    # Track results
    successful_uploads = []
    failed_uploads = []
    
    # Walk through all year folders
    for year_folder in os.listdir(rasters_folder):
        year_path = os.path.join(rasters_folder, year_folder)
        
        if not os.path.isdir(year_path):
            continue
            
        # Extract year from folder name
        year = get_year_from_folder(year_folder)
        if not year:
            print(f"⚠️  Skipping folder (no year found): {year_folder}")
            continue
            
        print(f"\n📅 Processing Year: {year}")
        print("-" * 40)
        
        # Process all .tif files in this year folder
        for filename in os.listdir(year_path):
            if filename.lower().endswith(('.tif', '.tiff', '.geotiff')):
                file_path = os.path.join(year_path, filename)
                
                # Extract disaster type from filename
                disaster_type = get_disaster_type_from_filename(filename)
                
                if disaster_type == 'unknown':
                    print(f"⚠️  Skipping file (unknown disaster type): {filename}")
                    continue
                
                # Upload the file
                success, store_name, layer_name = upload_raster_file(
                    file_path, disaster_type, year
                )
                
                if success:
                    successful_uploads.append({
                        'file': filename,
                        'year': year,
                        'disaster_type': disaster_type,
                        'store_name': store_name,
                        'layer_name': layer_name
                    })
                else:
                    failed_uploads.append({
                        'file': filename,
                        'year': year,
                        'disaster_type': disaster_type,
                        'store_name': store_name
                    })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    
    print(f"✅ Successful uploads: {len(successful_uploads)}")
    print(f"❌ Failed uploads: {len(failed_uploads)}")
    
    if successful_uploads:
        print(f"\n🎉 Successfully uploaded layers:")
        for item in successful_uploads:
            print(f"   • {item['disaster_type']}_{item['year']} ({item['file']})")
    
    if failed_uploads:
        print(f"\n💥 Failed uploads:")
        for item in failed_uploads:
            print(f"   • {item['disaster_type']}_{item['year']} ({item['file']})")
    
    # List all available layers
    print(f"\n" + "=" * 60)
    print("📋 ALL AVAILABLE LAYERS")
    print("=" * 60)
    
    try:
        layers_url = f"{creds['url']}rest/layers.json"
        layers_response = requests.get(layers_url, auth=(creds['username'], creds['password']))
        
        if layers_response.status_code == 200:
            layers_data = layers_response.json()
            disaster_layers = []
            
            for layer in layers_data.get('layers', {}).get('layer', []):
                layer_name = layer.get('name', 'Unknown')
                if 'ind:' in layer_name and any(disaster in layer_name.lower() for disaster in ['fire', 'flood', 'landslide']):
                    disaster_layers.append(layer_name)
            
            if disaster_layers:
                print("Disaster-related layers in 'ind' workspace:")
                for layer in sorted(disaster_layers):
                    print(f"   • {layer}")
            else:
                print("No disaster-related layers found.")
        else:
            print(f"Could not retrieve layers list. Status: {layers_response.status_code}")
            
    except Exception as e:
        print(f"Error retrieving layers: {e}")
    
    print(f"\n🌐 Access your layers at: {creds['url']}web/")
    print("=" * 60)

if __name__ == "__main__":
    main()
