from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
API_KEY = os.getenv('API_KEY')

def get_db():
    try:
        # Add connection timeouts
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
            connectTimeoutMS=5000,          # 5 second timeout for connecting
            socketTimeoutMS=5000            # 5 second timeout for operations
        )
        # Test the connection
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        return client.vin_database
    except errors.ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timeout: {str(e)}")
        raise
    except errors.ConnectionFailure as e:
        logger.error(f"MongoDB connection failure: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

@app.errorhandler(500)
def handle_500(e):
    logger.error(f"Internal Server Error: {str(e)}")
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(e)
    }), 500

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        logger.warning(f"Invalid API key attempt: {api_key}")
        return jsonify({'error': 'Invalid API key'}), 401
    return decorated

@app.route('/api/check_vin', methods=['GET'])
@require_api_key
def check_vin():
    try:
        vin = request.args.get('vin')
        if not vin:
            return jsonify({'error': 'No VIN provided'}), 400
            
        logger.info(f"Checking VIN: {vin}")
        
        try:
            db = get_db()
            result = db.vin_records.find_one(
                {'vin_value': vin},
                max_time_ms=5000  # 5 second timeout for query
            )
        except (errors.ServerSelectionTimeoutError, errors.ConnectionFailure) as e:
            logger.error(f"Database connection error: {str(e)}")
            return jsonify({
                'error': 'Database connection error',
                'message': 'Unable to connect to database'
            }), 503  # Service Unavailable
        
        if result:
            logger.info(f"Found VIN: {vin}")
            return jsonify({
                'found': True,
                'description': result.get('description'),
                'scan_date': result.get('scan_date')
            })
        logger.info(f"VIN not found: {vin}")
        return jsonify({'found': False})
    except Exception as e:
        logger.error(f"Error checking VIN: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/add_vin', methods=['POST'])
@require_api_key
def add_vin():
    try:
        data = request.json
        if not data or 'vin_value' not in data:
            return jsonify({'error': 'No VIN provided'}), 400
            
        logger.info(f"Adding VIN: {data['vin_value']}")
        db = get_db()
        
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
        
        logger.info(f"Successfully added/updated VIN: {data['vin_value']}")
        return jsonify({
            'success': True,
            'modified_count': result.modified_count,
            'upserted_id': str(result.upserted_id) if result.upserted_id else None
        })
    except Exception as e:
        logger.error(f"Error adding VIN: {str(e)}")
        raise

@app.route('/')
def home():
    try:
        # Test database connection
        db = get_db()
        return jsonify({
            'status': 'healthy',
            'message': 'VIN Scanner API is running!',
            'database': 'connected'
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'message': 'Database connection failed',
            'error': str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True) 