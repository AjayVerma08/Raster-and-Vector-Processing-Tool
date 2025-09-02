from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QListWidget, QListWidgetItem, QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import rasterio
import geopandas as gpd
import numpy as np
from pathlib import Path
import traceback


class LayerItem:
    """Enhanced layer item for tracking map layers with statistics"""

    def __init__(self, name, file_path, layer_type):
        self.name = name
        self.file_path = file_path
        self.layer_type = layer_type
        self.visible = True
        self.bounds = None
        self.plot_objects = []  # Store matplotlib objects for this layer
        self.statistics = None  # Store layer statistics


class SimpleMapViewer(QWidget):
    """Optimized simple map viewer using matplotlib with layer management"""

    def __init__(self):
        super().__init__()
        self.layers = {}  # Dictionary of LayerItem objects
        self.current_bounds = None
        self.setup_ui()

    def setup_ui(self):
        """Setup the simple map viewer interface"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Left panel for layer controls
        left_panel = QWidget()
        left_panel.setFixedWidth(200)
        left_layout = QVBoxLayout(left_panel)

        # Control buttons
        controls_layout = QVBoxLayout()

        self.zoom_extent_btn = QPushButton("Zoom to Extent")
        self.zoom_extent_btn.clicked.connect(self.zoom_to_extent)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_display)

        self.show_stats_btn = QPushButton("Show Layer Info")
        self.show_stats_btn.clicked.connect(self.show_layer_statistics)

        controls_layout.addWidget(self.zoom_extent_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addWidget(self.show_stats_btn)

        # Layer list
        layers_label = QLabel("Layers:")
        layers_label.setStyleSheet("font-weight: bold;")

        self.layer_list = QListWidget()
        self.layer_list.setMaximumHeight(300)

        left_layout.addLayout(controls_layout)
        left_layout.addWidget(layers_label)
        left_layout.addWidget(self.layer_list)
        left_layout.addStretch()

        # Right panel for map
        map_panel = QWidget()
        map_layout = QVBoxLayout(map_panel)
        map_layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure and canvas - optimized for performance
        self.figure = Figure(figsize=(12, 10), dpi=80, facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; }")

        map_layout.addWidget(self.toolbar)
        map_layout.addWidget(self.canvas)
        map_layout.addWidget(self.status_label)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(map_panel, 1)

        # Initialize empty plot
        self.clear_plot()

    def clear_plot(self):
        """Clear the plot and set up clean axes"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        # Clean, minimal styling
        self.ax.set_title("Data Viewer", fontsize=14, pad=20)
        self.ax.set_xlabel("Longitude", fontsize=12)
        self.ax.set_ylabel("Latitude", fontsize=12)

        # Remove grid and make it clean
        self.ax.grid(False)
        self.ax.set_facecolor('white')

        # Set reasonable default view (world extent)
        self.ax.set_xlim(-180, 180)
        self.ax.set_ylim(-90, 90)

        # Improve appearance
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.canvas.draw_idle()

    def add_raster_layer(self, file_path: str, layer_name: str = None):
        """Add raster layer with optimized display and statistics"""
        try:
            if layer_name is None:
                layer_name = Path(file_path).stem

            print(f"Adding raster: {layer_name}")

            # Check if layer already exists
            if layer_name in self.layers:
                layer_name = f"{layer_name}_{len(self.layers)}"

            with rasterio.open(file_path) as src:
                # Get bounds
                bounds = src.bounds

                # Read data with appropriate downsampling for performance
                # Limit to reasonable resolution for display
                max_size = 1024
                if src.width > max_size or src.height > max_size:
                    # Calculate downsampling factor
                    scale = min(max_size / src.width, max_size / src.height)
                    new_width = int(src.width * scale)
                    new_height = int(src.height * scale)

                    data = src.read(1, out_shape=(new_height, new_width),
                                    resampling=rasterio.enums.Resampling.average)
                else:
                    data = src.read(1)

                # Calculate statistics from original data (small sample for speed)
                sample_window = rasterio.windows.Window(0, 0, min(500, src.width), min(500, src.height))
                sample_data = src.read(1, window=sample_window)

                # Handle nodata values for statistics
                if src.nodata is not None:
                    valid_data = sample_data[sample_data != src.nodata]
                    data = np.ma.masked_equal(data, src.nodata)
                else:
                    valid_data = sample_data.flatten()

                # Calculate statistics
                if len(valid_data) > 0:
                    min_val = float(np.min(valid_data))
                    max_val = float(np.max(valid_data))
                    mean_val = float(np.mean(valid_data))
                    stats_text = f"Min: {min_val:.2f}, Max: {max_val:.2f}, Mean: {mean_val:.2f}"
                else:
                    stats_text = "No valid data"

                # Create extent for display
                extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

                # Choose appropriate colormap based on data
                if data.dtype == np.uint8:
                    cmap = 'gray'
                else:
                    cmap = 'viridis'

                # Plot the raster with optimized settings
                im = self.ax.imshow(data, extent=extent, cmap=cmap, alpha=0.8,
                                    interpolation='bilinear', aspect='auto')

                # Add colorbar with statistics
                cbar = self.figure.colorbar(im, ax=self.ax, shrink=0.6, pad=0.02)
                cbar.set_label(f'{layer_name}\n{stats_text}', fontsize=9)

                # Create layer item with statistics
                layer_item = LayerItem(layer_name, file_path, 'raster')
                layer_item.bounds = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                layer_item.plot_objects = [im, cbar]  # Include colorbar in plot objects
                layer_item.statistics = {
                    'min': min_val if len(valid_data) > 0 else None,
                    'max': max_val if len(valid_data) > 0 else None,
                    'mean': mean_val if len(valid_data) > 0 else None,
                    'nodata': src.nodata,
                    'dtype': str(src.dtypes[0])
                }

                self.layers[layer_name] = layer_item
                self.update_layer_list()

            self.status_label.setText(f"Added raster: {layer_name} - {stats_text}")
            self.update_bounds(layer_item.bounds)
            self.canvas.draw_idle()
            return True

        except Exception as e:
            error_msg = f"Error adding raster {layer_name}: {e}"
            print(error_msg)
            traceback.print_exc()
            self.status_label.setText(error_msg)
            return False

    def add_vector_layer(self, file_path: str, layer_name: str = None):
        """Add vector layer with optimized rendering"""
        try:
            if layer_name is None:
                layer_name = Path(file_path).stem

            print(f"Adding vector: {layer_name}")

            # Check if layer already exists
            if layer_name in self.layers:
                layer_name = f"{layer_name}_{len(self.layers)}"

            # Read the vector file
            gdf = gpd.read_file(file_path)

            if gdf.empty:
                self.status_label.setText(f"Vector file is empty: {layer_name}")
                return False

            # Filter out invalid geometries
            valid_mask = gdf.geometry.notna() & gdf.geometry.is_valid
            if not valid_mask.any():
                self.status_label.setText(f"No valid geometries in: {layer_name}")
                return False

            gdf = gdf[valid_mask]

            # Reproject to geographic coordinates if needed
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                try:
                    gdf = gdf.to_crs('EPSG:4326')
                except Exception as e:
                    print(f"Warning: Could not reproject {layer_name}: {e}")

            plot_objects = []

            # Color scheme for different geometry types
            colors = {'Point': 'red', 'LineString': 'blue', 'Polygon': 'green',
                      'MultiPoint': 'red', 'MultiLineString': 'blue', 'MultiPolygon': 'green'}

            # Plot geometries by type for better performance
            geom_types = gdf.geometry.geom_type.unique()

            for geom_type in geom_types:
                type_gdf = gdf[gdf.geometry.geom_type == geom_type]
                color = colors.get(geom_type, 'black')

                if geom_type in ['Point', 'MultiPoint']:
                    # Plot points efficiently
                    x_coords = []
                    y_coords = []

                    for geom in type_gdf.geometry:
                        if geom_type == 'Point':
                            x_coords.append(geom.x)
                            y_coords.append(geom.y)
                        else:  # MultiPoint
                            for point in geom.geoms:
                                x_coords.append(point.x)
                                y_coords.append(point.y)

                    if x_coords and y_coords:
                        scatter = self.ax.scatter(x_coords, y_coords, c=color, s=30, alpha=0.7)
                        plot_objects.append(scatter)

                elif geom_type in ['LineString', 'MultiLineString']:
                    # Plot lines
                    for geom in type_gdf.geometry:
                        if geom_type == 'LineString':
                            x, y = geom.xy
                            line = self.ax.plot(x, y, color=color, linewidth=1.5, alpha=0.8)[0]
                            plot_objects.append(line)
                        else:  # MultiLineString
                            for line_geom in geom.geoms:
                                x, y = line_geom.xy
                                line = self.ax.plot(x, y, color=color, linewidth=1.5, alpha=0.8)[0]
                                plot_objects.append(line)

                elif geom_type in ['Polygon', 'MultiPolygon']:
                    # Plot polygons
                    from matplotlib.patches import Polygon as MplPolygon

                    for geom in type_gdf.geometry:
                        if geom_type == 'Polygon':
                            if not geom.exterior.is_empty:
                                coords = list(geom.exterior.coords)
                                polygon = MplPolygon(coords, facecolor=color, alpha=0.3,
                                                     edgecolor=color, linewidth=1)
                                patch = self.ax.add_patch(polygon)
                                plot_objects.append(patch)
                        else:  # MultiPolygon
                            for poly_geom in geom.geoms:
                                if not poly_geom.exterior.is_empty:
                                    coords = list(poly_geom.exterior.coords)
                                    polygon = MplPolygon(coords, facecolor=color, alpha=0.3,
                                                         edgecolor=color, linewidth=1)
                                    patch = self.ax.add_patch(polygon)
                                    plot_objects.append(patch)

            # Create layer item
            layer_item = LayerItem(layer_name, file_path, 'vector')
            bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
            layer_item.bounds = bounds
            layer_item.plot_objects = plot_objects

            self.layers[layer_name] = layer_item
            self.update_layer_list()

            self.status_label.setText(f"Added vector: {layer_name} ({len(gdf)} features)")
            self.update_bounds(bounds)
            self.canvas.draw_idle()
            return True

        except Exception as e:
            error_msg = f"Error adding vector {layer_name}: {e}"
            print(error_msg)
            traceback.print_exc()
            self.status_label.setText(error_msg)
            return False

    def update_layer_list(self):
        """Update the layer list with checkboxes"""
        self.layer_list.clear()

        for layer_name, layer_item in self.layers.items():
            # Create list item
            list_item = QListWidgetItem()

            # Create widget for the item
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)

            # Checkbox for visibility
            checkbox = QCheckBox()
            checkbox.setChecked(layer_item.visible)
            checkbox.stateChanged.connect(
                lambda state, name=layer_name: self.toggle_layer_visibility(name, state == Qt.Checked)
            )

            # Layer info
            type_symbol = "🗺️" if layer_item.layer_type == "raster" else "📍"
            label = QLabel(f"{type_symbol} {layer_name}")

            item_layout.addWidget(checkbox)
            item_layout.addWidget(label)
            item_layout.addStretch()

            # Add to list
            list_item.setSizeHint(item_widget.sizeHint())
            self.layer_list.addItem(list_item)
            self.layer_list.setItemWidget(list_item, item_widget)

    def toggle_layer_visibility(self, layer_name, visible):
        """Toggle layer visibility"""
        if layer_name in self.layers:
            layer_item = self.layers[layer_name]
            layer_item.visible = visible

            # Show/hide plot objects
            for plot_obj in layer_item.plot_objects:
                plot_obj.set_visible(visible)

            self.canvas.draw_idle()
            print(f"Toggled {layer_name} visibility: {visible}")

    def update_bounds(self, new_bounds):
        """Update overall bounds tracking"""
        if new_bounds is None or len(new_bounds) != 4:
            return

        try:
            bounds = [float(b) for b in new_bounds]

            if self.current_bounds is None:
                self.current_bounds = bounds.copy()
            else:
                self.current_bounds[0] = min(self.current_bounds[0], bounds[0])  # minx
                self.current_bounds[1] = min(self.current_bounds[1], bounds[1])  # miny
                self.current_bounds[2] = max(self.current_bounds[2], bounds[2])  # maxx
                self.current_bounds[3] = max(self.current_bounds[3], bounds[3])  # maxy

        except Exception as e:
            print(f"Error updating bounds: {e}")

    def zoom_to_extent(self):
        """Zoom to show all visible layers"""
        try:
            visible_bounds = None

            for layer_item in self.layers.values():
                if layer_item.visible and layer_item.bounds is not None:
                    bounds = [float(b) for b in layer_item.bounds]

                    if visible_bounds is None:
                        visible_bounds = bounds.copy()
                    else:
                        visible_bounds[0] = min(visible_bounds[0], bounds[0])  # minx
                        visible_bounds[1] = min(visible_bounds[1], bounds[1])  # miny
                        visible_bounds[2] = max(visible_bounds[2], bounds[2])  # maxx
                        visible_bounds[3] = max(visible_bounds[3], bounds[3])  # maxy

            if visible_bounds and len(visible_bounds) == 4:
                minx, miny, maxx, maxy = visible_bounds

                # Add padding (5% of range)
                x_range = maxx - minx
                y_range = maxy - miny

                if x_range > 0 and y_range > 0:
                    padding_x = x_range * 0.05
                    padding_y = y_range * 0.05

                    self.ax.set_xlim(minx - padding_x, maxx + padding_x)
                    self.ax.set_ylim(miny - padding_y, maxy + padding_y)

                    self.status_label.setText("Zoomed to extent")
                    self.canvas.draw_idle()
                else:
                    self.status_label.setText("Invalid data extent")
            else:
                self.status_label.setText("No visible layers to zoom to")

        except Exception as e:
            error_msg = f"Zoom error: {e}"
            print(error_msg)
            self.status_label.setText(error_msg)

    def clear_all(self):
        """Clear all layers"""
        self.layers.clear()
        self.current_bounds = None
        self.clear_plot()
        self.update_layer_list()
        self.status_label.setText("Cleared all layers")

    def refresh_display(self):
        """Refresh the display"""
        self.canvas.draw()
        self.status_label.setText("Display refreshed")

    def show_layer_statistics(self):
        """Display detailed statistics for all layers"""
        if not self.layers:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Layer Information", "No layers loaded")
            return

        # Create detailed statistics dialog
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Layer Statistics")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        # Text area for statistics
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        # Compile statistics for all layers
        stats_text = "=== LAYER STATISTICS ===\n\n"

        for layer_name, layer_item in self.layers.items():
            stats_text += f"Layer: {layer_name}\n"
            stats_text += f"Type: {layer_item.layer_type.upper()}\n"
            stats_text += f"File: {Path(layer_item.file_path).name}\n"
            stats_text += f"Visible: {'Yes' if layer_item.visible else 'No'}\n"

            if layer_item.bounds:
                bounds = layer_item.bounds
                stats_text += f"Bounds: [{bounds[0]:.6f}, {bounds[1]:.6f}, {bounds[2]:.6f}, {bounds[3]:.6f}]\n"
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                stats_text += f"Extent: {width:.6f} x {height:.6f}\n"

            if layer_item.layer_type == 'raster' and layer_item.statistics:
                stats = layer_item.statistics
                stats_text += "--- Raster Statistics ---\n"
                if stats.get('min') is not None:
                    stats_text += f"Minimum Value: {stats['min']:.6f}\n"
                if stats.get('max') is not None:
                    stats_text += f"Maximum Value: {stats['max']:.6f}\n"
                if stats.get('mean') is not None:
                    stats_text += f"Mean Value: {stats['mean']:.6f}\n"
                if stats.get('dtype'):
                    stats_text += f"Data Type: {stats['dtype']}\n"
                if stats.get('nodata') is not None:
                    stats_text += f"NoData Value: {stats['nodata']}\n"

            elif layer_item.layer_type == 'vector':
                try:
                    import geopandas as gpd
                    gdf = gpd.read_file(layer_item.file_path)
                    stats_text += "--- Vector Statistics ---\n"
                    stats_text += f"Feature Count: {len(gdf)}\n"
                    stats_text += f"Geometry Types: {', '.join(gdf.geometry.geom_type.unique())}\n"
                    if gdf.crs:
                        stats_text += f"CRS: {gdf.crs}\n"
                    stats_text += f"Columns: {', '.join([col for col in gdf.columns if col != 'geometry'])}\n"
                except Exception as e:
                    stats_text += f"--- Vector Statistics ---\nError reading statistics: {e}\n"

            stats_text += "\n" + "-" * 50 + "\n\n"

        text_edit.setText(stats_text)
        layout.addWidget(text_edit)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()

    def get_current_layers(self):
        """Get list of current layer names"""
        return list(self.layers.keys())