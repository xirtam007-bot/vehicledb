from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps
import certifi
import logging
import time
from pymongo.errors import AutoReconnect

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
API_KEY = os.getenv('API_KEY')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        logger.info("Creating new MongoDB client connection")
        try:
            # Parse connection string first to validate format
            _mongo_client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                tlsCAFile=certifi.where()
            )
            
            # Test connection immediately
            _mongo_client.admin.command('ping')
            
            # Log topology information safely
            try:
                topology = _mongo_client.topology_description
                logger.info(f"MongoDB topology type: {topology.topology_type_name}")
                
                # Safe server logging
                for server in topology.server_descriptions().values():
                    if hasattr(server, 'address'):
                        logger.info(f"MongoDB server: {server.address}")
                    else:
                        logger.warning("Server description missing address attribute")
            except Exception as log_error:
                logger.warning(f"Non-critical error logging topology: {str(log_error)}")
                
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {str(e)}")
            _mongo_client = None
            raise
    return _mongo_client

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({'error': 'Invalid API key'}), 401
    return decorated

@app.route('/api/check_vin', methods=['GET'])
@require_api_key
def check_vin():
    vin = request.args.get('vin')
    if not vin:
        return jsonify({'error': 'No VIN provided'}), 400
        
    db = get_mongo_client().vin_database
    result = db.vin_records.find_one({'vin_value': vin})
    
    if result:
        return jsonify({
            'found': True,
            'description': result['description'],
            'scan_date': result['scan_date']
        })
    return jsonify({'found': False})

@app.route('/api/add_vin', methods=['POST'])
@require_api_key
def add_vin():
    data = request.json
    if not data or 'vin_value' not in data:
        return jsonify({'error': 'No VIN provided'}), 400
        
    db = get_mongo_client().vin_database
    try:
        result = db.vin_records.update_one(
            {'vin_value': data['vin_value']},
            {
                '$set': {
                    'vin_value': data['vin_value'],
                    'description': data.get('description', ''),
                    'scan_date': datetime.utcnow()
                }
            },
            upsert=True
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) 