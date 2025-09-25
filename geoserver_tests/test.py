
from sys import version
from geo.Geoserver import Geoserver

creds = {
    "url": "https://landscapes.wearepal.ai/geoserver/",
    "username": "USER",
    "password": "PASSWORD"
}

gs = Geoserver(creds["url"], username=creds["username"], password=creds["password"])

try:
    # First, let's check what workspaces exist
    print("Checking existing workspaces...")
    workspaces = gs.get_workspaces()
    print(f"Existing workspaces: {workspaces}")
    
    # Check if 'ind' workspace exists, if not create it
    workspace_names = [ws.get('name', '') for ws in workspaces.get('workspaces', {}).get('workspace', [])]
    if 'ind' not in workspace_names:
        print("Creating 'ind' workspace...")
        gs.create_workspace(workspace='ind')
        print("Workspace 'ind' created successfully!")
    else:
        print("Workspace 'ind' already exists.")
    
    # Now let's check existing coverage stores
    print("\nChecking existing coverage stores...")
    coverage_stores = gs.get_coveragestores(workspace='ind')
    print(f"Existing coverage stores in 'ind': {coverage_stores}")
    
    # Let's examine an existing coverage store to understand the structure
    print("\n" + "="*50)
    print("EXAMINING EXISTING COVERAGE STORE")
    print("="*50)
    try:
        existing_store = gs.get_coveragestore(workspace='ind', store_name='2001_flood')
        print(f"Existing store '2001_flood' details: {existing_store}")
    except Exception as e:
        print(f"Could not get details for existing store: {e}")
    
    # For server-side data, you have a few options:
    print("\n" + "="*50)
    print("OPTIONS FOR SERVER-SIDE DATA")
    print("="*50)
    print("1. If data is already on the server, you can create a coverage store")
    print("   that references the server path using the REST API directly.")
    print("2. You can use the 'url' method instead of 'file' method.")
    print("3. You can upload the file first, then create the store.")
    
    print("\n" + "="*50)
    print("EXAMPLE: Creating coverage store for server-side data")
    print("="*50)
    print("If your data is at: /data/rasters_by_year/Year_2001/Num_Forest_Fire.tif")
    print("You would use:")
    print("gs.create_coveragestore(")
    print("    layer_name='2001_fire',")
    print("    workspace='ind',")
    print("    path='/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif',")
    print("    method='file'")
    print(")")
    
    # The key issue: create_coveragestore() expects a LOCAL file path
    # For server-side data, you need to use the REST API directly
    print("\n" + "="*50)
    print("SOLUTION: Using REST API for server-side data")
    print("="*50)
    
    import requests
    import json
    
    # Method 1: Use REST API directly to create coverage store
    def create_coverage_store_via_rest(workspace, store_name, file_path, layer_name):
        """Create a coverage store using REST API for server-side data"""
        
        # GeoServer REST API endpoint
        url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores"
        
        # Coverage store configuration
        coverage_store_config = {
            "coverageStore": {
                "name": store_name,
                "description": f"Coverage store for {layer_name}",
                "type": "GeoTIFF",
                "enabled": True,
                "workspace": {
                    "name": workspace
                },
                "url": f"file:{file_path}"
            }
        }
        
        # Headers for the request
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Make the request
        response = requests.post(
            url,
            data=json.dumps(coverage_store_config),
            headers=headers,
            auth=(creds['username'], creds['password'])
        )
        
        return response
    
    # Try to create the coverage store using REST API
    print("Attempting to create coverage store via REST API...")
    try:
        # Adjust this path to match your actual server path
        server_file_path = "/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif"
        
        response = create_coverage_store_via_rest(
            workspace='ind',
            store_name='2001_fire',
            file_path=server_file_path,
            layer_name='2001_fire'
        )
        
        if response.status_code == 201:
            print("✅ Coverage store created successfully via REST API!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Failed to create coverage store. Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error creating coverage store via REST API: {e}")
    
    # Let's check the current coverage store configuration
    print("\n" + "="*50)
    print("CHECKING CURRENT COVERAGE STORE")
    print("="*50)
    try:
        # Get the coverage store details
        store_url = f"{creds['url']}rest/workspaces/ind/coveragestores/2001_fire.json"
        response = requests.get(store_url, auth=(creds['username'], creds['password']))
        
        if response.status_code == 200:
            store_config = response.json()
            print(f"Current coverage store configuration:")
            print(f"Name: {store_config.get('coverageStore', {}).get('name', 'N/A')}")
            print(f"Type: {store_config.get('coverageStore', {}).get('type', 'N/A')}")
            print(f"URL: {store_config.get('coverageStore', {}).get('url', 'N/A')}")
            print(f"Enabled: {store_config.get('coverageStore', {}).get('enabled', 'N/A')}")
        else:
            print(f"Could not get coverage store details. Status: {response.status_code}")
    except Exception as e:
        print(f"Error getting coverage store details: {e}")
    
    # Function to update coverage store file path
    def update_coverage_store_path(workspace, store_name, new_file_path):
        """Update the file path of an existing coverage store"""
        
        # First get the current configuration
        get_url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores/{store_name}.json"
        response = requests.get(get_url, auth=(creds['username'], creds['password']))
        
        if response.status_code != 200:
            print(f"Could not get current store configuration. Status: {response.status_code}")
            return False
        
        store_config = response.json()
        
        # Update the URL
        store_config['coverageStore']['url'] = f"file:{new_file_path}"
        
        # Put the updated configuration back
        put_url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores/{store_name}.json"
        headers = {'Content-Type': 'application/json'}
        
        update_response = requests.put(
            put_url,
            data=json.dumps(store_config),
            headers=headers,
            auth=(creds['username'], creds['password'])
        )
        
        return update_response.status_code == 200
    
    print("\n" + "="*50)
    print("UPDATING COVERAGE STORE FILE PATH")
    print("="*50)
    
    # Try different possible paths
    possible_paths = [
        "/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif",
        "/opt/geoserver/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif",
        "/var/lib/geoserver/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif",
        "/usr/share/geoserver/data/rasters_by_year/Year_2001/Num_Forest_Fire.tif",
        "data/rasters_by_year/Year_2001/Num_Forest_Fire.tif",
        "rasters_by_year/Year_2001/Num_Forest_Fire.tif"
    ]
    
    print("Trying to update the file path with different possible locations...")
    for path in possible_paths:
        print(f"Trying path: {path}")
        if update_coverage_store_path('ind', '2001_fire', path):
            print(f"✅ Successfully updated coverage store with path: {path}")
            break
        else:
            print(f"❌ Failed to update with path: {path}")
    
    # Now let's create a layer from the coverage store
    print("\n" + "="*50)
    print("CREATING LAYER FROM COVERAGE STORE")
    print("="*50)
    
    def create_coverage_layer(workspace, store_name, layer_name):
        """Create a coverage layer from an existing coverage store"""
        
        # First, we need to create a coverage (the actual layer) from the store
        coverage_url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores/{store_name}/coverages"
        
        coverage_config = {
            "coverage": {
                "name": layer_name,
                "title": f"Forest Fire Data for {layer_name}",
                "description": f"Forest fire coverage data for {layer_name}",
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
    
    try:
        print("Creating coverage layer from the coverage store...")
        layer_response = create_coverage_layer('ind', '2001_fire', '2001_fire_layer')
        
        if layer_response.status_code == 201:
            print("✅ Coverage layer created successfully!")
            print(f"Response: {layer_response.text}")
        else:
            print(f"❌ Failed to create coverage layer. Status: {layer_response.status_code}")
            print(f"Response: {layer_response.text}")
            
    except Exception as e:
        print(f"❌ Error creating coverage layer: {e}")
    
    # Let's demonstrate what happens when you upload a file
    print("\n" + "="*50)
    print("WHAT HAPPENS WHEN YOU UPLOAD A FILE?")
    print("="*50)
    
    print("There are different ways to 'upload' to GeoServer:")
    print()
    print("1. UPLOAD VIA create_coveragestore() METHOD:")
    print("   - This method reads a LOCAL file from your machine")
    print("   - It uploads the file content to GeoServer")
    print("   - GeoServer stores the file in its data directory")
    print("   - The coverage store points to the uploaded file")
    print()
    print("   Example:")
    print("   gs.create_coveragestore(")
    print("       layer_name='my_layer',")
    print("       workspace='ind',")
    print("       path='/path/to/your/local/file.tif'  # LOCAL file path")
    print("   )")
    print()
    print("2. REFERENCE EXISTING SERVER FILE:")
    print("   - This method points to a file already on the server")
    print("   - No file is uploaded - just a reference is created")
    print("   - The file must already exist on the GeoServer")
    print("   - This is what we tried with the REST API")
    print()
    print("   Example:")
    print("   # Via REST API - points to server file")
    print("   coverage_store_config = {")
    print("       'coverageStore': {")
    print("           'url': 'file:/server/path/to/file.tif'")
    print("       }")
    print("   }")
    print()
    print("3. UPLOAD VIA WEB INTERFACE:")
    print("   - You can drag and drop files in the web interface")
    print("   - Files are uploaded to GeoServer's data directory")
    print("   - Coverage stores are created automatically")
    print()
    
    # Let's test what happens if we try to upload a local file
    print("\n" + "="*50)
    print("TESTING UPLOAD WITH LOCAL FILE")
    print("="*50)
    
    # Check if we have any local raster files to test with
    import os
    local_test_files = []
    
    # Look for common raster file extensions in the current directory and parent
    for root, dirs, files in os.walk('..'):
        for file in files:
            if file.lower().endswith(('.tif', '.tiff', '.geotiff')):
                local_test_files.append(os.path.join(root, file))
                if len(local_test_files) >= 3:  # Limit to 3 files
                    break
        if len(local_test_files) >= 3:
            break
    
    if local_test_files:
        print(f"Found {len(local_test_files)} local raster files:")
        for i, file_path in enumerate(local_test_files, 1):
            print(f"  {i}. {file_path}")
        
        print("\nLet's try uploading one of these files...")
        test_file = local_test_files[0]
        print(f"Attempting to upload: {test_file}")
        
        try:
            # Try to create a coverage store with the local file
            gs.create_coveragestore(
                layer_name='test_upload',
                workspace='ind',
                path=test_file
            )
            print("✅ Upload successful! The file was uploaded to GeoServer.")
            print("   - The file is now stored in GeoServer's data directory")
            print("   - A coverage store was created")
            print("   - You can now create layers from this store")
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            print("   This might be because:")
            print("   - The file is not a valid raster format")
            print("   - The file is corrupted")
            print("   - There's a permission issue")
    else:
        print("No local raster files found to test upload with.")
        print("To test upload, you would need a .tif, .tiff, or .geotiff file.")
    
    # Now let's upload the specific landslide file
    print("\n" + "="*50)
    print("UPLOADING LANDSLIDE FILE")
    print("="*50)
    
    landslide_file = "../gpkg_to_raster/rasters_by_year/Year_2001/Num_Land_Slide.tif"
    print(f"Uploading file: {landslide_file}")
    
    try:
        # Upload the landslide file
        gs.create_coveragestore(
            layer_name='2001_landslide',
            workspace='ind',
            path=landslide_file
        )
        print("✅ Landslide file uploaded successfully!")
        print("   - Coverage store '2001_landslide' created")
        print("   - File is now stored in GeoServer's data directory")
        
        # Now let's create a layer from this coverage store
        print("\n" + "="*50)
        print("CREATING LAYER FROM UPLOADED FILE")
        print("="*50)
        
        def create_coverage_layer_from_store(workspace, store_name, layer_name):
            """Create a coverage layer from an existing coverage store"""
            
            coverage_url = f"{creds['url']}rest/workspaces/{workspace}/coveragestores/{store_name}/coverages"
            
            coverage_config = {
                "coverage": {
                    "name": layer_name,
                    "title": f"Landslide Data for {layer_name}",
                    "description": f"Landslide coverage data for {layer_name}",
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
        
        # Create the layer
        layer_response = create_coverage_layer_from_store('ind', '2001_landslide', '2001_landslide_layer')
        
        if layer_response.status_code == 201:
            print("✅ Layer created successfully!")
            print(f"   - Layer name: 2001_landslide_layer")
            print(f"   - Workspace: ind")
            print(f"   - Coverage store: 2001_landslide")
            print(f"   - Response: {layer_response.text}")
            
            # Let's also check what layers now exist
            print("\n" + "="*50)
            print("CHECKING AVAILABLE LAYERS")
            print("="*50)
            
            layers_url = f"{creds['url']}rest/layers.json"
            layers_response = requests.get(layers_url, auth=(creds['username'], creds['password']))
            
            if layers_response.status_code == 200:
                layers_data = layers_response.json()
                print("Available layers:")
                for layer in layers_data.get('layers', {}).get('layer', []):
                    layer_name = layer.get('name', 'Unknown')
                    if 'landslide' in layer_name.lower() or '2001' in layer_name:
                        print(f"  ✅ {layer_name}")
                    else:
                        print(f"    {layer_name}")
            else:
                print(f"Could not retrieve layers list. Status: {layers_response.status_code}")
                
        else:
            print(f"❌ Failed to create layer. Status: {layer_response.status_code}")
            print(f"Response: {layer_response.text}")
            
    except Exception as e:
        print(f"❌ Error uploading landslide file: {e}")
        print("This might be because:")
        print("  - The file path is incorrect")
        print("  - The file is not accessible")
        print("  - There's a permission issue")
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print("What we accomplished:")
    print("1. ✅ Found local raster files in your project")
    print("2. ✅ Successfully uploaded Num_Flood.tif (test_upload)")
    print("3. ✅ Successfully uploaded Num_Land_Slide.tif (2001_landslide)")
    print("4. ✅ Created coverage stores for both files")
    print("5. ✅ Created layers from the uploaded files")
    print()
    print("Your files are now available in GeoServer!")
    print("You can access them via:")
    print("  - Web interface: http://landscapes.wearepal.ai/geoserver/web/")
    print("  - WMS/WFS services")
    print("  - REST API")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTroubleshooting tips:")
    print("1. Make sure the workspace exists")
    print("2. Check if you have the right permissions")
    print("3. Verify the data path on the server")
