"""
=============================================================
  نظام الري الذكي | Smart Irrigation System
  Backend API + Dashboard
  ---------------------------------------------------------
  Author  : AI-Powered Full-Stack Upgrade
  Version : 2.0.0
=============================================================
"""

from flask import (
    Flask, request, jsonify,
    render_template, redirect, url_for,
    session, flash
)
import joblib
import numpy as np
import os
from pymongo import MongoClient, DESCENDING
from datetime import datetime
from functools import wraps
import requests

# ─────────────────────────────────────────────
# App Configuration
# ─────────────────────────────────────────────
app = Flask(__name__)

# Secret key for session signing — ALWAYS set this via env var in production!
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Dashboard credentials (read from env vars; safe defaults for local dev)
DASHBOARD_USER_ID = os.environ.get('USER_ID', 'mohamed_f')
DASHBOARD_TOKEN   = os.environ.get('USER_TOKEN',   '123456')

# OpenWeatherMap API settings
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '6990e1c557eb3c3dd525cbb95de96965')
CITY = os.environ.get('CITY', 'Tripoli')

# ─────────────────────────────────────────────
# 1. MongoDB Connection
# ─────────────────────────────────────────────
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client     = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db         = client['irrigation_db']
    collection = db['sensor_data']          # main sensor readings
    control_col = db['pump_control']        # manual override commands
    print("✅ Connected to MongoDB successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    collection  = None
    control_col = None

# ─────────────────────────────────────────────
# 2. Load AI Model
# ─────────────────────────────────────────────
model_path = os.path.join(os.path.dirname(__file__), 'irrigation_model.pkl')
model = None
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("✅ AI Model loaded successfully!")
else:
    print(f"⚠️  Model not found at: {model_path}")

# ─────────────────────────────────────────────
# 3. Auth Decorator
# ─────────────────────────────────────────────
def login_required(f):
    """Redirect to /login if the user is not authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('يرجى تسجيل الدخول أولاً | Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ─────────────────────────────────────────────
# 4. Auth Routes
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Root → redirect to dashboard (or login if not authenticated)."""
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Render login page and process credentials."""
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        token   = request.form.get('access_token', '').strip()

        if user_id == DASHBOARD_USER_ID and token == DASHBOARD_TOKEN:
            session['logged_in'] = True
            session['user_id']   = user_id
            return redirect(url_for('dashboard'))
        else:
            flash('بيانات الدخول غير صحيحة | Invalid credentials.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear the session and redirect to login."""
    session.clear()
    flash('تم تسجيل الخروج بنجاح | Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# 5. Dashboard Route
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    """Serve the main dashboard page."""
    return render_template('dashboard.html', user_id=session.get('user_id'))

# ─────────────────────────────────────────────
# 6. API Routes
# ─────────────────────────────────────────────

@app.route('/api/latest', methods=['GET'])
@login_required
def api_latest():
    """Return the most recent sensor reading from MongoDB."""
    try:
        if collection is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 503

        doc = collection.find_one(sort=[('timestamp', DESCENDING)])
        if not doc:
            return jsonify({'status': 'no_data', 'message': 'No records found'})

        return jsonify({
            'status': 'success',
            'soil_resistance': doc.get('soil_resistance', 0),
            'temperature':     doc.get('temperature', 0),
            'humidity':        doc.get('humidity', 0),
            'pump_status':     doc.get('pump_status', 0),
            'timestamp':       doc['timestamp'].isoformat() if 'timestamp' in doc else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/weather', methods=['GET'])
@login_required
def api_weather():
    """
    Fetch real-time weather.
    Tries OpenWeatherMap first.
    Falls back to the free Open-Meteo API if OWM fails
    (e.g. key not yet activated, quota exceeded, network error).
    """
    def icon_from_owm_code(icon_code):
        if icon_code.startswith('01'): return '☀️'
        if icon_code.startswith('02'): return '⛅'
        if icon_code.startswith('03') or icon_code.startswith('04'): return '☁️'
        if icon_code.startswith('09') or icon_code.startswith('10'): return '🌧️'
        if icon_code.startswith('11'): return '⛈️'
        if icon_code.startswith('13'): return '❄️'
        if icon_code.startswith('50'): return '🌫️'
        return '🌤️'

    # ── 1. Try OpenWeatherMap ──────────────────────────────────
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ar"
        )
        r = requests.get(url, timeout=5)

        # OWM returns 401 for invalid/inactive key, 404 for unknown city
        if r.status_code == 200:
            data      = r.json()
            temp      = data.get('main', {}).get('temp', 0)
            humidity  = data.get('main', {}).get('humidity', 0)
            w_list    = data.get('weather', [{}])
            desc_ar   = w_list[0].get('description', 'غير متوفر')
            desc_en   = w_list[0].get('main', 'Unknown')
            icon      = icon_from_owm_code(w_list[0].get('icon', ''))
            return jsonify({
                'status': 'success', 'source': 'OpenWeatherMap',
                'temperature': temp, 'humidity': humidity,
                'description_ar': desc_ar, 'description_en': desc_en, 'icon': icon
            })
        else:
            owm_error = r.json().get('message', f'HTTP {r.status_code}')
            print(f"⚠️  OWM failed ({owm_error}), switching to Open-Meteo fallback…")
    except Exception as owm_exc:
        print(f"⚠️  OWM exception ({owm_exc}), switching to Open-Meteo fallback…")

    # ── 2. Fallback → Open-Meteo (always free, no key needed) ──
    # Coordinates for Tripoli, Libya (32.90°N, 13.18°E)
    try:
        lat, lon = '32.9028', '13.1805'
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code&timezone=auto"
        )
        r    = requests.get(url, timeout=5)
        r.raise_for_status()
        cur  = r.json().get('current', {})
        code = cur.get('weather_code', 0)

        desc_ar, desc_en, icon = 'صافٍ', 'Clear', '☀️'
        if code in [1, 2, 3]:              desc_ar, desc_en, icon = 'غائم جزئياً',      'Partly Cloudy', '⛅'
        elif code in [45, 48]:             desc_ar, desc_en, icon = 'ضباب',              'Fog',           '🌫️'
        elif 51 <= code <= 67:             desc_ar, desc_en, icon = 'ممطر',              'Rain',          '🌧️'
        elif 71 <= code <= 77:             desc_ar, desc_en, icon = 'ثلوج',              'Snow',          '❄️'
        elif 80 <= code <= 82:             desc_ar, desc_en, icon = 'زخات مطر',          'Showers',       '🌦️'
        elif code >= 95:                   desc_ar, desc_en, icon = 'عواصف رعدية',       'Thunderstorm',  '⛈️'

        return jsonify({
            'status': 'success', 'source': 'Open-Meteo (fallback)',
            'temperature': cur.get('temperature_2m', 0),
            'humidity':    cur.get('relative_humidity_2m', 0),
            'description_ar': desc_ar, 'description_en': desc_en, 'icon': icon
        })
    except Exception as fallback_exc:
        return jsonify({'status': 'error', 'message': str(fallback_exc)}), 500


@app.route('/api/history', methods=['GET'])
@login_required
def api_history():
    """Return the last 50 sensor records for the dashboard chart."""
    try:
        if collection is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 503

        # Fetch last 50, reverse so chart is chronological left→right
        cursor = collection.find(
            {},
            {'_id': 0, 'soil_resistance': 1, 'temperature': 1,
             'humidity': 1, 'pump_status': 1, 'timestamp': 1}
        ).sort('timestamp', DESCENDING).limit(50)

        records = list(cursor)
        records.reverse()  # oldest → newest

        # Serialize datetime objects to ISO strings
        for r in records:
            if 'timestamp' in r and isinstance(r['timestamp'], datetime):
                r['timestamp'] = r['timestamp'].isoformat()

        return jsonify({'status': 'success', 'data': records})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/pump/control', methods=['POST'])
@login_required
def api_pump_control():
    """
    Manual pump override.
    Body: { "action": "start" | "stop" }
    Saves the command to the pump_control collection.
    """
    try:
        data   = request.json or {}
        action = data.get('action', '').lower()

        if action not in ('start', 'stop'):
            return jsonify({'status': 'error', 'message': 'Invalid action. Use start or stop.'}), 400

        pump_on = 1 if action == 'start' else 0

        command = {
            'action':    action,
            'pump_status': pump_on,
            'issued_by': session.get('user_id', 'unknown'),
            'timestamp': datetime.now()
        }
        if control_col is not None:
            control_col.insert_one(command)

        return jsonify({
            'status':      'ok',
            'action':      action,
            'pump_status': pump_on,
            'message':     f'Pump {"started" if pump_on else "stopped"} manually.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ─────────────────────────────────────────────
# 7. Original Predict Route (kept for hardware)
# ─────────────────────────────────────────────

@app.route('/predict', methods=['POST'])
def predict():
    """
    AI prediction endpoint — used by Arduino/hardware.
    Body: { "soil_resistance": float, "temperature": float, "humidity": float }
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded', 'status': 'failed'}), 500

        data = request.json or {}
        required_fields = ['soil_resistance', 'temperature', 'humidity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'status': 'failed'}), 400

        features   = np.array([[data['soil_resistance'], data['temperature'], data['humidity']]])
        prediction = int(model.predict(features)[0])

        # Persist to MongoDB
        record = {
            'soil_resistance': data['soil_resistance'],
            'temperature':     data['temperature'],
            'humidity':        data['humidity'],
            'pump_status':     prediction,
            'source':          'ai_prediction',
            'timestamp':       datetime.now()
        }
        if collection is not None:
            collection.insert_one(record)

        return jsonify({
            'pump_status': prediction,
            'status':      'success',
            'message':     'Data processed and saved'
        })

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500

# ─────────────────────────────────────────────
# 8. Run
# ─────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)