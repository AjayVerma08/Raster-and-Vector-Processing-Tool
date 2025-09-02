from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QComboBox, QLabel,
                             QLineEdit, QGroupBox,
                             QDoubleSpinBox, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import pyqtSignal
from pathlib import Path
from raster_processor import RasterProcessor


class RasterPanel(QWidget):
    """Panel for raster processing operations"""
    processing_requested = pyqtSignal(object)  # func, input, output, params
    file_loaded = pyqtSignal(str)


    def __init__(self):
        super().__init__()
        self.output_format = None
        self.output_file_input = None
        self.reclass_table = None
        self.resampling_method = None
        self.scale_factor = None
        self.custom_crs_input = None
        self.crs_combo = None
        self.raster_clip_file = None
        self.vector_clip_file = None
        self.browse_button = None
        self.file_label = None
        self.current_file = None
        self.setup_ui()

    def setup_ui(self):
        """Setup raster processing UI"""
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
        self.setup_clipping_section(layout)
        self.setup_projection_section(layout)
        self.setup_resampling_section(layout)
        self.setup_reclassification_section(layout)

        # Output settings
        self.setup_output_section(layout)

        layout.addStretch()

    def setup_clipping_section(self, parent_layout):
        """Setup clipping operations"""
        clip_group = QGroupBox("Clipping Operations")
        clip_layout = QVBoxLayout(clip_group)

        # Clip with vector
        vector_clip_layout = QHBoxLayout()
        self.vector_clip_file = QLineEdit()
        self.vector_clip_file.setPlaceholderText("Select vector file for clipping...")
        vector_browse_btn = QPushButton("Browse Vector")
        vector_browse_btn.clicked.connect(self.browse_vector_clip)
        clip_vector_btn = QPushButton("Clip with Vector")
        clip_vector_btn.clicked.connect(self.clip_with_vector)

        vector_clip_layout.addWidget(QLabel("Vector:"))
        vector_clip_layout.addWidget(self.vector_clip_file)
        vector_clip_layout.addWidget(vector_browse_btn)
        vector_clip_layout.addWidget(clip_vector_btn)

        # Clip with raster
        raster_clip_layout = QHBoxLayout()
        self.raster_clip_file = QLineEdit()
        self.raster_clip_file.setPlaceholderText("Select raster file for clipping...")
        raster_browse_btn = QPushButton("Browse Raster")
        raster_browse_btn.clicked.connect(self.browse_raster_clip)
        clip_raster_btn = QPushButton("Clip with Raster")
        clip_raster_btn.clicked.connect(self.clip_with_raster)

        raster_clip_layout.addWidget(QLabel("Raster:"))
        raster_clip_layout.addWidget(self.raster_clip_file)
        raster_clip_layout.addWidget(raster_browse_btn)
        raster_clip_layout.addWidget(clip_raster_btn)

        clip_layout.addLayout(vector_clip_layout)
        clip_layout.addLayout(raster_clip_layout)
        parent_layout.addWidget(clip_group)

    def setup_projection_section(self, parent_layout):
        """Setup reprojection operations"""
        proj_group = QGroupBox("Projection Operations")
        proj_layout = QVBoxLayout(proj_group)

        proj_control_layout = QHBoxLayout()

        self.crs_combo = QComboBox()
        self.crs_combo.addItems([
            "EPSG:4326 - WGS84 Geographic",
            "EPSG:3857 - Web Mercator",
            "EPSG:32633 - UTM Zone 33N",
            "EPSG:32643 - UTM Zone 43N",
            "EPSG:2157 - Irish Grid",
            "Custom..."
        ])

        self.custom_crs_input = QLineEdit()
        self.custom_crs_input.setPlaceholderText("Enter EPSG code or PROJ string...")
        self.custom_crs_input.setEnabled(False)

        self.crs_combo.currentTextChanged.connect(self.on_crs_changed)

        reproject_btn = QPushButton("Reproject")
        reproject_btn.clicked.connect(self.reproject_raster)

        proj_control_layout.addWidget(QLabel("Target CRS:"))
        proj_control_layout.addWidget(self.crs_combo)
        proj_control_layout.addWidget(self.custom_crs_input)
        proj_control_layout.addWidget(reproject_btn)

        proj_layout.addLayout(proj_control_layout)
        parent_layout.addWidget(proj_group)

    def setup_resampling_section(self, parent_layout):
        """Setup resampling operations"""
        resample_group = QGroupBox("Resampling Operations")
        resample_layout = QHBoxLayout(resample_group)

        self.scale_factor = QDoubleSpinBox()
        self.scale_factor.setRange(0.1, 10.0)
        self.scale_factor.setValue(1.0)
        self.scale_factor.setSingleStep(0.1)

        self.resampling_method = QComboBox()
        self.resampling_method.addItems([
            "nearest", "bilinear", "cubic", "average", "mode"
        ])

        resample_btn = QPushButton("Resample")
        resample_btn.clicked.connect(self.resample_raster)

        resample_layout.addWidget(QLabel("Scale Factor:"))
        resample_layout.addWidget(self.scale_factor)
        resample_layout.addWidget(QLabel("Method:"))
        resample_layout.addWidget(self.resampling_method)
        resample_layout.addWidget(resample_btn)

        parent_layout.addWidget(resample_group)

    def setup_reclassification_section(self, parent_layout):
        """Setup reclassification operations"""
        reclass_group = QGroupBox("Reclassification")
        reclass_layout = QVBoxLayout(reclass_group)

        # Classification rules table
        self.reclass_table = QTableWidget(0, 3)
        self.reclass_table.setHorizontalHeaderLabels(["Min Value", "Max Value", "New Value"])
        header = self.reclass_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Control buttons
        table_controls = QHBoxLayout()
        add_rule_btn = QPushButton("Add Rule")
        add_rule_btn.clicked.connect(self.add_reclass_rule)
        remove_rule_btn = QPushButton("Remove Rule")
        remove_rule_btn.clicked.connect(self.remove_reclass_rule)
        reclassify_btn = QPushButton("Reclassify")
        reclassify_btn.clicked.connect(self.reclassify_raster)

        table_controls.addWidget(add_rule_btn)
        table_controls.addWidget(remove_rule_btn)
        table_controls.addStretch()
        table_controls.addWidget(reclassify_btn)

        reclass_layout.addWidget(self.reclass_table)
        reclass_layout.addLayout(table_controls)
        parent_layout.addWidget(reclass_group)

    def setup_output_section(self, parent_layout):
        """Setup output configuration"""
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)

        # Output file selection
        output_file_layout = QHBoxLayout()
        self.output_file_input = QLineEdit()
        self.output_file_input.setPlaceholderText("Choose output file location...")
        output_browse_btn = QPushButton("Browse...")
        output_browse_btn.clicked.connect(self.browse_output_file)

        output_file_layout.addWidget(QLabel("Output File:"))
        output_file_layout.addWidget(self.output_file_input)
        output_file_layout.addWidget(output_browse_btn)

        # Output format
        format_layout = QHBoxLayout()
        self.output_format = QComboBox()
        self.output_format.addItems(["GeoTIFF", "IMG", "PNG", "JPEG"])

        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.output_format)
        format_layout.addStretch()

        output_layout.addLayout(output_file_layout)
        output_layout.addLayout(format_layout)
        parent_layout.addWidget(output_group)

    def browse_file(self):
        """Browse for input raster file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Raster File", "",
            "Raster Files (*.tif *.tiff *.img *.jpg *.png);;NetCDF (*.nc);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        # """Load raster file"""
        # self.current_file = Path(file_path)
        # self.file_label.setText(f"File: {self.current_file.name}")
        """Load raster file"""
        try:
            self.current_file = Path(file_path)
            self.file_label.setText(f"File: {self.current_file.name}")
            # Emit signal that file is loaded
            self.file_loaded.emit(str(file_path))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def browse_vector_clip(self):
        """Browse for vector clipping file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Vector File", "",
            "Vector Files (*.shp *.kml *.geojson *.gpkg);;All Files (*)"
        )
        if file_path:
            self.vector_clip_file.setText(file_path)

    def browse_raster_clip(self):
        """Browse for raster clipping file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Raster File", "",
            "Raster Files (*.tif *.tiff *.img);;NetCDF (*.nc);;All Files (*)"
        )
        if file_path:
            self.raster_clip_file.setText(file_path)

    def browse_output_file(self):
        """Browse for output file location"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output File", "",
            "GeoTIFF (*.tif);;IMG (*.img);;PNG (*.png);;NetCDF (*.nc);;All Files (*)"
        )
        if file_path:
            self.output_file_input.setText(file_path)

    def on_crs_changed(self, text):
        """Handle CRS selection change"""
        self.custom_crs_input.setEnabled(text == "Custom...")

    def add_reclass_rule(self):
        """Add new reclassification rule"""
        row = self.reclass_table.rowCount()
        self.reclass_table.insertRow(row)

        # default values
        self.reclass_table.setItem(row, 0, QTableWidgetItem("0"))
        self.reclass_table.setItem(row, 1, QTableWidgetItem("100"))
        self.reclass_table.setItem(row, 2, QTableWidgetItem("1"))

    def remove_reclass_rule(self):
        """Remove selected reclassification rule"""
        current_row = self.reclass_table.currentRow()
        if current_row >= 0:
            self.reclass_table.removeRow(current_row)

    def get_reclass_rules(self):
        """Get reclassification rules from table"""
        rules = {}
        for row in range(self.reclass_table.rowCount()):
            try:
                min_val = float(self.reclass_table.item(row, 0).text())
                max_val = float(self.reclass_table.item(row, 1).text())
                new_val = int(self.reclass_table.item(row, 2).text())
                rules[(min_val, max_val)] = new_val
            except (ValueError, AttributeError):
                continue
        return rules

    def get_target_crs(self):
        """Get selected target CRS"""
        crs_text = self.crs_combo.currentText()
        if crs_text == "Custom...":
            return self.custom_crs_input.text()
        else:
            return crs_text.split(" - ")[0]  # Extract EPSG code

    def validate_inputs(self):
        """Validate input parameters"""
        if not self.current_file:
            raise ValueError("No input file selected")
        if not self.output_file_input.text():
            raise ValueError("No output file specified")

    # Processing operation methods
    def clip_with_vector(self):
        """Initiate vector clipping"""
        try:
            self.validate_inputs()
            if not self.vector_clip_file.text():
                raise ValueError("No vector file selected for clipping")

            operation = lambda: RasterProcessor.clip_raster_with_vector(
                self.current_file,
                Path(self.vector_clip_file.text()),
                Path(self.output_file_input.text())
            )

            self.processing_requested.emit(operation)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def clip_with_raster(self):
        """Initiate raster clipping"""
        try:
            self.validate_inputs()
            if not self.raster_clip_file.text():
                raise ValueError("No raster file selected for clipping")

            operation = lambda: RasterProcessor.clip_raster_with_raster(
                self.current_file,
                Path(self.raster_clip_file.text()),
                Path(self.output_file_input.text())
            )

            self.processing_requested.emit(operation)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def reproject_raster(self):
        """Initiate raster reprojection"""
        try:
            self.validate_inputs()
            target_crs = self.get_target_crs()
            if not target_crs:
                raise ValueError("No target CRS specified")

            operation = lambda: RasterProcessor.reproject_raster(
                self.current_file,
                Path(self.output_file_input.text()),
                target_crs,
                self.resampling_method.currentText()
            )

            self.processing_requested.emit(operation)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def resample_raster(self):
        """Initiate raster resampling"""
        try:
            self.validate_inputs()

            operation = lambda: RasterProcessor.resample_raster(
                self.current_file,
                Path(self.output_file_input.text()),
                self.scale_factor.value(),
                self.resampling_method.currentText()
            )

            self.processing_requested.emit(operation)
        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))

    def reclassify_raster(self):
        """Initiate raster reclassification"""
        try:
            self.validate_inputs()
            rules = self.get_reclass_rules()
            if not rules:
                raise ValueError("No reclassification rules defined")

            operation = lambda: RasterProcessor.reclassify_raster(
                self.current_file,
                Path(self.output_file_input.text()),
                rules
            )

            self.processing_requested.emit(operation)

        except Exception as e:
            QMessageBox.warning(self, "Input Error", str(e))