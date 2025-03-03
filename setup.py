import os
import subprocess
import sys

def setup_environment():
    """Setup the Python environment with all required dependencies"""
    try:
        # Set the library path for ZBar
        os.environ['DYLD_LIBRARY_PATH'] = '/usr/local/lib'
        
        # Install required packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Test imports
        import cv2
        from pyzbar import pyzbar
        import numpy as np
        
        print("All dependencies installed successfully!")
        print(f"OpenCV version: {cv2.__version__}")
        print(f"NumPy version: {np.__version__}")
        
        # Test camera access
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Warning: Cannot access camera")
        else:
            print("Camera access successful")
            cap.release()
            
    except Exception as e:
        print(f"Error setting up environment: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    setup_environment() 