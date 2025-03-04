from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps
import logging
import time
from pymongo.errors import AutoReconnect
import certifi

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
API_KEY = os.getenv('API_KEY')

# Global MongoDB client with connection pooling
_mongo_client = None

def get_mongo_client():
    global _mongo_client
    if _mongo_client is None:
        logger.info("Creating new MongoDB client connection")
        try:
            _mongo_client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=45000,
                retryWrites=True,
                w='majority',
                tls=True,
                tlsCertificateKeyFile=None,  # Remove if not using client cert
                tlsCAFile=certifi.where(),
                tlsAllowInvalidCertificates=False
            )
            # Test connection immediately
            _mongo_client.admin.command('ping')
            # Log server information
            topology = _mongo_client.topology_description
            logger.info(f"MongoDB topology type: {topology.topology_type_name}")
            for server in topology.server_descriptions():
                logger.info(f"MongoDB server: {server.address}")
        except Exception as e:
            logger.error(f"Failed to create MongoDB client: {str(e)}")
            _mongo_client = None
            raise
    return _mongo_client

def retry_with_backoff(func, max_retries=3):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except (errors.ServerSelectionTimeoutError, 
                errors.ConnectionFailure,
                errors.NetworkTimeout,
                AutoReconnect) as e:
            if attempt == max_retries - 1:
                logger.error(f"Final retry attempt failed: {str(e)}")
                raise
            wait_time = (2 ** attempt) * 0.1  # 0.1s, 0.2s, 0.4s
            logger.warning(f"Retry attempt {attempt + 1}/{max_retries}. Waiting {wait_time}s")
            time.sleep(wait_time)

def get_db():
    try:
        client = get_mongo_client()
        # Test connection with retry
        def test_connection():
            client.admin.command('ping')
            return client.vin_database
        
        db = retry_with_backoff(test_connection)
        logger.info("Successfully connected to MongoDB")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {type(e).__name__}: {str(e)}")
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
        # Log the client IP address
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        logger.info(f"Request from IP: {client_ip}")
        
        vin = request.args.get('vin')
        if not vin:
            return jsonify({'error': 'No VIN provided'}), 400
            
        logger.info(f"Checking VIN: {vin}")
        
        def query_vin():
            db = get_db()
            return db.vin_records.find_one(
                {'vin_value': vin},
                max_time_ms=5000
            )
        
        # Use retry logic for the query
        result = retry_with_backoff(query_vin)
        
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
            'error': 'Database connection error',
            'message': 'Unable to connect to database',
            'details': str(e)
        }), 503

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