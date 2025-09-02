from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLabel,
                             QLineEdit, QGroupBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import pyqtSignal
from pathlib import Path
try:
    from vector_processor import VectorProcessor
except ImportError:
    print("Warning: VectorProcessor not available")

    class VectorProcessor:
        @staticmethod
        def clip_vector(*args): return False

        @staticmethod
        def reproject_vector(*args): return False

        @staticmethod
        def erase_vector(*args): return False

        @staticmethod
        def union_vectors(*args): return False

        @staticmethod
        def intersection_vectors(*args): return False

        @staticmethod
        def symmetric_difference_vectors(*args): return False


class VectorPanel(QWidget):
    """Panel for vector processing operations"""
    processing_requested = pyqtSignal(object)  # Processing function with args
    file_loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.vector_custom_crs = None
        self.current_file = None
        self.setup_ui()

    def setup_ui(self):
        """Setup vector processing UI"""
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("Input File")
        file_layout = QVBoxLayout(file_group)

        file_select_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)

        file_select_layout.addWidget(self.file_label)
        file_select_layout.addWidget(self.browse_button)
        file_layout.addLayout(file_select_layout)
        layout.addWidget(file_group)

        # Processing operations
        self.setup_basic_operations(layout)
        self.setup_overlay_operations(layout)
        self.setup_extraction_operations(layout)

        # Output settings
        self.setup_output_section(layout)
        layout.addStretch()

    def setup_basic_operations(self, parent_layout):
        """Setup basic vector operations"""
        basic_group = QGroupBox("Basic Operations")
        basic_layout = QVBoxLayout(basic_group)

        # Clipping
        clip_layout = QHBoxLayout()
        self.clip_file_input = QLineEdit()
        self.clip_file_input.setPlaceholderText("Select clip boundary file...")
        clip_browse_btn = QPushButton("Browse")
        clip_browse_btn.clicked.connect(self.browse_clip_file)
        clip_btn = QPushButton("Clip")
        clip_btn.clicked.connect(self.clip_vector)

        clip_layout.addWidget(QLabel("Clip File:"))
        clip_layout.addWidget(self.clip_file_input)
        clip_layout.addWidget(clip_browse_btn)
        clip_layout.addWidget(clip_btn)

        # Reprojection
        reproj_layout = QHBoxLayout()
        self.vector_crs_combo = QComboBox()
        self.vector_crs_combo.addItems([
            "EPSG:4326 - WGS84 Geographic",
            "EPSG:3857 - Web Mercator",
            "EPSG:32643 - UTM Zone 43N",
            "Custom..."
        ])
        self.vector_custom_crs = QLineEdit()
        self.vector_custom_crs.setPlaceholderText("Custom CRS...")
        self.vector_custom_crs.setEnabled(False)
        self.vector_crs_combo.currentTextChanged.connect(self.on_vector_crs_changed)

        reproj_btn = QPushButton("Reproject")
        reproj_btn.clicked.connect(self.reproject_vector)

        reproj_layout.addWidget(QLabel("Target CRS:"))
        reproj_layout.addWidget(self.vector_crs_combo)
        reproj_layout.addWidget(self.vector_custom_crs)
        reproj_layout.addWidget(reproj_btn)

        basic_layout.addLayout(clip_layout)
        basic_layout.addLayout(reproj_layout)
        parent_layout.addWidget(basic_group)

    def setup_overlay_operations(self, parent_layout):
        """Setup overlay operations"""
        overlay_group = QGroupBox("Overlay Operations")
        overlay_layout = QVBoxLayout(overlay_group)

        # Second file input for overlay operations
        overlay_file_layout = QHBoxLayout()
        self.overlay_file_input = QLineEdit()
        self.overlay_file_input.setPlaceholderText("Select second file for overlay...")
        overlay_browse_btn = QPushButton("Browse")
        overlay_browse_btn.clicked.connect(self.browse_overlay_file)

        overlay_file_layout.addWidget(QLabel("Overlay File:"))
        overlay_file_layout.addWidget(self.overlay_file_input)
        overlay_file_layout.addWidget(overlay_browse_btn)

        # Overlay operation buttons
        overlay_buttons_layout = QHBoxLayout()
        intersection_btn = QPushButton("Intersection")
        intersection_btn.clicked.connect(self.intersection_operation)

        union_btn = QPushButton("Union")
        union_btn.clicked.connect(self.union_operation)

        difference_btn = QPushButton("Difference")
        difference_btn.clicked.connect(self.difference_operation)

        sym_diff_btn = QPushButton("Symmetric Difference")
        sym_diff_btn.clicked.connect(self.symmetric_difference_operation)

        overlay_buttons_layout.addWidget(intersection_btn)
        overlay_buttons_layout.addWidget(union_btn)
        overlay_buttons_layout.addWidget(difference_btn)
        overlay_buttons_layout.addWidget(sym_diff_btn)

        overlay_layout.addLayout(overlay_file_layout)
        overlay_layout.addLayout(overlay_buttons_layout)
        parent_layout.addWidget(overlay_group)

    def setup_extraction_operations(self, parent_layout):
        """Setup extraction operations"""
        extract_group = QGroupBox("Extraction Operations")
        extract_layout = QHBoxLayout(extract_group)

        erase_btn = QPushButton("Erase")
        erase_btn.clicked.connect(self.erase_operation)

        split_btn = QPushButton("Split Features")
        split_btn.clicked.connect(self.split_features)

        extract_layout.addWidget(erase_btn)
        extract_layout.addWidget(split_btn)
        extract_layout.addStretch()
        parent_layout.addWidget(extract_group)

    def setup_output_section(self, parent_layout):
        """Setup output configuration"""
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)

        # Output file
        output_file_layout = QHBoxLayout()
        self.vector_output_file = QLineEdit()
        self.vector_output_file.setPlaceholderText("Choose output file location...")
        vector_output_browse_btn = QPushButton("Browse...")
        vector_output_browse_btn.clicked.connect(self.browse_vector_output)

        output_file_layout.addWidget(QLabel("Output File:"))
        output_file_layout.addWidget(self.vector_output_file)
        output_file_layout.addWidget(vector_output_browse_btn)

        # Output format
        format_layout = QHBoxLayout()
        self.vector_output_format = QComboBox()
        self.vector_output_format.addItems([
            "Shapefile", "GeoJSON", "KML", "GPKG"
        ])

        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.vector_output_format)
        format_layout.addStretch()

        output_layout.addLayout(output_file_layout)
        output_layout.addLayout(format_layout)
        parent_layout.addWidget(output_group)

    def browse_file(self):
        """Browse for input vector file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Vector File", "",
            "Vector Files (*.shp *.kml *.geojson *.gpkg);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        # """Load vector file"""
        # self.current_file = Path(file_path)
        # self.file_label.setText(f"File: {self.current_file.name}")
        """Load vector file"""
        try:
            self.current_file = Path(file_path)
            self.file_label.setText(f"File: {self.current_file.name}")
            # Emit signal that file is loaded
            self.file_loaded.emit(str(file_path))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def browse_clip_file(self):
        """Browse for clip boundary file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Clip Boundary File", "",
            "Vector Files (*.shp *.kml *.geojson *.gpkg);;All Files (*)"
        )
        if file_path:
            self.clip_file_input.setText(file_path)

    def browse_overlay_file(self):
        """Browse for overlay file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Overlay File", "",
            "Vector Files (*.shp *.kml *.geojson *.gpkg);;All Files (*)"
        )
        if file_path:
            self.overlay_file_input.setText(file_path)

    def browse_vector_output(self):
        """Browse for vector output location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Vector Output", "",
            "Shapefile (*.shp);;GeoJSON (*.geojson);;KML (*.kml);;GPKG (*.gpkg)"
        )
        if file_path:
            self.vector_output_file.setText(file_path)

    def on_vector_crs_changed(self, text):
        """Handle vector CRS selection change"""
        self.vector_custom_crs.setEnabled(text == "Custom...")

    def validate_inputs(self, need_overlay=False):
        """Validate vector processing inputs"""
        if not self.current_file:
            raise ValueError("No input file selected")
        if not self.vector_output_file.text():
            raise ValueError("No output file specified")
        if need_overlay and not self.overlay_file_input.text():
            raise ValueError("No overlay file selected")

    def get_vector_target_crs(self):
        """Get target CRS for vector operations"""
        crs_text = self.vector_crs_combo.currentText()
        if crs_text == "Custom...":
            return self.vector_custom_crs.text()
        else:
            return crs_text.split(" - ")[0]

    # Vector operation methods
    def clip_vector(self):
        """Initiate vector clipping"""
        try:
            self.validate_inputs()
            if not self.clip_file_input.text():
                raise ValueError("No clip file selected")

            self.processing_requested.emit(
                lambda: VectorProcessor.clip_vector(
                    self.current_file,
                    Path(self.clip_file_input.text()),
                    Path(self.vector_output_file.text())
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def reproject_vector(self):
        """Initiate vector reprojection"""
        try:
            self.validate_inputs()
            target_crs = self.get_vector_target_crs()
            self.processing_requested.emit(
                lambda: VectorProcessor.reproject_vector(
                    self.current_file,
                    Path(self.vector_output_file.text()),
                    target_crs
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def intersection_operation(self):
        """Perform intersection overlay"""
        try:
            self.validate_inputs(need_overlay=True)
            self.processing_requested.emit(
                lambda: VectorProcessor.intersection_vectors(
                    self.current_file,
                    Path(self.overlay_file_input.text()),
                    Path(self.vector_output_file.text())
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def union_operation(self):
        """Perform union operation"""
        try:
            self.validate_inputs(need_overlay=True)
            self.processing_requested.emit(
                lambda: VectorProcessor.union_vectors(
                    [self.current_file, Path(self.overlay_file_input.text())],
                    Path(self.vector_output_file.text())
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def difference_operation(self):
        """Perform difference operation (erase)"""
        try:
            self.validate_inputs(need_overlay=True)
            self.processing_requested.emit(
                lambda: VectorProcessor.erase_vector(
                    self.current_file,
                    Path(self.overlay_file_input.text()),
                    Path(self.vector_output_file.text())
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def symmetric_difference_operation(self):
        """Perform symmetric difference"""
        try:
            self.validate_inputs(need_overlay=True)
            self.processing_requested.emit(
                lambda: VectorProcessor.symmetric_difference_vectors(
                    self.current_file,
                    Path(self.overlay_file_input.text()),
                    Path(self.vector_output_file.text())
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def erase_operation(self):
        """Perform erase operation"""
        self.difference_operation()  # Same as difference

    def split_features(self):
        """Split vector features (placeholder for advanced implementation)"""
        QMessageBox.information(
            self, "Feature",
            "Split features functionality - Advanced implementation needed"
        )