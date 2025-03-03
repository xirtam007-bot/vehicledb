import sqlite3
from datetime import datetime
import sys
import subprocess
import pyodbc
import pandas as pd
import os
import csv
from io import StringIO
import re

def try_pyodbc_connection():
    """Try to connect using pyodbc with different drivers"""
    drivers = [
        '{Microsoft Access Driver (*.mdb, *.accdb)}',
        '{Microsoft Access Driver}',
        '{Microsoft Access ODBC Driver}',
        '{Microsoft Office Access Driver (*.mdb, *.accdb)}',
        'Microsoft.ACE.OLEDB.12.0'
    ]
    
    for driver in drivers:
        try:
            conn_str = f"DRIVER={driver};DBQ={os.path.abspath('dave.accdb')}"
            conn = pyodbc.connect(conn_str)
            print(f"Successfully connected using {driver}")
            return conn
        except Exception as e:
            print(f"Failed with driver {driver}: {str(e)}")
    return None

def try_mdb_tools():
    """Try to use mdb-tools to extract data"""
    try:
        # Get list of tables
        tables = subprocess.check_output(['mdb-tables', 'dave.accdb']).decode().strip().split(' ')
        print(f"Found tables: {tables}")
        
        # Try to extract data from each table
        for table in tables:
            try:
                data = subprocess.check_output(['mdb-export', 'dave.accdb', table]).decode()
                if 'VIN' in data.upper():
                    print(f"Found potential VIN data in table: {table}")
                    return table, data
            except:
                continue
    except Exception as e:
        print(f"MDB Tools error: {str(e)}")
    return None, None

def try_pandas_connection():
    """Try to connect using pandas"""
    try:
        conn_str = (
            r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
            f"DBQ={os.path.abspath('dave.accdb')};"
        )
        return pd.read_sql('SELECT * FROM YourTableName', f'access:///{conn_str}')
    except Exception as e:
        print(f"Pandas connection failed: {str(e)}")
    return None

def extract_vin(text):
    """Extract any sequence as a potential VIN from text"""
    if not text:
        return None
    
    # Convert to uppercase and clean the text
    text = str(text).upper().strip()
    
    # Split by common delimiters and take the first non-empty part
    parts = re.split(r'[,;\s]+', text)
    for part in parts:
        if part:  # Return first non-empty part
            return part
    
    return None

def init_database():
    """Initialize SQLite database with VIN-like sequences from descriptions"""
    try:
        # Create SQLite database
        sqlite_conn = sqlite3.connect('vin_database.db')
        sqlite_cursor = sqlite_conn.cursor()
        
        # Drop existing table if it exists
        sqlite_cursor.execute('DROP TABLE IF EXISTS vin_records')
        
        # Create table for VIN records
        sqlite_cursor.execute('''
            CREATE TABLE IF NOT EXISTS vin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vin_value TEXT UNIQUE NOT NULL,
                description TEXT,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        print("\nExtracting values from Job table descriptions...")
        
        # Export Job table
        export_cmd = ['mdb-export', 'dave.accdb', 'Job']
        export_process = subprocess.Popen(export_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        csv_output, error = export_process.communicate()
        
        if error:
            print(f"Error exporting data: {error.decode()}")
            return
            
        # Parse CSV data
        csv_data = StringIO(csv_output.decode())
        reader = csv.DictReader(csv_data)
        
        # Import values
        count = 0
        for row in reader:
            try:
                description = row.get('Description') or row.get('description')
                if description:
                    print(f"\nChecking description: {description}")
                    value = extract_vin(description)
                    if value:
                        sqlite_cursor.execute(
                            'INSERT OR IGNORE INTO vin_records (vin_value, description) VALUES (?, ?)', 
                            (value, description)
                        )
                        count += 1
                        print(f"Found value: {value}")
                        print(f"From description: {description}")
                    else:
                        print("No value found in this description")
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue

        sqlite_conn.commit()
        print(f"\nSuccessfully imported {count} values")
        
        # Show what was imported
        print("\nImported values:")
        sqlite_cursor.execute('SELECT * FROM vin_records')
        for row in sqlite_cursor.fetchall():
            print(f"ID: {row[0]}, Value: {row[1]}")
            print(f"From description: {row[2]}")
            print(f"Date: {row[3]}\n")
        
    except Exception as e:
        print(f"Error during import: {str(e)}")
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()

if __name__ == "__main__":
    init_database() 