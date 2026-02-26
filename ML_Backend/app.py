from flask import Flask, request, jsonify
import joblib
import numpy as np
import os
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# إعداد الاتصال بقاعدة بيانات MongoDB
# سيأخذ الرابط من متغيرات البيئة في Railway
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGO_URI)
    db = client['irrigation_db']          # اسم قاعدة البيانات
    collection = db['sensor_data']        # اسم "المجموعة" (الجدول)
    print("--- Connected to MongoDB successfully! ---")
except Exception as e:
    print(f"--- MongoDB Connection Error: {e} ---")

# تحميل المودل
model_path = os.path.join(os.path.dirname(__file__), 'irrigation_model.pkl')
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("--- Model loaded successfully! ---")
else:
    print(f"--- Error: {model_path} not found! ---")

@app.route('/', methods=['GET'])
def home():
    return """
    <h1>Smart Irrigation Server is Online!</h1>
    <p>The AI model and MongoDB connection are ready.</p>
    """

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # استقبال البيانات
        data = request.json
        
        # التنبؤ
        features = np.array([[
            data['temperature'],
            data['humidity'],
            data['soil_moisture'],
            data['light'],
            data['rainfall']
        ]])
        prediction = int(model.predict(features)[0])
        
        # تجهيز السجل لحفظه في MongoDB
        record = {
            "temperature": data['temperature'],
            "humidity": data['humidity'],
            "soil_moisture": data['soil_moisture'],
            "light": data['light'],
            "rainfall": data['rainfall'],
            "irrigation_required": prediction,
            "timestamp": datetime.now() # حفظ وقت وتاريخ القراءة
        }
        
        # إدخال البيانات في قاعدة البيانات
        collection.insert_one(record)
        
        # إرسال النتيجة لـ Node-RED
        return jsonify({
            'irrigation_required': prediction,
            'status': 'success',
            'message': 'Data saved to MongoDB successfully!'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)