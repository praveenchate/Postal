from flask_cors import CORS
from flask import Flask, request, jsonify, render_template, send_file
import cv2
import numpy as np
import base64
import re
import nltk
from nltk.tokenize import word_tokenize
from dotenv import load_dotenv
import os
import easyocr
import requests
import mysql.connector
from datetime import datetime
import json
import pandas as pd
from pincode_service import PincodeService

# Initialize Flask app
app = Flask(__name__)

# Configure CORS - update this to match your frontend URL
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5174"],  # Your Vite frontend port
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Load environment variables
load_dotenv()

required_env_vars = {
    'GOOGLE_MAPS_API_KEY': 'Google Maps API key',
    'DB_HOST': 'Database host',
    'DB_USER': 'Database user',
    'DB_PASSWORD': 'Database password',
    'DB_NAME': 'Database name'
}
missing_vars = [name for name, desc in required_env_vars.items() if not os.getenv(name)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MYSQL_HOST = os.getenv("DB_HOST")
MYSQL_USER = os.getenv("DB_USER")
MYSQL_PASSWORD = os.getenv("DB_PASSWORD")
MYSQL_DATABASE = os.getenv("DB_NAME")

# Initialize PincodeService
pincode_service = PincodeService()

# Initialize NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    reader = easyocr.Reader(['en'], gpu=True)
    print("EasyOCR initialized with GPU support")
except Exception as e:
    print(f"GPU not available, falling back to CPU: {str(e)}")
    reader = easyocr.Reader(['en'], gpu=False)

# Nodal centers data
nodal_centers = {
    "Pune Main Nodal Center": ["411001", "411002", "411003", "411004", "411005"],
    "Mumbai Central Nodal Center": ["400001", "400016", "400020", "400021", "400022"],
    "Nagpur Regional Nodal Center": ["440001", "440002", "440003", "440004", "440005"],
    "Solapur Distribution Hub": ["413001", "413002", "413003", "413004", "413005"],
    "Aurangabad Logistics Park": ["431001", "431002", "431003", "431004", "431005"],
    "Kolhapur Delivery Center": ["416001", "416002", "416003", "416004", "416005"],
    "Thane West Sorting Office": ["400601", "400602", "400603", "400604", "400605"],
    "Nashik Main Post Office": ["422001", "422002", "422003", "422004", "422005"],
    "Amravati Camp Hub": ["444601", "444602", "444603", "444604", "444605"],
    "Akola City Dispatch": ["444001", "444002", "444003", "444004", "444005"],
    "Latur City Post Office": ["413512", "413513", "413514", "413515", "413516"],
    "Jalgaon City Delivery": ["425001", "425002", "425003", "425004", "425005"],
    "Parbhani City Post": ["431401", "431402", "431403", "431404", "431405"],
    "New Delhi Central Hub": ["110001", "110002", "110003", "110004", "110006"],
    "Bangalore MG Road Center": ["560001", "560002", "560003", "560004", "560005"],
    "Kolkata Park Street Hub": ["700001", "700016", "700017", "700018", "700019"],
    "Jaipur JLN Marg Center": ["302001", "302002", "302003", "302004", "302005"],
    "Ahmedabad MG Road Hub": ["380001", "380002", "380003", "380009", "380010"],
    "Hyderabad Sarojini Devi Hub": ["500001", "500002", "500003", "500004", "500005"]
}

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=3306,  # Explicitly set port
            auth_plugin='mysql_native_password',  # Important for MySQL 8+
            use_pure=True  # Force pure Python connector
        )
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        raise


