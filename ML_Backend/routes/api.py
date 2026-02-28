"""
routes/api.py — واجهات برمجة التطبيقات
API blueprint: latest, history, weather, pump control.
"""
from flask import Blueprint, request, jsonify, session
from pymongo import DESCENDING
from datetime import datetime
import requests

from auth import login_required
from database import collection, control_col
from config import WEATHER_API_KEY, CITY

api_bp = Blueprint('api', __name__, url_prefix='/api')


# ── GET /api/latest ───────────────────────────────
@api_bp.route('/latest', methods=['GET'])
@login_required
def latest():
    """Return the most recent sensor reading from MongoDB."""
    try:
        if collection is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 503

        doc = collection.find_one(sort=[('timestamp', DESCENDING)])
        if not doc:
            return jsonify({'status': 'no_data', 'message': 'No records found'})

        return jsonify({
            'status':          'success',
            'soil_resistance': doc.get('soil_resistance', 0),
            'temperature':     doc.get('temperature', 0),
            'humidity':        doc.get('humidity', 0),
            'pump_status':     doc.get('pump_status', 0),
            'timestamp':       doc['timestamp'].isoformat() if 'timestamp' in doc else None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── GET /api/history ──────────────────────────────
@api_bp.route('/history', methods=['GET'])
@login_required
def history():
    """Return the last 50 sensor records for the chart."""
    try:
        if collection is None:
            return jsonify({'status': 'error', 'message': 'Database not connected'}), 503

        cursor = collection.find(
            {},
            {'_id': 0, 'soil_resistance': 1, 'temperature': 1,
             'humidity': 1, 'pump_status': 1, 'timestamp': 1}
        ).sort('timestamp', DESCENDING).limit(50)

        records = list(cursor)
        records.reverse()

        for r in records:
            if 'timestamp' in r and isinstance(r['timestamp'], datetime):
                r['timestamp'] = r['timestamp'].isoformat()

        return jsonify({'status': 'success', 'data': records})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── GET /api/weather ──────────────────────────────
@api_bp.route('/weather', methods=['GET'])
@login_required
def weather():
    """
    Fetch real-time weather.
    Tries OpenWeatherMap first → falls back to Open-Meteo.
    """
    def _icon_from_owm(code):
        if code.startswith('01'): return '☀️'
        if code.startswith('02'): return '⛅'
        if code.startswith('03') or code.startswith('04'): return '☁️'
        if code.startswith('09') or code.startswith('10'): return '🌧️'
        if code.startswith('11'): return '⛈️'
        if code.startswith('13'): return '❄️'
        if code.startswith('50'): return '🌫️'
        return '🌤️'

    # 1) Try OpenWeatherMap
    try:
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ar"
        )
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data    = r.json()
            w       = data.get('weather', [{}])
            return jsonify({
                'status': 'success', 'source': 'OpenWeatherMap',
                'temperature':    data['main']['temp'],
                'humidity':       data['main']['humidity'],
                'description_ar': w[0].get('description', ''),
                'description_en': w[0].get('main', ''),
                'icon':           _icon_from_owm(w[0].get('icon', ''))
            })
        print(f"⚠️  OWM {r.status_code}, switching to Open-Meteo…")
    except Exception as e:
        print(f"⚠️  OWM error ({e}), switching to Open-Meteo…")

    # 2) Fallback → Open-Meteo (Tripoli, Libya)
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=32.9028&longitude=13.1805"
            "&current=temperature_2m,relative_humidity_2m,weather_code&timezone=auto"
        )
        r   = requests.get(url, timeout=5)
        r.raise_for_status()
        cur = r.json().get('current', {})
        code = cur.get('weather_code', 0)

        desc_ar, desc_en, icon = 'صافٍ', 'Clear', '☀️'
        if code in [1, 2, 3]:   desc_ar, desc_en, icon = 'غائم جزئياً', 'Partly Cloudy', '⛅'
        elif code in [45, 48]:  desc_ar, desc_en, icon = 'ضباب',        'Fog',           '🌫️'
        elif 51 <= code <= 67:  desc_ar, desc_en, icon = 'ممطر',        'Rain',          '🌧️'
        elif 71 <= code <= 77:  desc_ar, desc_en, icon = 'ثلوج',        'Snow',          '❄️'
        elif 80 <= code <= 82:  desc_ar, desc_en, icon = 'زخات مطر',    'Showers',       '🌦️'
        elif code >= 95:        desc_ar, desc_en, icon = 'عواصف رعدية', 'Thunderstorm',  '⛈️'

        return jsonify({
            'status': 'success', 'source': 'Open-Meteo (fallback)',
            'temperature':    cur.get('temperature_2m', 0),
            'humidity':       cur.get('relative_humidity_2m', 0),
            'description_ar': desc_ar, 'description_en': desc_en, 'icon': icon
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── POST /api/pump/control ────────────────────────
@api_bp.route('/pump/control', methods=['POST'])
@login_required
def pump_control():
    """Manual pump override. Body: { "action": "start" | "stop" }"""
    try:
        data   = request.json or {}
        action = data.get('action', '').lower()

        if action not in ('start', 'stop'):
            return jsonify({'status': 'error', 'message': 'Use start or stop.'}), 400

        pump_on = 1 if action == 'start' else 0
        command = {
            'action':      action,
            'pump_status': pump_on,
            'issued_by':   session.get('user_id', 'unknown'),
            'timestamp':   datetime.now()
        }
        if control_col is not None:
            control_col.insert_one(command)

        return jsonify({
            'status': 'ok', 'action': action, 'pump_status': pump_on,
            'message': f'Pump {"started" if pump_on else "stopped"} manually.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
