"""
config.py — إعدادات النظام المركزية
All application settings in one place.
"""
import os

# ── Flask App ─────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ── Auth Credentials ──────────────────────────────
DASHBOARD_USER_ID = os.environ.get('USER_ID', 'mohamed_f')
DASHBOARD_TOKEN   = os.environ.get('USER_TOKEN', '123456')

# ── MongoDB ───────────────────────────────────────
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

# ── OpenWeatherMap ────────────────────────────────
WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', '6990e1c557eb3c3dd525cbb95de96965')
CITY = os.environ.get('CITY', 'Tripoli')

# ── Server ────────────────────────────────────────
PORT = int(os.environ.get('PORT', 8080))
