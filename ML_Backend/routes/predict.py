"""
routes/predict.py — نقطة تنبؤ الذكاء الاصطناعي
Predict blueprint: AI prediction endpoint used by Arduino/hardware.
"""
from flask import Blueprint, request, jsonify
import numpy as np
from datetime import datetime

from database import collection

predict_bp = Blueprint('predict', __name__)

# Model reference — set by app.py after loading
model = None


@predict_bp.route('/predict', methods=['POST'])
def predict():
    """
    AI prediction endpoint.
    Body: { "soil_resistance": float, "temperature": float, "humidity": float }
    """
    try:
        if model is None:
            return jsonify({'error': 'Model not loaded', 'status': 'failed'}), 500

        data = request.json or {}
        for field in ('soil_resistance', 'temperature', 'humidity'):
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'status': 'failed'}), 400

        features   = np.array([[data['soil_resistance'], data['temperature'], data['humidity']]])
        prediction = int(model.predict(features)[0])

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
