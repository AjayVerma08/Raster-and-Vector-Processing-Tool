import sys
from pathlib import Path

project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from main import main
    if __name__ == "__main__":
        sys.exit(main())
except ImportError as e:
    print(f"Error importing main module: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)