from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
API_KEY = os.getenv('API_KEY')

def get_db():
    client = MongoClient(MONGO_URI)
    return client.vin_database

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
        
    db = get_db()
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
        
    db = get_db()
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