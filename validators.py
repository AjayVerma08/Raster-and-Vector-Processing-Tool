from pathlib import Path
import rasterio
import geopandas as gpd
from exceptions import DataFormatError, ProjectionError, FileAccessError
from file_manager import FileManager


class DataValidator:
    """Validates geospatial data and parameters"""

    @staticmethod
    def validate_raster_file(file_path: Path) -> bool:
        """Validate raster file can be opened"""
        try:
            with rasterio.open(file_path) as src:
                # Basic checks
                if src.width <= 0 or src.height <= 0:
                    raise DataFormatError("Invalid raster dimensions")
                if src.count <= 0:
                    raise DataFormatError("No bands found in raster")
            return True
        except rasterio.errors.RasterioIOError as e:
            raise DataFormatError(f"Cannot read raster file: {e}")

    @staticmethod
    def validate_vector_file(file_path: Path) -> bool:
        """Validate vector file can be opened"""
        try:
            gdf = gpd.read_file(file_path)
            if gdf.empty:
                raise DataFormatError("Vector file contains no features")
            if gdf.geometry.isna().all():
                raise DataFormatError("Vector file contains no valid geometries")
            return True
        except Exception as e:
            raise DataFormatError(f"Cannot read vector file: {e}")

    @staticmethod
    def validate_crs_compatibility(file1_path: Path, file2_path: Path) -> bool:
        """Check if two files have compatible CRS"""
        try:
            # Determine file types
            type1 = FileManager.detect_file_type(file1_path)
            type2 = FileManager.detect_file_type(file2_path)

            crs1 = crs2 = None

            if type1 == 'raster':
                with rasterio.open(file1_path) as src:
                    crs1 = src.crs
            else:
                gdf = gpd.read_file(file1_path)
                crs1 = gdf.crs

            if type2 == 'raster':
                with rasterio.open(file2_path) as src:
                    crs2 = src.crs
            else:
                gdf = gpd.read_file(file2_path)
                crs2 = gdf.crs

            if crs1 != crs2:
                raise ProjectionError(f"CRS mismatch: {crs1} vs {crs2}")

            return True

        except Exception as e:
            raise ProjectionError(f"CRS validation failed: {e}")

    @staticmethod
    def validate_output_path(output_path: Path, overwrite: bool = False) -> bool:
        """Validate output path is writable"""
        # Check parent directory exists and is writable
        parent_dir = output_path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True)
            except PermissionError:
                raise FileAccessError(f"Cannot create output directory: {parent_dir}")

        # Check if file exists and overwrite permission
        if output_path.exists() and not overwrite:
            raise FileAccessError(f"Output file already exists: {output_path}")

        # Test write permission
        try:
            test_file = parent_dir / "write_test.tmp"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise FileAccessError(f"No write permission in: {parent_dir}")

        return True


