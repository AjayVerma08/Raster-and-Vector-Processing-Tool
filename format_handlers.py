from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
import rasterio
import geopandas as gpd
import rioxarray as rxr
from exceptions import DataFormatError


class FormatHandler(ABC):
    """Abstract base class for format-specific handlers"""

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Check if handler can process this file"""
        pass

    @abstractmethod
    def read(self, file_path: Path) -> Any:
        """Read file using format-specific logic"""
        pass

    @abstractmethod
    def write(self, data: Any, file_path: Path, **kwargs) -> bool:
        """Write data using format-specific logic"""
        pass


class GeoTiffHandler(FormatHandler):
    """Handler for GeoTIFF files"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.tif', '.tiff']

    def read(self, file_path: Path):
        """Read GeoTIFF file"""
        return rasterio.open(file_path)

    def write(self, data, file_path: Path, **kwargs) -> bool:
        """Write GeoTIFF file"""
        try:
            # Implementation depends on data type
            if hasattr(data, 'save'):
                data.save(file_path, **kwargs)
            return True
        except Exception:
            return False


class ShapefileHandler(FormatHandler):
    """Handler for Shapefile format"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.shp'

    def read(self, file_path: Path):
        """Read Shapefile"""
        return gpd.read_file(file_path)

    def write(self, data: gpd.GeoDataFrame, file_path: Path, **kwargs) -> bool:
        """Write Shapefile"""
        try:
            data.to_file(str(file_path), driver='ESRI Shapefile', **kwargs)
            return True
        except Exception:
            return False


class GeoJSONHandler(FormatHandler):
    """Handler for GeoJSON format"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.geojson', '.json']

    def read(self, file_path: Path):
        """Read GeoJSON file"""
        return gpd.read_file(file_path)

    def write(self, data: gpd.GeoDataFrame, file_path: Path, **kwargs) -> bool:
        """Write GeoJSON file"""
        try:
            data.to_file(str(file_path), driver='GeoJSON', **kwargs)
            return True
        except Exception:
            return False

class KMZHandler(FormatHandler):
    """Handler for KMZ files (zipped KML)"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.kmz'

    def read(self, file_path: Path):
        """Read KMZ file using geopandas with the zip:// protocol"""
        kml_path_in_zip = f"zip://{file_path.as_posix()}!doc.kml"
        return gpd.read_file(kml_path_in_zip)

    def write(self, data: gpd.GeoDataFrame, file_path: Path, **kwargs) -> bool:
        """Write to KML (writing to KMZ directly is complex, so we'll write KML instead)"""
        try:
            if file_path.suffix.lower() == '.kmz':
                print("Warning: Writing directly to KMZ is not implemented. Saving as KML instead.")
                file_path = file_path.with_suffix('.kml')

            data.to_file(str(file_path), driver='KML', **kwargs)
            return True
        except Exception as e:
            print(f"Failed to write KML/KMZ: {e}")
            return False


class NetCDFHandler(FormatHandler):
    """Handler for NetCDF files (using rioxarray)"""

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.nc', '.cdf', '.netcdf']

    def read(self, file_path: Path):
        """
        Read NetCDF file with rioxarray.
        NetCDFs can have multiple variables and time dimensions.
        This returns the first data variable it finds as a rasterio-like dataset.
        """
        # Open the dataset
        xds = rxr.open_rasterio(file_path)

        # get the first data variable if it's a DataArray.
        if hasattr(xds, 'data_vars'):
            # It's a Dataset with multiple variables, let's take the first one.
            var_name = list(xds.data_vars.keys())[0]
            data_array = xds[var_name]
        else:
            data_array = xds

        # take the first time step.
        if 'time' in data_array.dims:
            data_array = data_array.isel(time=0)

        # ensuring it has spatial coordinates and a CRS
        if not data_array.rio.crs:
            data_array.rio.write_crs("EPSG:4326", inplace=True)

        return data_array

    def write(self, data, file_path: Path, **kwargs) -> bool:
        """Write data to NetCDF format."""
        try:
            # Check if the data is an xarray object (like what we read)
            if hasattr(data, 'to_netcdf'):
                data.to_netcdf(file_path, **kwargs)
                return True
            else:
                print("Error: Data is not in an xarray format suitable for NetCDF export.")
                return False
        except Exception as e:
            print(f"Failed to write NetCDF: {e}")
            return False

class FormatFactory:
    """Factory for creating format handlers"""

    def __init__(self):
        self.handlers = [
            GeoTiffHandler(),
            ShapefileHandler(),
            GeoJSONHandler(),
            KMZHandler(),
            NetCDFHandler()
        ]

    def get_handler(self, file_path: Path) -> FormatHandler:
        """Get appropriate handler for file"""
        for handler in self.handlers:
            if handler.can_handle(file_path):
                return handler

        raise DataFormatError(f"No handler available for {file_path.suffix}")