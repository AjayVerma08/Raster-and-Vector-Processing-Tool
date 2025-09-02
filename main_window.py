from PyQt5.QtWidgets import (QMainWindow, QHBoxLayout, QWidget, QTabWidget,
                             QFileDialog, QMessageBox, QStatusBar,
                             QProgressBar, QLabel, QVBoxLayout)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QAction
import traceback
from pathlib import Path
from raster_panel import RasterPanel
from vector_panel import VectorPanel

class ProcessingWorker(QThread):
    """Enhanced worker thread for processing operations"""
    finished = pyqtSignal(bool, str, str)  # success, message, output_path
    progress = pyqtSignal(int)  # progress percentage
    error = pyqtSignal(str)  # error message

    def __init__(self, operation_func, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        self.output_path = None

    def run(self):
        try:
            # Extract output path if it's in the arguments
            for arg in self.args:
                if isinstance(arg, (str, Path)) and str(arg).endswith(('.tif', '.shp', '.geojson', '.gpkg', '.kml')):
                    self.output_path = str(arg)
                    break

            # Execute the processing operation
            result = self.operation_func(*self.args, **self.kwargs)

            if result:
                self.finished.emit(True, "Operation completed successfully", self.output_path or "")
            else:
                self.finished.emit(False, "Operation failed", "")

        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            print(f"Worker thread error: {error_msg}")
            traceback.print_exc()
            self.error.emit(error_msg)
            self.finished.emit(False, error_msg, "")


class MainWindow(QMainWindow):
    """Enhanced main application window with fixed layer loading"""

    def __init__(self):
        super().__init__()
        self.status_label = None
        self.progress_bar = None
        self.status_bar = None
        self.map_viewer = None
        self.vector_panel = None
        self.raster_panel = None
        self.tab_widget = None
        self.setWindowTitle("GIS Processing Tool")
        self.setGeometry(100, 100, 1400, 900)

        # Processing thread
        self.worker_thread = None
        self.current_operation = None

        # Initialize components
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()

    def setup_ui(self):
        """Setup main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel with processing tools
        self.tab_widget = QTabWidget()
        self.raster_panel = RasterPanel()
        self.vector_panel = VectorPanel()

        self.tab_widget.addTab(self.raster_panel, "Raster Processing")
        self.tab_widget.addTab(self.vector_panel, "Vector Processing")

        # Connect file loading signals
        self.raster_panel.file_loaded.connect(self.on_raster_file_loaded)
        self.vector_panel.file_loaded.connect(self.on_vector_file_loaded)

        # Connect processing signals
        self.raster_panel.processing_requested.connect(self.start_processing_simple)
        self.vector_panel.processing_requested.connect(self.start_processing)

        # Right panel with simple map display
        try:
            # Use the improved simple map viewer instead of folium-based one
            from simple_map_viewer import SimpleMapViewer
            self.map_viewer = SimpleMapViewer()
            print("Using SimpleMapViewer for better performance")
        except ImportError as e:
            print(f"Failed to import SimpleMapViewer: {e}")
            # Create a placeholder widget
            self.map_viewer = QWidget()
            placeholder_label = QLabel("Map viewer not available")
            placeholder_layout = QVBoxLayout(self.map_viewer)
            placeholder_layout.addWidget(placeholder_label)

        # Add to layout
        main_layout.addWidget(self.tab_widget, 1)
        main_layout.addWidget(self.map_viewer, 2)

    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        open_raster_action = QAction('Open Raster', self)
        open_raster_action.triggered.connect(self.open_raster_file)
        file_menu.addAction(open_raster_action)

        open_vector_action = QAction('Open Vector', self)
        open_vector_action.triggered.connect(self.open_vector_file)
        file_menu.addAction(open_vector_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu('View')

        zoom_extent_action = QAction('Zoom to Extent', self)
        zoom_extent_action.triggered.connect(lambda: self.map_viewer.zoom_to_extent() if hasattr(self.map_viewer, 'zoom_to_extent') else None)
        view_menu.addAction(zoom_extent_action)

        refresh_map_action = QAction('Refresh Map', self)
        refresh_map_action.triggered.connect(lambda: self.map_viewer.refresh_display() if hasattr(self.map_viewer, 'refresh_display') else None)
        view_menu.addAction(refresh_map_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Setup status bar with progress indication"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def on_raster_file_loaded(self, file_path):
        """Handle raster file loading with improved error handling"""
        print(f"Raster file loaded: {file_path}")
        try:
            # Validate file exists and is readable
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Update status
            self.status_label.setText(f"Loading raster: {file_path_obj.name}")

            # Add to map with proper error handling
            success = self.add_layer_to_map(file_path, "raster")

            if success:
                self.status_label.setText(f"Loaded raster: {file_path_obj.name}")
            else:
                self.status_label.setText(f"Failed to load raster: {file_path_obj.name}")

        except Exception as e:
            print(f"Error in raster file loading handler: {e}")
            QMessageBox.warning(self, "File Loading Error", f"Failed to load raster file:\n{str(e)}")

    def on_vector_file_loaded(self, file_path):
        """Handle vector file loading with improved error handling"""
        print(f"Vector file loaded: {file_path}")
        try:
            # Validate file exists and is readable
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Update status
            self.status_label.setText(f"Loading vector: {file_path_obj.name}")

            # Add to map with proper error handling
            success = self.add_layer_to_map(file_path, "vector")

            if success:
                self.status_label.setText(f"Loaded vector: {file_path_obj.name}")
            else:
                self.status_label.setText(f"Failed to load vector: {file_path_obj.name}")

        except Exception as e:
            print(f"Error in vector file loading handler: {e}")
            QMessageBox.warning(self, "File Loading Error", f"Failed to load vector file:\n{str(e)}")

    def add_layer_to_map(self, file_path, layer_type):
        """Add layer to map with comprehensive error handling and validation"""
        try:
            print(f"Attempting to add {layer_type} layer: {file_path}")

            # Validate inputs
            if not file_path:
                raise ValueError("No file path provided")

            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check if map viewer is available
            if not hasattr(self.map_viewer, 'add_raster_layer') and not hasattr(self.map_viewer, 'add_vector_layer'):
                raise RuntimeError("Map viewer is not properly initialized")

            # Add layer based on type
            success = False
            layer_name = file_path_obj.stem

            if layer_type == "raster":
                if hasattr(self.map_viewer, 'add_raster_layer'):
                    success = self.map_viewer.add_raster_layer(str(file_path), layer_name)
                else:
                    raise RuntimeError("Raster layer functionality not available")
            elif layer_type == "vector":
                if hasattr(self.map_viewer, 'add_vector_layer'):
                    success = self.map_viewer.add_vector_layer(str(file_path), layer_name)
                else:
                    raise RuntimeError("Vector layer functionality not available")
            else:
                raise ValueError(f"Unknown layer type: {layer_type}")

            if success:
                print(f"Successfully added {layer_type} layer: {layer_name}")
                # Auto-zoom to new layer extent after a delay
                QTimer.singleShot(1000, lambda: self.zoom_to_layer_extent())
                return True
            else:
                print(f"Failed to add {layer_type} layer: {layer_name}")
                QMessageBox.warning(
                    self, "Layer Loading Warning",
                    f"Failed to load {layer_type} layer:\n{file_path_obj.name}\n\n"
                    "Possible issues:\n"
                    "• File format not supported\n"
                    "• File is corrupted or incomplete\n"
                    "• Coordinate system issues\n"
                    "• File is locked by another application"
                )
                return False

        except FileNotFoundError as e:
            print(f"File not found error: {e}")
            QMessageBox.critical(
                self, "File Not Found",
                f"The selected file could not be found:\n{e}"
            )
            return False
        except Exception as e:
            print(f"Error adding layer: {e}")
            traceback.print_exc()
            QMessageBox.critical(
                self, "Layer Loading Error",
                f"Error loading {layer_type} layer:\n{str(e)}\n\n"
                "Check the console output for detailed error information."
            )
            return False

    def zoom_to_layer_extent(self):
        """Zoom to extent of all layers"""
        try:
            if hasattr(self.map_viewer, 'zoom_to_extent'):
                self.map_viewer.zoom_to_extent()
        except Exception as e:
            print(f"Error zooming to extent: {e}")

    def open_raster_file(self):
        """Open raster file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Raster File", "",
            "Raster Files (*.tif *.tiff *.img *.jpg *.png);;All Files (*)"
        )
        if file_path:
            print(f"Selected raster file: {file_path}")
            self.raster_panel.load_file(file_path)

    def open_vector_file(self):
        """Open vector file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Vector File", "",
            "Vector Files (*.shp *.kml *.geojson *.gpkg);;All Files (*)"
        )
        if file_path:
            print(f"Selected vector file: {file_path}")
            self.vector_panel.load_file(file_path)

    def start_processing(self, operation_func, *args, **kwargs):
        """Start processing operation in separate thread with enhanced monitoring"""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Processing", "Another operation is running")
            return

        print(f"Starting processing operation: {operation_func.__name__ if hasattr(operation_func, '__name__') else 'Unknown'}")

        # Store current operation info
        self.current_operation = {
            'function': operation_func,
            'args': args,
            'kwargs': kwargs
        }

        # Create and configure worker thread
        self.worker_thread = ProcessingWorker(operation_func, *args, **kwargs)
        self.worker_thread.finished.connect(self.processing_finished)
        self.worker_thread.progress.connect(self.update_progress)
        self.worker_thread.error.connect(self.processing_error)

        # Update UI to show processing state
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Processing...")

        # Disable processing panels during operation
        self.raster_panel.setEnabled(False)
        self.vector_panel.setEnabled(False)

        # Start processing
        self.worker_thread.start()

    def start_processing_simple(self, operation_func):
        """Start processing operation with simplified signal"""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Processing", "Another operation is running")
            return

        # Create worker thread with the operation function
        self.worker_thread = ProcessingWorker(operation_func)
        self.worker_thread.finished.connect(self.processing_finished)
        self.worker_thread.progress.connect(self.update_progress)
        self.worker_thread.error.connect(self.processing_error)

        # Update UI
        self.progress_bar.setVisible(True)
        self.status_label.setText("Processing...")
        self.raster_panel.setEnabled(False)
        self.vector_panel.setEnabled(False)

        # Start processing
        self.worker_thread.start()

    def processing_finished(self, success: bool, message: str, output_path: str):
        """Handle processing completion with automatic output loading"""
        # Re-enable UI
        self.progress_bar.setVisible(False)
        self.raster_panel.setEnabled(True)
        self.vector_panel.setEnabled(True)

        if success:
            self.status_label.setText("Processing completed")
            QMessageBox.information(self, "Success", message)

            # Automatically add processed output to map if path is provided
            if output_path and output_path.strip():
                try:
                    output_file = Path(output_path)
                    if output_file.exists():
                        print(f"Adding processed output to map: {output_path}")

                        # Determine file type and add to map
                        suffix = output_file.suffix.lower()
                        if suffix in ['.tif', '.tiff', '.img']:
                            layer_type = 'raster'
                        elif suffix in ['.shp', '.geojson', '.kml', '.gpkg']:
                            layer_type = 'vector'
                        else:
                            print(f"Unknown output file type: {suffix}")
                            return

                        # Add to map with a delay to ensure file is fully written
                        QTimer.singleShot(2000, lambda: self.add_processed_output_to_map(output_path, layer_type))

                    else:
                        print(f"Output file not found: {output_path}")

                except Exception as e:
                    print(f"Error handling processed output: {e}")

        else:
            self.status_label.setText("Processing failed")
            QMessageBox.critical(self, "Processing Error", f"Processing failed:\n{message}")

        # Clear current operation
        self.current_operation = None

    def processing_error(self, error_message: str):
        """Handle processing errors"""
        print(f"Processing error received: {error_message}")
        self.progress_bar.setVisible(False)
        self.raster_panel.setEnabled(True)
        self.vector_panel.setEnabled(True)
        self.status_label.setText("Processing error")

    def update_progress(self, value: int):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About GIS Processing Tool",
            "GIS Processing Tool v1.0\n\n"
            "Professional raster and vector data processing application.\n"
            "Built with Python, PyQt5, and geospatial libraries.\n\n"
            "Features:\n"
            "• Raster processing (clipping, reprojection, resampling)\n"
            "• Vector operations (overlay analysis, transformations)\n"
        )

    def closeEvent(self, event):
        """Handle application closing"""
        # Stop any running processing
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Processing operation is running. Do you want to force quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.worker_thread.terminate()
                self.worker_thread.wait()
            else:
                event.ignore()
                return

        # Clean up map viewer if it has cleanup method
        if hasattr(self.map_viewer, 'cleanup_temp_files'):
            self.map_viewer.cleanup_temp_files()

        event.accept()