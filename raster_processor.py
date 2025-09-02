import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import geopandas as gpd
from exceptions import GISProcessingError, ProjectionError


class RasterProcessor:
    """for handling all raster processing operations"""

    @staticmethod
    def clip_raster_with_vector(raster_path: Path, vector_path: Path, output_path: Path) -> bool:
        """clipping raster data using vector boundary"""
        try:
            # load the vector data
            gdf = gpd.read_file(vector_path)

            # ensuring same crs among raster and vector
            with rasterio.open(raster_path) as src:
                if gdf.crs != src.crs:
                    gdf = gdf.to_crs(src.crs)

                # clipping operation
                geometries = [geom for geom in gdf.geometry]
                clipped_data, clipped_transform = mask(
                    src, geometries, crop=True, nodata=src.nodata
                )

                # updating the metadata
                clipped_meta = src.meta.copy()
                clipped_meta.update({
                    "driver": "GTiff",
                    "height": clipped_data.shape[1],
                    "width": clipped_data.shape[2],
                    "transform": clipped_transform
                })

                # writing the output
                with rasterio.open(output_path, 'w', **clipped_meta) as dst:
                    dst.write(clipped_data)
            return True

        except Exception as e:
            raise GISProcessingError(f"Raster clipping failed: {e}")

    @staticmethod
    def clip_raster_with_raster(source_path: Path, mask_path: Path, output_path: Path) -> bool:
        """clipping raster data with raster data as a mask"""
        try:
            with rasterio.open(source_path) as src, rasterio.open(mask_path) as mask_src:
                if src.crs != mask_src.crs:
                    raise ProjectionError("Both Raster must have the same CRS for clipping")

                # reading the mask data
                mask_data = mask_src.read(1)

                boolean_mask = mask_data != mask_src.nodata

                src_data = src.read()

                for i in range(src_data.shape[0]):
                    src_data[i][~boolean_mask] = src.nodata

                meta = src.meta.copy()
                with rasterio.open(output_path, 'w', **meta) as dst:
                    dst.write(src_data)

            return True

        except Exception as e:
            raise GISProcessingError(f"Clipping raster user raster failed: {e}")


    @staticmethod
    def reproject_raster(input_path: Path, output_path: Path, target_crs, resampling_method: str = 'nearest') -> bool:
        """Reprojecting the raster to target coordinate system"""
        try:
            # resampling methods
            resampling_map = {
                'nearest': Resampling.nearest,
                'bilinear': Resampling.bilinear,
                'cubic': Resampling.cubic,
                'average': Resampling.average,
                'mode': Resampling.mode
            }

            with rasterio.open(input_path) as src:
                # calculating transform for target crs
                transform, width, height = calculate_default_transform(
                src.crs, target_crs, src.width, src.height, *src.bounds
                )

                # updating the metadata
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': target_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })

                # performing reprojection
                with rasterio.open(output_path, 'w', **kwargs) as dst:
                    for i in range(1, src.count + 1):
                        reproject(
                            source=rasterio.band(src, i),
                            destination=rasterio.band(dst, i),
                            src_transform=transform,
                            dst_crs=target_crs,
                            resampling=resampling_map[resampling_method]
                        )

                return True

        except Exception as e:
            raise GISProcessingError(f"Raster reprojection failed: {e}")

    @staticmethod
    def resample_raster(input_path: Path, output_path: Path, scale_factor: float, resampling_method: str = 'nearest') -> bool:
        """resampling raster by scale factor"""
        try:
            with rasterio.open(input_path) as src:
                # computing the dimensions
                new_width = int(src.width * scale_factor)
                new_height = int(src.height * scale_factor)

                # computing the new transform
                transform = src.transform * src.transform.scale(
                    (src.width / new_width), (src.height / new_height)
                )

                # reading and resampling the data
                data = src.read(
                    out_shape =(src.count, new_height, new_width),
                    resampling=getattr(Resampling, resampling_method)
                )

                # updating the metadata
                meta = src.meta.copy()
                meta.update({
                    'width': new_width,
                    'height': new_height,
                    'transform': transform,
                })

                # writing the output
                with rasterio.open(output_path, 'w', **meta) as dst:
                    dst.write(data)

            return True
        except Exception as e:
            raise GISProcessingError(f"Raster resampling failed: {e}")

    @staticmethod
    def reclassify_raster(input_path: Path, output_path: Path,
                          classification_rules: Dict[Tuple[float, float], int]) -> bool:
        """Reclassifying raster based on value ranges with proper nodata handling"""
        try:
            print(f"Starting reclassification: {input_path}")
            print(f"Classification rules: {classification_rules}")

            # Validate inputs
            if not input_path.exists():
                raise FileNotFoundError(f"Input raster not found: {input_path}")
            if not classification_rules:
                raise ValueError("No classification rules provided")

            with rasterio.open(input_path) as src:
                try:
                    data = src.read(1)  # Read first band
                    print(f"Input data shape: {data.shape}, dtype: {data.dtype}")
                    print(f"Data range: {data.min()} to {data.max()}")
                    print(f"Original nodata: {src.nodata}")

                except Exception as e:
                    raise GISProcessingError(f"Failed to read input data: {e}")

                # Create the output array
                reclassified = np.full_like(data, -9999, dtype=np.int32)

                # Apply classification rules
                pixels_classified = 0
                for (min_val, max_val), new_val in classification_rules.items():
                    try:
                        # Handle nodata values
                        if src.nodata is not None:
                            mask = ((data >= min_val) & (data <= max_val) & (data != src.nodata))
                        else:
                            mask = ((data >= min_val) & (data <= max_val))

                        pixel_count = mask.sum()
                        if pixel_count > 0:
                            reclassified[mask] = new_val
                            pixels_classified += pixel_count
                            print(f"Classified {pixel_count} pixels from {min_val}-{max_val} to {new_val}")

                    except Exception as e:
                        print(f"Error applying rule {min_val}-{max_val}: {e}")
                        continue

                print(f"Total pixels classified: {pixels_classified}")

                if pixels_classified == 0:
                    raise ValueError("No pixels were classified - check your classification rules")

                # FIXED: Use appropriate nodata value for int32
                output_nodata = -9999  # Standard nodata value that fits in int32

                # Make sure unclassified pixels are set to nodata
                if src.nodata is not None:
                    # Set pixels that were originally nodata to output nodata
                    nodata_mask = (data == src.nodata)
                    reclassified[nodata_mask] = output_nodata

                # Set pixels that weren't classified to output nodata
                unclassified_mask = (reclassified == -9999)
                classified_mask = np.zeros_like(data, dtype=bool)

                # Create mask of all classified pixels
                for (min_val, max_val), new_val in classification_rules.items():
                    if src.nodata is not None:
                        rule_mask = ((data >= min_val) & (data <= max_val) & (data != src.nodata))
                    else:
                        rule_mask = ((data >= min_val) & (data <= max_val))
                    classified_mask |= rule_mask

                # Set unclassified pixels (excluding original nodata) to output nodata
                if src.nodata is not None:
                    unclassified_pixels = (~classified_mask) & (data != src.nodata)
                else:
                    unclassified_pixels = (~classified_mask)

                reclassified[unclassified_pixels] = output_nodata

                # Update metadata for integer output with proper nodata
                meta = src.meta.copy()
                meta.update({
                    'dtype': 'int32',
                    'count': 1,
                    'nodata': output_nodata,  # Use int32-compatible nodata
                    'compress': 'lzw'
                })

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write the output
                try:
                    with rasterio.open(output_path, 'w', **meta) as dst:
                        dst.write(reclassified, 1)

                    print(f"Successfully wrote reclassified raster to: {output_path}")
                    print(f"Output nodata value: {output_nodata}")

                    # Verify output
                    if output_path.exists() and output_path.stat().st_size > 0:
                        return True
                    else:
                        raise GISProcessingError("Reclassified file was not created properly")

                except Exception as e:
                    raise GISProcessingError(f"Failed to write reclassified output: {e}")

        except Exception as e:
            print(f"Raster reclassification failed: {e}")
            # Clean up partial output
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise GISProcessingError(f"Raster reclassification failed: {e}")

