"""
=============================================================
  نظام الري الذكي | Smart Irrigation System
  Main Application Entry Point
=============================================================
"""
import os
import joblib
from flask import Flask

from config import SECRET_KEY, PORT
from auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.predict import predict_bp
import routes.predict as predict_module

# ── Create Flask App ──────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ── Register Blueprints ──────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(api_bp)
app.register_blueprint(predict_bp)

# ── Load AI Model ────────────────────────────────
model_path = os.path.join(os.path.dirname(__file__), 'irrigation_model.pkl')
if os.path.exists(model_path):
    predict_module.model = joblib.load(model_path)
    print("✅ AI Model loaded successfully!")
else:
    print(f"⚠️  Model not found at: {model_path}")

# ── Run ──────────────────────────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)