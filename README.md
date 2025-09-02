# GIS Processing Tool

A simple GUI-based raster and vector processing tool built with Python.

<img width="1919" height="1020" alt="Image" src="https://github.com/user-attachments/assets/8c3b4b93-8e7c-42bf-b43e-7dbe3cb50769" />

## Project Structure

```
gis-processing-tool/
├── logs/                 # Log files (created at runtime)
├── main.py               # Main application entry point
├── data_models.py        # Data classes and models
├── exceptions.py         # Custom exceptions
├── raster_processor.py   # Raster processing operations
├── vector_processor.py   # Vector processing operations
├── main_window.py        # Main application window
├── raster_panel.py       # Raster processing panel
├── vector_panel.py       # Vector processing panel
├── map_viewer.py         # Map visualization component
├── file_manager.py       # File operations
├── format_handlers.py    # Format-specific handlers
├── settings.py           # Application settings
├── validators.py         # Data validation
├── logger.py             # Logging utilities
├── requirements.txt      # Python dependencies
├── setup.py              # Package setup
├── run_app.py            # Application runner script
└── README.md             # Project documentation
```

## Installation

1. Clone or download the project
2. Install Python 3.9 or higher
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Method 1: Using the runner script
```bash
    python run_app.py
```

### Method 2: Direct execution
```bash
  cd src
  python main.py
```

## Features

### Raster Processing
- Clipping with vector or raster data
- Reprojection to different coordinate systems
- Resampling with various methods
- Reclassification based on user-defined rules

### Vector Processing
- Clipping operations
- Reprojection to different CRS
- Overlay operations (intersection, union, difference, symmetric difference)
- Erase operations
- Data extraction and analysis

### Visualization
- Simple plot based data viewer
- Layer management and display
- Zoom and pan controls

### File Support
- **Raster formats**: GeoTIFF, IMG, JPEG, PNG
- **Vector formats**: Shapefile, GeoJSON, KML, GPKG

## Requirements

- Python 3.9+
- PyQt5
- Rasterio
- GeoPandas
- Shapely
- Folium
- NumPy
- Pandas
- Rioxarray

## Usage

1. Launch the application
2. Use the tabs to switch between raster and vector processing
3. Load input files using the browse buttons
4. Configure processing parameters
5. Set output location and format
6. Click process to execute operations
7. View results in the integrated map viewer

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure all dependencies are installed
2. **File Access Error**: Check file permissions and paths
3. **CRS Issues**: Ensure input data has proper coordinate reference systems
4. **Memory Issues**: Large files may require more RAM

### Log Files

Check the `logs/` directory for detailed error messages and processing information.

# Installation and setup instructions
## Setup Instructions

1. Copy all the code files to their respective locations
2. Install dependencies:
   pip install -r requirements.txt
3. Run the application:
   python run_app.py

## Key Files to Create:

1. requirements.txt - Dependencies list
2. run_app.py - Application runner
3. All the Python modules from the uploaded document

## Customization:

- Modify the dark theme in main.py
- Add new processing operations in the processor classes
- Extend file format support in format_handlers.py
- Customize the UI layout in the panel classes
