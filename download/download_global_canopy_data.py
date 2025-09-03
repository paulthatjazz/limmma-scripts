import os
import requests

# ---------------- CONFIG ----------------
BASE_URL = "https://libdrive.ethz.ch/index.php/s/cO8or7iOe5dT2Rt/download?path=%2F3deg_cogs&files="
OUTPUT_FOLDER = "Canopy_Downloads_N57W015_N48E000"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Bounding box (lat_min, lat_max, lon_min, lon_max)
LAT_MIN, LAT_MAX = 48, 57
LON_MIN, LON_MAX = -15, 0   # W015 → E000

# Step size (3° tiles)
LAT_STEP = 3
LON_STEP = 3
# ----------------------------------------

def lat_label(lat):
    return f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"

def lon_label(lon):
    if lon >= 0:
        return f"E{lon:03d}"
    else:
        return f"W{abs(lon):03d}"

# Generate latitude range (top to bottom)
lat_range = range(LAT_MAX, LAT_MIN - 1, -LAT_STEP)

# Generate longitude range (left to right)
if LON_MIN <= LON_MAX:
    lon_range = range(LON_MIN, LON_MAX + 1, LON_STEP)
else:
    lon_range = range(LON_MIN, LON_MAX - 1, -LON_STEP)

for lat in lat_range:
    for lon in lon_range:
        lat_str = lat_label(lat)
        lon_str = lon_label(lon)

        for suffix in ["Map.tif", "Map_SD.tif"]:
            fname = f"ETH_GlobalCanopyHeight_10m_2020_{lat_str}{lon_str}_{suffix}"
            url = BASE_URL + fname
            out_path = os.path.join(OUTPUT_FOLDER, fname)

            if os.path.exists(out_path):
                print(f"✔️ Skipping {fname}, already downloaded")
                continue

            print(f"⬇️ Downloading {fname} ...")
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ {fname} saved!")
            else:
                print(f"⚠️ Failed: {url}")