# Database initialization
def initialize_db():
    """Initialize database and create tables if they don't exist"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        cursor.execute(f"USE {MYSQL_DATABASE}")
        
        # Create addresses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                address_text TEXT,
                pincode VARCHAR(10),
                city VARCHAR(100),
                state VARCHAR(100),
                street VARCHAR(255),
                google_maps_pincode VARCHAR(10),
                google_maps_city VARCHAR(100),
                google_maps_state VARCHAR(100),
                google_maps_street VARCHAR(255),
                nodal_delivery_center VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create wrong_pincodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wrong_pincodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_pincode VARCHAR(10),
                corrected_pincode VARCHAR(10),
                address_text TEXT,
                confidence_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create voice_addresses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_addresses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                audio_file_path VARCHAR(255),
                transcribed_text TEXT,
                pincode VARCHAR(10),
                city VARCHAR(100),
                state VARCHAR(100),
                nodal_delivery_center VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create route_optimization table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS route_optimization (
                id INT AUTO_INCREMENT PRIMARY KEY,
                route_name VARCHAR(255),
                nodal_center VARCHAR(255),
                start_location VARCHAR(255),
                stops TEXT,  
                total_distance FLOAT,
                estimated_time VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Initialize pincodes table
        pincode_service.initialize_pincodes_table()
        
        conn.commit()
        print("Database initialized successfully")
        
    except Exception as err:
        print(f"Database initialization error: {err}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
# Address Processing Functions
def extract_address_from_image(image_data):
    """Extracts address text from base64 image data using EasyOCR."""
    try:
        if not image_data or not isinstance(image_data, str):
            raise ValueError("Invalid image data format")
            
        if not image_data.startswith('data:image'):
            raise ValueError("Invalid image format, expected base64 encoded image")
            
        try:
            header, encoded = image_data.split(',', 1)
            image_data = base64.b64decode(encoded)
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {str(e)}")
            
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")

        # Preprocess image
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
        img = cv2.resize(img, (min(800, img.shape[1]), min(600, img.shape[0])))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Perform OCR
        try:
            results = reader.readtext(gray, detail=0)
            address_text = ' '.join(results).strip()
            
            if not address_text:
                raise ValueError("No text detected in image")
                
            return address_text
        except Exception as e:
            raise ValueError(f"OCR processing failed: {str(e)}")

    except Exception as e:
        print(f"Error during EasyOCR: {str(e)}")
        raise

def parse_address_text(address_text):
    """Parses address text with flexible pattern matching."""
    try:
        if not address_text or not isinstance(address_text, str):
            raise ValueError("Invalid address text")

        # Split using commas or semicolons
        parts = re.split(r'[;,]+', address_text.strip())
        parts = [part.strip() for part in parts if part.strip()]

        street = city = state = pincode = None

        # Find pincode (6 digits)
        for i, part in enumerate(parts):
            pincode_match = re.search(r'\d{6}', part)
            if pincode_match:
                pincode = pincode_match.group(0)
                parts[i] = re.sub(r'\d{6}', '', parts[i]).strip()
                if not parts[i]:
                    parts.pop(i)
                break

        # Find State - common Indian states
        states = ["Maharashtra", "Delhi", "Karnataka", "West Bengal", "Rajasthan", 
                 "Gujarat", "Telangana", "Tamil Nadu", "Uttar Pradesh", "Kerala"]
        for i, part in enumerate(parts):
            for state_name in states:
                if state_name.lower() in part.lower():
                    state = state_name
                    parts[i] = part.replace(state_name, "").strip()
                    if not parts[i]:
                        parts.pop(i)
                    break
            if state:
                break

        # Remaining parts are street and city
        if len(parts) >= 2:
            street = parts[0]
            city = parts[-1]
        elif len(parts) == 1:
            if len(parts[0].split()) >= 3:
                street = parts[0]
            else:
                city = parts[0]

        return {
            "street": street,
            "city": city,
            "state": state,
            "pincode": pincode
        }

    except Exception as e:
        print(f"Error during address parsing: {str(e)}")
        raise

def geocode_address(address_data):
    """Geocodes the address using the Google Maps Geocoding API."""
    try:
        if not address_data or not isinstance(address_data, dict):
            raise ValueError("Invalid address data")

        # Build address string, handling None values
        address_parts = []
        if address_data.get('street'):
            address_parts.append(address_data['street'])
        if address_data.get('city'):
            address_parts.append(address_data['city'])
        if address_data.get('state'):
            address_parts.append(address_data['state'])
        if address_data.get('pincode'):
            address_parts.append(address_data['pincode'])
        
        if not address_parts:
            return None
            
        address = ', '.join(address_parts)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_MAPS_API_KEY}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'OK':
            result = data['results'][0]['address_components']
            return {
                'google_maps_pincode': next((c['long_name'] for c in result if 'postal_code' in c['types']), None),
                'google_maps_city': next((c['long_name'] for c in result if 'locality' in c['types']), None),
                'google_maps_state': next((c['long_name'] for c in result if 'administrative_area_level_1' in c['types']), None),
                'google_maps_street': next((c['long_name'] for c in result if 'route' in c['types']), None),
            }
        elif data['status'] == 'ZERO_RESULTS':
            print("Geocoding failed: Address not found")
            return None
        else:
            print(f"Geocoding failed: {data.get('error_message', data['status'])}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Geocoding request error: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Geocoding response parsing error: {str(e)}")
        return None
    except Exception as e:
        print(f"Geocoding general error: {str(e)}")
        return None

def get_nodal_center(pincode):
    """Retrieves the nodal delivery center based on the pincode."""
    if not pincode or not isinstance(pincode, str):
        return "Nodal Center Not Found"
        
    for center, pincode_list in nodal_centers.items():
        if pincode in pincode_list:
            return center
    return "Nodal Center Not Found"

def verify_pincode(pincode):
    """Verify if a pincode is valid (exists in our nodal centers)"""
    if not pincode or not isinstance(pincode, str) or not pincode.isdigit() or len(pincode) != 6:
        return False, None
        
    for center, pincode_list in nodal_centers.items():
        if pincode in pincode_list:
            return True, center
    return False, None

def suggest_correct_pincode(incorrect_pincode):
    """Suggest a correct pincode based on similarity to existing pincodes"""
    if not incorrect_pincode or len(incorrect_pincode) < 4:
        return None, 0
        
    # Flatten all pincodes from nodal centers
    all_pincodes = [pincode for pincode_list in nodal_centers.values() for pincode in pincode_list]
    
    best_match = None
    highest_score = 0
    
    for correct_pincode in all_pincodes:
        # Simple similarity score: count matching digits in same position
        score = sum(1 for a, b in zip(incorrect_pincode, correct_pincode) if a == b)
        score = score / max(len(incorrect_pincode), len(correct_pincode))  # Normalize
        
        if score > highest_score:
            highest_score = score
            best_match = correct_pincode
    
    # Only return a suggestion if the confidence is above a threshold
    if highest_score >= 0.5:
        return best_match, highest_score
    return None, 0

# Database Operations
def insert_address(address_data):
    """Inserts address data into the database."""
    try:
        if not address_data or not isinstance(address_data, dict):
            raise ValueError("Invalid address data")

        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()

        query = """
        INSERT INTO addresses (address_text, pincode, city, state, street,
                               google_maps_pincode, google_maps_city, google_maps_state, google_maps_street,
                               nodal_delivery_center)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            address_data.get('address_text'),
            address_data.get('pincode'),
            address_data.get('city'),
            address_data.get('state'),
            address_data.get('street'),
            address_data.get('google_maps_pincode'),
            address_data.get('google_maps_city'),
            address_data.get('google_maps_state'),
            address_data.get('google_maps_street'),
            address_data.get('nodal_delivery_center')
        )
        cursor.execute(query, values)
        conn.commit()
        return True

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def insert_wrong_pincode(original, corrected, address_text, confidence):
    """Record wrong pincodes and their corrections in the database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()

        query = """
        INSERT INTO wrong_pincodes (original_pincode, corrected_pincode, address_text, confidence_score)
        VALUES (%s, %s, %s, %s)
        """
        values = (original, corrected, address_text, confidence)
        cursor.execute(query, values)
        conn.commit()
        return True

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_wrong_pincodes():
    """Fetch wrong pincodes from the database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT * FROM wrong_pincodes 
        ORDER BY created_at DESC
        """
        cursor.execute(query)
        return cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def insert_voice_address(audio_path, transcribed_text, pincode, city, state, nodal_center):
    """Record voice recognized addresses in the database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()

        query = """
        INSERT INTO voice_addresses (audio_file_path, transcribed_text, pincode, city, state, nodal_delivery_center)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (audio_path, transcribed_text, pincode, city, state, nodal_center)
        cursor.execute(query, values)
        conn.commit()
        return True

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def save_route_optimization(route_data):
    """Save route optimization data to the database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()

        query = """
        INSERT INTO route_optimization (route_name, nodal_center, start_location, stops, 
                                       total_distance, estimated_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            route_data.get('route_name'),
            route_data.get('nodal_center'),
            route_data.get('start_location'),
            json.dumps(route_data.get('stops', [])),
            route_data.get('total_distance'),
            route_data.get('estimated_time')
        )
        cursor.execute(query, values)
        conn.commit()
        return True

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_dashboard_data():
    """Get aggregate data for the dashboard"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get total addresses processed
        cursor.execute("SELECT COUNT(*) as total_addresses FROM addresses")
        total_addresses = cursor.fetchone()['total_addresses']
        
        # Get total wrong pincodes
        cursor.execute("SELECT COUNT(*) as total_wrong_pincodes FROM wrong_pincodes")
        total_wrong_pincodes = cursor.fetchone()['total_wrong_pincodes']
        
        # Get total voice addresses
        cursor.execute("SELECT COUNT(*) as total_voice_addresses FROM voice_addresses")
        total_voice_addresses = cursor.fetchone()['total_voice_addresses']
        
        # Get addresses by nodal center
        cursor.execute("""
            SELECT nodal_delivery_center, COUNT(*) as count 
            FROM addresses 
            GROUP BY nodal_delivery_center
        """)
        nodal_centers_data = cursor.fetchall()
        
        # Get recent addresses
        cursor.execute("""
            SELECT * FROM addresses 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_addresses = cursor.fetchall()
        
        return {
            "total_addresses": total_addresses,
            "total_wrong_pincodes": total_wrong_pincodes,
            "total_voice_addresses": total_voice_addresses,
            "nodal_centers_data": nodal_centers_data,
            "recent_addresses": recent_addresses
        }

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return {}
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.errorhandler(Exception)
def handle_exception(e):
    """Global error handler for all routes"""
    print(f"Unhandled exception: {str(e)}")
    return jsonify({
        'error': 'An internal server error occurred',
        'message': str(e)
    }), 500

# Frontend Routes
@app.route('/')
def dashboard():
    """Render the main dashboard page"""
    return render_template('dashboard.html')

@app.route('/add_parcel_single')
def add_parcel_single():
    """Render the single address capture page"""
    return render_template('index.html')

@app.route('/batch_address_capture')
def batch_address_capture():
    """Render the batch address capture page"""
    return render_template('batch_address_capture.html')

# API Endpoints
@app.route('/api/capture_and_process', methods=['POST'])
def capture_and_process():
    """Process handwritten address image"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Extract text from image
        address_text = extract_address_from_image(data['image'])
        if not address_text:
            return jsonify({'error': 'OCR extraction failed'}), 400

        # Parse address text
        expected_address = parse_address_text(address_text)
        if not expected_address:
            return jsonify({'error': 'Address parsing failed'}), 400

        # Geocode address
        geocode_result = geocode_address(expected_address)
        if not geocode_result:
            return jsonify({'error': 'Invalid address (Google Maps API)'}), 400

        # Combine results
        expected_address.update(geocode_result)
        expected_address['address_text'] = address_text
        expected_address['nodal_delivery_center'] = get_nodal_center(expected_address['pincode'])

        # Insert into database
        if not insert_address(expected_address):
            return jsonify({'error': 'Database insertion failed'}), 500

        return jsonify({
            'message': 'Address processed and stored successfully',
            'extracted_address': {
                'address_text': expected_address.get('address_text'),
                'street': expected_address.get('street'),
                'city': expected_address.get('city'),
                'state': expected_address.get('state'),
                'pincode': expected_address.get('pincode')
            },
            'geocoding_results': {
                'google_maps_street': expected_address.get('google_maps_street'),
                'google_maps_city': expected_address.get('google_maps_city'),
                'google_maps_state': expected_address.get('google_maps_state'),
                'google_maps_pincode': expected_address.get('google_maps_pincode')
            },
            'nodal_delivery_center': expected_address['nodal_delivery_center']
        })

    except Exception as e:
        print(f"Error during capture and process: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/capture_and_process', methods=['POST'])
def legacy_capture_and_process():
    """Legacy endpoint for backward compatibility"""
    return capture_and_process()

@app.route('/api/validate_pincode', methods=['POST'])
def validate_pincode_api():
    """Validate and suggest corrections for pincodes"""
    try:
        data = request.get_json()
        if not data or 'pincode' not in data:
            return jsonify({'error': 'No pincode provided'}), 400

        pincode = data['pincode']
        address_text = data.get('address_text', '')
        
        # Validate pincode
        is_valid, nodal_center = verify_pincode(pincode)
        
        if is_valid:
            return jsonify({
                'is_valid': True,
                'pincode': pincode,
                'nodal_center': nodal_center,
                'message': f'Valid pincode for {nodal_center}'
            })
        
        # Suggest correction if invalid
        suggestion, confidence = suggest_correct_pincode(pincode)
        
        if suggestion:
            # Record the wrong pincode
            insert_wrong_pincode(pincode, suggestion, address_text, confidence)
            
            suggested_nodal_center = get_nodal_center(suggestion)
            return jsonify({
                'is_valid': False,
                'suggestion': suggestion,
                'confidence': confidence,
                'suggested_nodal_center': suggested_nodal_center,
                'message': f'Invalid pincode. Did you mean {suggestion} for {suggested_nodal_center}?'
            })
        
        return jsonify({
            'is_valid': False,
            'message': 'Invalid pincode. No suggestion available.'
        })

    except Exception as e:
        print(f"Error during pincode validation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Process voice recordings with address information"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        # Save the audio file
        upload_folder = os.path.join(app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = f"voice_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        filepath = os.path.join(upload_folder, filename)
        audio_file.save(filepath)
        
        # TODO: Implement actual speech recognition
        # For now, simulate with dummy data
        transcribed_text = "123 Main Street, Mumbai, Maharashtra 400016"
        
        # Parse the address
        parsed_address = parse_address_text(transcribed_text)
        
        if parsed_address and parsed_address['pincode']:
            nodal_center = get_nodal_center(parsed_address['pincode'])
            
            # Save to database
            insert_voice_address(
                filepath, 
                transcribed_text,
                parsed_address['pincode'],
                parsed_address['city'],
                parsed_address['state'],
                nodal_center
            )
            
            return jsonify({
                'success': True,
                'transcribed_text': transcribed_text,
                'parsed_address': parsed_address,
                'nodal_center': nodal_center
            })
        
        return jsonify({
            'success': False,
            'transcribed_text': transcribed_text,
            'error': 'Could not parse address or find pincode'
        })

    except Exception as e:
        print(f"Error processing voice input: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/wrong_pincodes', methods=['GET'])
def get_wrong_pincodes_api():
    """Get list of wrong pincodes"""
    try:
        wrong_pincodes = get_wrong_pincodes()
        return jsonify({'wrong_pincodes': wrong_pincodes})
    except Exception as e:
        print(f"Error fetching wrong pincodes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/optimize_route', methods=['POST'])
def optimize_route():
    """Optimize delivery routes for a nodal center"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        nodal_center = data.get('nodal_center')
        start_location = data.get('start_location')
        delivery_points = data.get('delivery_points', [])
        
        if not nodal_center or not start_location:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # TODO: Implement actual route optimization
        # Simulated result for now
        optimized_route = {
            'route_name': f"Route for {nodal_center}",
            'nodal_center': nodal_center,
            'start_location': start_location,
            'stops': delivery_points,
            'total_distance': 15.7,  # km
            'estimated_time': "2 hours 15 minutes"
        }
        
        # Save to database
        save_route_optimization(optimized_route)
        
        return jsonify({
            'success': True,
            'optimized_route': optimized_route
        })
        
    except Exception as e:
        print(f"Error optimizing route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/dashboard_data', methods=['GET'])
def dashboard_data():
    """Get dashboard statistics"""
    try:
        data = get_dashboard_data()
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching dashboard data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/address_parsing', methods=['POST'])
def parse_address():
    """Parse a text address"""
    try:
        data = request.get_json()
        if not data or 'address_text' not in data:
            return jsonify({'error': 'No address text provided'}), 400
            
        address_text = data['address_text']
        parsed_address = parse_address_text(address_text)
        
        if parsed_address:
            nodal_center = get_nodal_center(parsed_address['pincode']) if parsed_address['pincode'] else None
            return jsonify({
                'success': True,
                'parsed_address': parsed_address,
                'nodal_center': nodal_center
            })
        
        return jsonify({
            'success': False,
            'error': 'Could not parse address'
        })
            
    except Exception as e:
        print(f"Error parsing address: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/import_pincodes', methods=['POST'])
def import_pincodes():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'Only CSV files are allowed'}), 400
    
    success, message = pincode_service.import_from_csv(file)
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 500

@app.route('/api/pincodes', methods=['GET'])
def get_pincodes():
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        result = pincode_service.get_pincodes(page, per_page)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pincodes/search', methods=['GET'])
def search_pincodes():
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        results = pincode_service.search_pincodes(query, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


def initialize_services():
    """Initialize all required services"""
    try:
        initialize_db()
        print("All services initialized successfully")
        return True
    except Exception as e:
        print(f"Failed to initialize services: {str(e)}")
        return False

if __name__ == '__main__':
    if initialize_services():
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("Failed to start application due to initialization errors")