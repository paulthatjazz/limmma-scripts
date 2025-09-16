from owslib.wfs import WebFeatureService
import requests
from shapely.geometry import shape
import geopandas as gpd

def get_filtered_extent(layer_name, cql_filter, name, region):
    """
    Get extent (bounding box) of filtered features from a GeoServer WFS layer.

    Parameters
    layer_name : str
        Name of the layer (workspace:layername format if applicable)
    cql_filter : str
        CQL filter string (e.g. "id=123")
    name : str
        Name of the extent
    region : str
        Region of the extent

    Returns
    -------
    str
        Ruby snippet to create the extent
    """
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature",
        "typeName": layer_name,
        "outputFormat": "application/json",
        "cql_filter": cql_filter,
        "srsName": "EPSG:3857"
    }

    geoserver_url = f"https://landscapes.wearepal.ai/geoserver/wfs"

    # Request GeoServer WFS
    response = requests.get(geoserver_url, params=params)
    response.raise_for_status()

    # Load GeoJSON into GeoDataFrame
    gdf = gpd.read_file(response.text)

    if gdf.empty:
        raise ValueError("No features found with given CQL filter.")

    extent = gdf.total_bounds  # (minx, miny, maxx, maxy)

    ruby_snippet = f'''Extent.create!(
        name: "{name}",
        value: [{extent[0]},{extent[1]},{extent[2]},{extent[3]}],
        team_id: nil,
        layer: '{layer_name}',
        cql: '{cql_filter}',
        region: '{region}'
    )'''

    # Get bounding box
    return ruby_snippet


# Example usage
if __name__ == "__main__":

    # Layer name, cql filter, name, region
    layer_name = "ind:ADM_ADM_1"
    cql_filter = "NAME_1 = 'Papua Barat'"
    name = "West Papua (Papua Barat)"
    region = "Indonesia"

    ruby_snippet = get_filtered_extent(layer_name, cql_filter, name, region)
    
    print("Ruby snippet:", ruby_snippet)
