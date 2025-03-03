def test_dependencies():
    try:
        import cv2
        print("OpenCV version:", cv2.__version__)
    except ImportError:
        print("Error: OpenCV not installed properly")
        
    try:
        from pyzbar import pyzbar
        print("pyzbar installed successfully")
    except ImportError:
        print("Error: pyzbar not installed properly")
        
    try:
        import numpy as np
        print("NumPy version:", np.__version__)
    except ImportError:
        print("Error: NumPy not installed properly")

if __name__ == "__main__":
    test_dependencies() 