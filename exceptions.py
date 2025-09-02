class GISProcessingError(Exception):
    """Base exception for GIS processing errors"""
    pass

class ProjectionError(GISProcessingError):
    """Raised when projection operations fail"""
    pass

class DataFormatError(GISProcessingError):
    """Raised when data format is unsupported or corrupted"""
    pass

class GeometryError(GISProcessingError):
    """Raised when geometry operations fail"""
    pass

class FileAccessError(GISProcessingError):
    """Raised when file cannot be read or written"""
    pass