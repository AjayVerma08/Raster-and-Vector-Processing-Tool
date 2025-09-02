from pathlib import Path
from typing import List, Dict, Any
import rasterio
import geopandas as gpd
from data_models import RasterDataset, VectorDataset
from exceptions import DataFormatError, FileAccessError


class FileManager:
    """Handles file I/O operations for various geospatial formats"""

    # Supported formats
    RASTER_EXTENSIONS = {'.tif', '.tiff', '.img', '.jpg', '.jpeg', '.png', '.bmp', '.nc', '.cdf', '.netcdf'}
    VECTOR_EXTENSIONS = {'.shp', '.kml', '.geojson', '.gpkg', '.gml', '.json', '.kmz'}

    @classmethod
    def detect_file_type(cls, file_path: Path) -> str:
        """Detect if file is raster or vector"""
        suffix = file_path.suffix.lower()

        if suffix in cls.RASTER_EXTENSIONS:
            return 'raster'
        elif suffix in cls.VECTOR_EXTENSIONS:
            return 'vector'
        else:
            raise DataFormatError(f"Unsupported file format: {suffix}")

    @classmethod
    def validate_file_access(cls, file_path: Path) -> bool:
        """Validate file exists and is accessible"""
        if not file_path.exists():
            raise FileAccessError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise FileAccessError(f"Path is not a file: {file_path}")

        try:
            file_path.open('rb').close()
        except PermissionError:
            raise FileAccessError(f"Permission denied: {file_path}")

        return True

    @classmethod
    def load_dataset(cls, file_path: Path):
        """Load dataset based on file type"""
        cls.validate_file_access(file_path)
        file_type = cls.detect_file_type(file_path)

        if file_type == 'raster':
            return RasterDataset(file_path)
        elif file_type == 'vector':
            return VectorDataset(file_path)
        return None

    @classmethod
    def get_raster_info(cls, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive raster information"""
        try:
            with rasterio.open(file_path) as src:
                return {
                    'format': src.driver,
                    'width': src.width,
                    'height': src.height,
                    'bands': src.count,
                    'dtype': src.dtypes[0],
                    'crs': str(src.crs) if src.crs else 'Unknown',
                    'transform': src.transform,
                    'bounds': src.bounds,
                    'nodata': src.nodata,
                    'compression': src.compression.name if src.compression else None
                }
        except Exception as e:
            raise DataFormatError(f"Cannot read raster info: {e}")

    @classmethod
    def get_vector_info(cls, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive vector information"""
        try:
            gdf = gpd.read_file(file_path)
            return {
                'format': file_path.suffix,
                'feature_count': len(gdf),
                'geometry_type': gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else 'Empty',
                'crs': str(gdf.crs) if gdf.crs else 'Unknown',
                'bounds': gdf.total_bounds,
                'columns': list(gdf.columns),
                'area': gdf.geometry.area.sum() if not gdf.geometry.empty else 0
            }
        except Exception as e:
            raise DataFormatError(f"Cannot read vector info: {e}")

    @classmethod
    def get_supported_formats(cls) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        return {
            'raster': list(cls.RASTER_EXTENSIONS),
            'vector': list(cls.VECTOR_EXTENSIONS)
        }

    @classmethod
    def create_file_filter(cls, data_type: str = 'all') -> str:
        """Create file dialog filter string"""
        if data_type == 'raster':
            extensions = cls.RASTER_EXTENSIONS
            desc = "Raster Files"
        elif data_type == 'vector':
            extensions = cls.VECTOR_EXTENSIONS
            desc = "Vector Files"
        else:
            extensions = cls.RASTER_EXTENSIONS.union(cls.VECTOR_EXTENSIONS)
            desc = "Geospatial Files"

        ext_str = " ".join([f"*{ext}" for ext in extensions])
        return f"{desc} ({ext_str});;All Files (*)"


