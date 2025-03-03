import cv2
from pyzbar.pyzbar import decode
import numpy as np
import sqlite3
from datetime import datetime
import os
import requests

def check_database_for_vin(vin_number):
    """Check if scanned value exists in cloud database"""
    try:
        headers = {
            'X-API-Key': os.getenv('API_KEY')
        }
        response = requests.get(
            f"{os.getenv('API_URL')}/api/check_vin",
            params={'vin': vin_number},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('found'):
                return True, f"Found match: {data['description']}"
            return False, "Value not found in database"
        else:
            return False, f"API error: {response.status_code}"
    except Exception as e:
        return False, f"Error checking VIN: {str(e)}"

def draw_status_overlay(frame, message, color=(255, 255, 255)):
    """Draw status message overlay"""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 100), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, message, (20, 60), font, 1.0, color, 3)

def test_camera():
    """Test if camera is working"""
    print("Testing camera access...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not access camera")
        return False
    
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Could not read frame from camera")
        return False
    
    print("SUCCESS: Camera is working")
    cap.release()
    return True

def test_qr_detection():
    """Test QR code detection and database checking"""
    print("\nTesting QR code detection and database checking...")
    print("Please show a QR code to the camera")
    print("Press 'q' to quit the test")
    
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        display_frame = frame.copy()
        decoded_objects = decode(frame)
        
        if decoded_objects:
            for obj in decoded_objects:
                # Draw rectangle around QR code
                points = obj.polygon
                if points is not None and len(points) > 0:
                    pts = np.array(points, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(display_frame, [pts], True, (0, 255, 0), 3)
                
                # Decode and check database
                try:
                    vin_number = obj.data.decode('utf-8')
                    print(f"\nDetected VIN: {vin_number}")
                    
                    # Show checking message
                    draw_status_overlay(display_frame, f"Checking database for: {vin_number}", (255, 165, 0))
                    cv2.imshow('QR Code Test', display_frame)
                    cv2.waitKey(1000)  # Show checking message for 1 second
                    
                    # Check database
                    found, message = check_database_for_vin(vin_number)
                    print(f"Database check result: {message}")
                    
                    # Show result
                    color = (0, 255, 0) if found else (0, 0, 255)  # Green if found, Red if not
                    draw_status_overlay(display_frame, message, color)
                    cv2.imshow('QR Code Test', display_frame)
                    cv2.waitKey(2000)  # Show result for 2 seconds
                    
                except Exception as e:
                    print(f"Error processing VIN: {str(e)}")
                    draw_status_overlay(display_frame, f"Error: {str(e)}", (0, 0, 255))
        else:
            draw_status_overlay(display_frame, "Ready to scan VIN QR Code...")
        
        cv2.imshow('QR Code Test', display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    print("=== VIN Scanner Test Suite ===")
    
    # Test 1: Camera Access
    if not test_camera():
        return
        
    # Test 2: QR Detection and Database Check
    test_qr_detection()
    
if __name__ == "__main__":
    main() 