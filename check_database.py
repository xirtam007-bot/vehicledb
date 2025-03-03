import sqlite3

def check_database():
    """Check the contents of the VIN database"""
    try:
        conn = sqlite3.connect('vin_database.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vin_records'")
        if not cursor.fetchone():
            print("Table 'vin_records' does not exist!")
            return
            
        # Get record count
        cursor.execute('SELECT COUNT(*) FROM vin_records')
        count = cursor.fetchone()[0]
        print(f"\nTotal records in database: {count}")
        
        # Show all records
        cursor.execute('SELECT * FROM vin_records')
        records = cursor.fetchall()
        print("\nAll records:")
        for record in records:
            print(f"ID: {record[0]}, VIN: {record[1]}, Date: {record[2]}")
            
    except Exception as e:
        print(f"Error checking database: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database() 