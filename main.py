import sys
import traceback
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
sys.path.insert(0, str(Path(__file__).parent))
from main_window import MainWindow
from settings import SettingsManager
from loggers import GISLogger

class GISProcessorApp:
    """Main application class"""

    def __init__(self):
        self.app = None
        self.main_window = None
        self.settings_manager = SettingsManager()
        self.logger = GISLogger()

    def setup_application(self):
        """Initialize PyQt application"""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("GIS Processing Tool")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("YourName")

        # Set application style
        self.app.setStyle('Fusion')  # Modern cross-platform style

        # Apply dark theme (optional)
        # self.apply_dark_theme()

        # Setup exception handling
        sys.excepthook = self.handle_exception

    def apply_dark_theme(self):
        """Apply dark theme to application"""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        QPushButton {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 8px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #4c4c4c;
        }
        QPushButton:pressed {
            background-color: #2c2c2c;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
        }
        QTabBar::tab {
            background-color: #3c3c3c;
            padding: 8px 16px;
            border: 1px solid #555555;
        }
        QTabBar::tab:selected {
            background-color: #4c4c4c;
        }
        QTableWidget {
            background-color: #3c3c3c;
            border: 1px solid #555555;
            gridline-color: #555555;
        }
        QTableWidget::item {
            padding: 5px;
        }
        QHeaderView::section {
            background-color: #4c4c4c;
            border: 1px solid #555555;
            padding: 5px;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 2px;
        }
        QStatusBar {
            background-color: #3c3c3c;
            border-top: 1px solid #555555;
        }
        """
        self.app.setStyleSheet(dark_stylesheet)

    def create_main_window(self):
        """Create and configure main window"""
        self.main_window = MainWindow()

        # Apply saved window settings
        settings = self.settings_manager.settings
        self.main_window.resize(settings.window_width, settings.window_height)
        self.main_window.show()

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.error(f"Unhandled exception: {error_msg}")

        # Show user-friendly error dialog
        QMessageBox.critical(
            None, "Unexpected Error",
            f"An unexpected error occurred:\n{exc_value}\n\n"
            "Please check the log files for more details."
        )

    def run(self):
        """Run the application"""
        try:
            self.logger.info("Starting GIS Processing Tool")
            self.setup_application()
            self.create_main_window()

            # Start event loop
            exit_code = self.app.exec()

            # Save settings on exit
            self.settings_manager.save_settings()
            self.logger.info("Application closed")
            return exit_code

        except Exception as e:
            self.logger.error(f"Failed to start application: {e}")
            QMessageBox.critical(
                None, "Startup Error",
                f"Failed to start the application:\n{e}"
            )
            return 1


def main():
    """Main entry point"""
    app = GISProcessorApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())