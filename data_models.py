from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import rasterio
import geopandas as gpd

@dataclass
class ProjectionInfo:
    """Coordinate system info"""
    epsg_code: Optional[int] = None
    proj4_string: Optional[str] = None
    wkt_string: Optional[str] = None
    authority: Optional[str] = None

    def to_crs(self):
        """Convert coordinate system to usable format by geopandas"""
        if self.epsg_code:
            return f"EPSG:{self.epsg_code}"
        elif self.proj4_string:
            return self.proj4_string
        elif self.wkt_string:
            return self.wkt_string
        return None

@dataclass
class BoundingBox:
    """bounding box for display"""
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    crs: ProjectionInfo

    def to_shapely_box(self):
        """conversion to shapely box geometry"""
        from shapely.geometry import box
        return box(self.min_x, self.min_y, self.max_x, self.max_y)

class GeoDataset:
    """all geographic datasets"""
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.crs = None
        self.bounds = None
        self.metadata = None

    def get_info(self) -> Dict[str, Any]:
        """returns the information about dataset"""
        raise NotImplementedError

    def reproject(self, target_crs: ProjectionInfo) -> 'GeoDataset':
        """reprojecting dataset to target CRS"""
        raise NotImplementedError

class RasterDataset(GeoDataset):
    """dataset wrapper for raster"""
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.data = None
        self.transform = None
        self.width = None
        self.height = None
        self.band_count = None
        self.dtype = None
        self._load_metadata()

    def _load_metadata(self):
        """load the raster metadata without reading the full data"""
        try:
            with rasterio.open(self.file_path) as src:
                self.crs = ProjectionInfo(
                    epsg_code = src.crs.to_epsg() if src.crs else None,
                    wkt_string=src.crs.to_wkt() if src.crs else None
                )
                self.bounds = BoundingBox(
                    *src.bounds, crs = self.crs
                )
                self.transform = src.transform
                self.width = src.width
                self.height = src.height
                self.band_count = src.count
                self.dtype = src.dtypes[0]
                self.metadata = src.meta.copy()
        except Exception as e:
            raise ValueError(f"Failed to load raster: {e}")

    def read_data(self, bands=None, window=None):
        """reading the raster data with optional band/window selection"""
        with rasterio.open(self.file_path) as src:
            if bands:
                return src.read(bands, window=window)
            return src.read(window=window)

class VectorDataset(GeoDataset):
    """wrapper for vector datasets"""
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self.gdf = None
        self.geometry_type = None
        self.feature_count = None
        self._load_metadata()

    def _load_metadata(self):
        """loading the vector metadata"""
        try:
            #read only the first few features to get the metadata information
            sample_gdf = gpd.read_file(self.file_path, rows=1)
            self.crs = ProjectionInfo(
                epsg_code=sample_gdf.crs.to_epsg() if sample_gdf.crs else None
            )
            self.geometry_type = sample_gdf.geometry.geom_type[0]

            #getting the full feature count
            full_gdf = gpd.read_file((self.file_path))
            self.feature_count = len(full_gdf)
            self.bounds = BoundingBox(
                *full_gdf.total_bounds, crs=self.crs
            )
        except Exception as e:
            raise ValueError(f"Failed to load vector data: {e}")

    def read_data(self):
        """reads the vector data"""
        if self.gdf is None:
            self.gdf = gpd.read_file(self.file_path)
        return self.gdf


