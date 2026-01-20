import os
import base64
import uuid
import psycopg2
import requests
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# --- 1. CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- DATABASE SETTINGS ---
DB_HOST = "localhost"
DB_NAME = "plantdb"
DB_USER = "postgres"
DB_PASS = "root"  # <--- I kept your password as 'root'

# --- API SETTINGS (Pl@ntNet) ---
# I fixed the syntax error on this line for you:
API_KEY = "2b10grzENr2nQ4q7k2wVEyc38u"
API_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- 2. DATABASE HELPER ---
def get_db_connection():
    """Connects to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn


# --- 3. WEBSITE ROUTES ---

@app.route('/')
def index():
    """Shows the main scanner page."""
    return render_template('index.html')


@app.route('/history')
def history():
    """Shows the list of past scans from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch all logs, newest first
    cur.execute("SELECT * FROM plant_logs ORDER BY captured_at DESC")
    plants = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('history.html', plants=plants)


@app.route('/identify', methods=['POST'])
def identify():
    """Handles image upload, API identification, and database saving."""
    filename = None
    filepath = None

    # --- A. HANDLE IMAGE (File or Webcam) ---
    if 'file' in request.files:
        # Case 1: User uploaded a file
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

    elif 'webcam_image' in request.form:
        # Case 2: User used the webcam
        data_url = request.form['webcam_image']
        if ',' in data_url:
            # Remove the "data:image/jpeg;base64," header
            _, encoded = data_url.split(",", 1)
            data = base64.b64decode(encoded)
            filename = f"webcam_{uuid.uuid4()}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, "wb") as f:
                f.write(data)

    if not filepath:
        return jsonify({"error": "No image received"}), 400


    # --- B. SEND TO PL@NTNET API ---
    plant_name = "Unknown"
    probability = 0.0

    try:
        # Prepare the file for the API
        with open(filepath, 'rb') as img_file:
            files = {'images': open(filepath, 'rb')}
            data = {'organs': ['auto']}  # Let the AI guess if it's a leaf or flower
            
            # Send Request
            response = requests.post(API_URL, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                # Parse the best match
                best_match = result['results'][0]
                plant_name = best_match['species']['scientificNameWithoutAuthor']
                probability = best_match['score'] # 0 to 1
            else:
                print("API Error:", response.text)
                plant_name = "API Error"
                
    except Exception as e:
        print("Request Failed:", e)


    # --- C. SAVE TO DATABASE ---
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        insert_query = """
        INSERT INTO plant_logs (image_filename, plant_name, probability)
        VALUES (%s, %s, %s)
        """
        cur.execute(insert_query, (filename, plant_name, probability))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Database Save Error:", e)


    # --- D. RETURN RESULT TO FRONTEND ---
    return jsonify({
        "status": "success",
        "image_url": f"/{filepath}",
        "plant_name": plant_name,
        "probability": round(probability * 100, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)