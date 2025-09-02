import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict


@dataclass
class AppSettings:
    """Application settings configuration"""
    # Default CRS
    default_display_crs: str = "EPSG:4326"
    default_processing_crs: str = "EPSG:3857"

    # File paths
    last_raster_directory: str = str(Path.home())
    last_vector_directory: str = str(Path.home())
    last_output_directory: str = str(Path.home())

    # Processing defaults
    default_resampling_method: str = "nearest"
    default_raster_format: str = "GTiff"
    default_vector_format: str = "ESRI Shapefile"

    # UI preferences
    window_width: int = 1400
    window_height: int = 900
    default_basemap: str = "OpenStreetMap"

    # Performance settings
    max_display_size: int = 1000  # Max pixels for raster display
    chunk_size: int = 1024  # Processing chunk size
    enable_multithreading: bool = True


class SettingsManager:
    """Manages application settings persistence"""

    def __init__(self):
        self.settings_file = Path.home() / ".gis_processor_settings.json"
        self.settings = self.load_settings()

    def load_settings(self) -> AppSettings:
        """Load settings from file or create defaults"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                return AppSettings(**data)
            else:
                return AppSettings()
        except Exception:
            return AppSettings()

    def save_settings(self):
        """Save current settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(asdict(self.settings), f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key: str, default=None):
        """Get setting value"""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any):
        """Set setting value"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()