# This code is used to transform irrigated harvest area data from .tif format to .nc
import os
import numpy as np
import rasterio
import xarray as xr
from affine import Affine
from rasterio.warp import reproject, Resampling

# Path for the original data
input_path = '/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/SPAM/spam2005v3r2_global_harv_area/geotiff_global_harv_area'
output_path = "/lustre/nobackup/WUR/ESG/zhou111/Data/Raw/SPAM/spam2005v3r2_global_harv_area/ncFormat"
crop_list = ["ACOF", "BANA", "BARL", "BEAN", "CASS", "CHIC", "CNUT", "COCO", "COTT", "COWP", "GROU", "LENT", "MAIZ", "OCER", "OFIB", "OILP", "OOIL", "ORTS", "PIGE", "PLNT", "PMIL", "POTA", "RAPE", "RCOF", "REST", "RICE", "SESA", "SMIL", "SORG", "SUGB", "SUGC", "SUNF", "SWPO", "TEAS", "TEMF", "TOBA", "TROF", "VEGE", "WHEA", "YAMS"]

# Define our 0.5 degree global grid
lon_new = np.arange(-179.75, 180, 0.5)
lat_new = np.arange(89.75, -90, -0.5)

def aggregate_to_half_degree(file_path, aggregation_method):

    with rasterio.open(file_path) as src:
        # Get input data and metadata
        data = src.read(1)
        nodata = src.nodata
        if nodata is None:
            if src.dtypes[0] == 'float32':
                nodata = -9999.0
            else:
                nodata = 0
        
        # Create mask for valid data
        valid_mask = (data != nodata)
        
        # Convert invalid values to NaN for proper treatment
        data = data.astype(np.float64)
        data[~valid_mask] = np.nan
        
        # Create target array for the half-degree grid
        output_shape = (len(lat_new), len(lon_new))
        output_data = np.zeros(output_shape, dtype=np.float64)
        output_weights = np.zeros(output_shape, dtype=np.float64)
        
        # Get geotransform of the source raster
        src_transform = src.transform
        
        # Calculate pixel size of the source raster
        src_pixel_width = src_transform[0]
        src_pixel_height = -src_transform[4]  # Negative because rows go from north to south
        
        # Initialize a counter for progress reporting
        total_pixels = data.shape[0] * data.shape[1]
        processed_pixels = 0
        
        # Process each valid pixel in the source raster
        for y in range(data.shape[0]):
            for x in range(data.shape[1]):
                if np.isnan(data[y, x]):
                    continue
                    
                # Get the lat/lon of this pixel
                lon, lat = rasterio.transform.xy(src_transform, y, x)
                
                # Find where this pixel belongs in our half-degree grid
                lon_idx = np.abs(lon_new - lon).argmin()
                lat_idx = np.abs(lat_new - lat).argmin()
                
                # Calculate contribution based on aggregation method
                if aggregation_method == 'sum':
                    # For sum, we add the pixel value
                    output_data[lat_idx, lon_idx] += data[y, x]
                    output_weights[lat_idx, lon_idx] += 1
                elif aggregation_method == 'mean':
                    # For mean, we add the pixel value and count for averaging later
                    output_data[lat_idx, lon_idx] += data[y, x]
                    output_weights[lat_idx, lon_idx] += 1
                
                processed_pixels += 1
                if processed_pixels % 1000000 == 0:
                    print(f"Processed {processed_pixels}/{total_pixels} pixels")
        
        # Finalize the aggregation
        if aggregation_method == 'mean':
            # Compute mean where we have data
            valid_cells = output_weights > 0
            output_data[valid_cells] /= output_weights[valid_cells]
        
        # Set cells with no data to NaN
        output_data[output_weights == 0] = np.nan
        
        return output_data

# Create output directory if it doesn't exist
os.makedirs(output_path, exist_ok=True)

for crop in crop_list:
    try:
        print(f"Processing crop: {crop}")
        HA_file = os.path.join(input_path, f"SPAM2005V3r2_global_H_TA_{crop}_A.tif")
        
        # Check if files exist
        if not os.path.exists(HA_file):
            print(f"Warning: {HA_file} does not exist. Skipping.")
            continue

        print(f"Aggregating Harvest Area for {crop} (summing values)")
        HA_aggregated = aggregate_to_half_degree(HA_file, 'sum')
                   
        # Create dataset
        ds = xr.Dataset(
            {
                "Harvest_Area": (["lat", "lon"], HA_aggregated),
            },
            coords={
                "lon": lon_new,
                "lat": lat_new
            },
        )
        
        # Add proper attributes
        ds["Harvest_Area"].attrs = {
            "units": "ha",
            "long_name": f"Harvested area for {crop}",
            "_FillValue": np.nan,
            "aggregation_method": "sum"
        }
        
        
        # Save NetCDF with compression
        nc_file = os.path.join(output_path, f"{crop}_Harvest_Area_05d.nc")
        encoding = {
            "Harvest_Area": {"zlib": True, "complevel": 5},
        }
        ds.to_netcdf(nc_file, encoding=encoding)
        print(f"Saved: {nc_file}")
        
    except Exception as e:
        print(f"Error processing {crop}: {str(e)}")
        continue