import geopandas as gpd
from pathlib import Path
from typing import List
import pandas as pd

from exceptions import GISProcessingError


class VectorProcessor:
    """handles all the vector processing operations"""

    @staticmethod
    def clip_vector(input_path: Path, clip_path: Path, output_path: Path) -> bool:
        """clip the vector data using another vector file"""
        try:
            # loading the datasets
            gdf = gpd.read_file(input_path)
            clip_gdf = gpd.read_file(clip_path)

            if gdf.crs != clip_gdf.crs:
                clip_gdf = clip_gdf.to_crs(gdf.crs)

            # perform the clipping operation
            clipped = gdf.clip(clip_gdf)

            clipped.to_file(output_path)
            return True
        except Exception as e:
            raise GISProcessingError(f"Failed to clip: {e}")


    @staticmethod
    def reproject_vector(input_path: Path, output_path: Path, target_crs: str) -> bool:
        """reproject the vector data to the target CRS"""

        try:
            gdf = gpd.read_file(input_path)
            reprojected = gdf.to_crs(target_crs)
            reprojected.to_file(output_path)
            return True
        except Exception as e:
            raise GISProcessingError(f"Failed to reproject vector: {e}")

    @staticmethod
    def erase_vector(input_path: Path,erase_path: Path, output_path: Path) -> bool:
        """erasing the input vector using defined vector file"""
        try:
            gdf = gpd.read_file(input_path)
            erase_gdf = gpd.read_file(erase_path)

            if gdf.crs != erase_gdf.crs:
                erase_gdf = erase_gdf.to_crs(gdf.crs)

            # erasing operation
            erased = gpd.overlay(gdf, erase_gdf, how='difference')

            erased.to_file(str(output_path))
            return True
        except Exception as e:
            raise GISProcessingError(f"Failed to erase vector: {e}")

    @staticmethod
    def union_vectors(input_paths: List[Path], output_path: Path) -> bool:
        """combining multiple vector datasets"""
        try:
            gdfs = []

            target_crs = None

            # loading all datasets
            for path in input_paths:
                gdf =gpd.read_file(path)
                if target_crs is None:
                    target_crs = gdf.crs
                elif gdf.crs != target_crs:
                    gdf = gdf.to_crs(target_crs)
                gdfs.append(gdf)

            # combining all datasets
            combined = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
            combined.crs = target_crs

            combined.to_file(str(output_path))
            return True
        except Exception as e:
            raise GISProcessingError(f"Union processing failed: {e}")

    @staticmethod
    def intersection_vectors(input1_path: Path, input2_path: Path, output_path: Path) -> bool:
        """finding intersection between two vector datasets"""
        try:
            gdf1 = gpd.read_file(input1_path)
            gdf2 = gpd.read_file(input2_path)

            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)

            # intersection operation
            intersection = gpd.overlay(gdf1, gdf2, how='intersection')

            intersection.to_file(str(output_path))
            return True
        except Exception as e:
            raise GISProcessingError(f"Intersection operation failed: {e}")

    @staticmethod
    def symmetric_difference_vectors(input1_path: Path, input2_path: Path, output_path: Path) -> bool:
        """finding the symmetric difference between two vector files"""
        try:
            gdf1 = gpd.read_file(input1_path)
            gdf2 = gpd.read_file(input2_path)

            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)

            # computing symmetric difference
            sym_diff = gpd.overlay(gdf1, gdf2, how='symmetric_difference')
            sym_diff.to_file(str(output_path))
            return True
        except Exception as e:
            raise GISProcessingError(f"Symmetrical difference failed: {e}")
