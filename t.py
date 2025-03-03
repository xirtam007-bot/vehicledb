import cv2
from pyzbar.pyzbar import decode
import sqlite3
from datetime import datetime
import numpy as np
import tkinter as tk
from tkinter import ttk

class VINScanner:
    def __init__(self, db_path='vin_database.db'):
        self.db_path = db_path
        self.setup_database()
        self.status_message = ""
        self.status_color = (0, 255, 0)
        self.last_scan_time = 0
        self.scan_cooldown = 2.0
        self.scanning_active = True
        self.cap = None
        
    def setup_database(self):
        """Initialize the SQLite database with a VIN records table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin_number TEXT UNIQUE NOT NULL,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def show_status_window(self, vin_number, success, message):
        """Show status window with scan results"""
        # Create status window
        status_window = tk.Tk()
        status_window.title("Scan Results")
        status_window.geometry("400x300")
        
        # Style configuration
        style = ttk.Style()
        style.configure("Success.TLabel", foreground="green", font=("Helvetica", 12))
        style.configure("Error.TLabel", foreground="red", font=("Helvetica", 12))
        style.configure("Header.TLabel", font=("Helvetica", 14, "bold"))
        style.configure("Warning.TLabel", foreground="red", font=("Helvetica", 14, "bold"))
        
        # Create and pack widgets
        header = ttk.Label(
            status_window, 
            text="VIN Scan Results", 
            style="Header.TLabel"
        )
        header.pack(pady=20)
        
        # VIN label - red if not in database
        vin_style = "Warning.TLabel" if not success else "Header.TLabel"
        vin_label = ttk.Label(
            status_window,
            text=f"VIN: {vin_number}",
            style=vin_style
        )
        vin_label.pack(pady=10)
        
        # Status message - always red if not successful
        status_label = ttk.Label(
            status_window,
            text=message,
            style="Error.TLabel" if not success else "Success.TLabel"
        )
        status_label.pack(pady=10)
        
        # Add database info if successful, otherwise show warning
        if success:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_info = ttk.Label(
                status_window,
                text=f"Added to database at:\n{timestamp}",
                style="Success.TLabel"
            )
            db_info.pack(pady=10)
        else:
            warning_label = ttk.Label(
                status_window,
                text="VIN NOT FOUND IN DATABASE",
                style="Warning.TLabel"
            )
            warning_label.pack(pady=10)
        
        # Continue button
        continue_btn = ttk.Button(
            status_window,
            text="Scan Next VIN",
            command=lambda: self.resume_scanning(status_window)
        )
        continue_btn.pack(pady=20)
        
        # Center the window on screen
        status_window.update_idletasks()
        width = status_window.winfo_width()
        height = status_window.winfo_height()
        x = (status_window.winfo_screenwidth() // 2) - (width // 2)
        y = (status_window.winfo_screenheight() // 2) - (height // 2)
        status_window.geometry(f'{width}x{height}+{x}+{y}')
        
        status_window.mainloop()
    
    def resume_scanning(self, status_window):
        """Resume scanning after status window is closed"""
        status_window.destroy()
        self.scanning_active = True
        self.scan_qr_code()

    def scan_qr_code(self):
        """Scan QR code using MacBook camera"""
        self.cap = cv2.VideoCapture(0)
        window_name = 'VIN QR Code Scanner (Press Q to quit)'
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        while self.scanning_active:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            display_frame = frame.copy()
            
            try:
                decoded_objects = decode(frame)
                
                for obj in decoded_objects:
                    try:
                        vin_number = obj.data.decode('utf-8')
                        print(f"\nScanned VIN: {vin_number}")  # Debug print
                        
                        # Force display update for checking message
                        check_frame = frame.copy()
                        self.draw_status_overlay(
                            check_frame,
                            f"CHECKING DATABASE\nVIN: {vin_number}",
                            (0, 255, 255)
                        )
                        cv2.imshow(window_name, check_frame)
                        cv2.waitKey(1000)  # Wait 1 second
                        
                        print("Checking database...")  # Debug print
                        success, message = self.process_vin(vin_number)
                        print(f"Database check result: {message}")  # Debug print
                        
                        # Show result
                        result_color = (0, 255, 0) if success else (0, 0, 255)
                        result_frame = frame.copy()
                        self.draw_status_overlay(
                            result_frame,
                            f"RESULT: {message}\nVIN: {vin_number}",
                            result_color
                        )
                        cv2.imshow(window_name, result_frame)
                        cv2.waitKey(2000)  # Wait 2 seconds
                        
                        # Close camera and show status window
                        self.scanning_active = False
                        self.cap.release()
                        cv2.destroyAllWindows()
                        self.show_status_window(vin_number, success, message)
                        return
                        
                    except Exception as e:
                        print(f"Error processing VIN: {str(e)}")  # Debug print
                        continue
                
                # Show ready message
                self.draw_status_overlay(display_frame, "Ready to scan VIN QR Code...")
                
            except Exception as e:
                print(f"Scanning error: {str(e)}")  # Debug print
                if "Assertion" not in str(e):
                    self.draw_status_overlay(display_frame, f"Error: {str(e)}", (0, 0, 255))

            cv2.imshow(window_name, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def draw_status_overlay(self, frame, message, text_color=None):
        """Draw status overlay on frame"""
        overlay_height = 150  # Increased height for multi-line text
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], overlay_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)  # More opaque overlay
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2  # Larger font
        thickness = 3  # Thicker text
        
        # Split message into lines and display each line
        lines = message.split('\n')
        for i, line in enumerate(lines):
            y_position = 50 + (i * 40)  # Spacing between lines
            x_position = 20
            
            # Add black outline for better visibility
            cv2.putText(frame, line, (x_position, y_position),
                        font, font_scale, (0, 0, 0), thickness + 2)
            cv2.putText(frame, line, (x_position, y_position),
                        font, font_scale, text_color if text_color else (255, 255, 255), thickness)

    def process_vin(self, vin_number):
        """Process scanned VIN number"""
        print(f"\nProcessing VIN: {vin_number}")  # Debug print
        
        if not self.is_valid_vin(vin_number):
            print("Invalid VIN format")  # Debug print
            return False, "Invalid VIN format"
            
        # Check if VIN exists in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            print(f"Checking database for VIN: {vin_number}")  # Debug print
            cursor.execute('SELECT COUNT(*) FROM vin_records WHERE vin_number = ?', (vin_number,))
            count = cursor.fetchone()[0]
            print(f"Found {count} matches in database")  # Debug print
            
            if count == 0:
                return False, "VIN not found in database"
            else:
                return True, "VIN found in database"
                
        except Exception as e:
            print(f"Database error: {str(e)}")  # Debug print
            return False, f"Error checking VIN: {str(e)}"
        finally:
            conn.close()

    def is_valid_vin(self, vin):
        """Basic VIN validation (17 characters, alphanumeric)"""
        if len(vin) != 17:
            return False
        return vin.isalnum()

def main():
    scanner = VINScanner()
    scanner.scan_qr_code()

if __name__ == "__main__":
    main()
