from flask import Flask, request, jsonify, render_template_string
import joblib
import numpy as np
import os
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- 1. إعداد الاتصال بقاعدة بيانات MongoDB ---
# سيستخدم الرابط من متغيرات بيئة Railway، أو المحلي إذا كنت تختبره بجهازك
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGO_URI)
    db = client['irrigation_db']
    collection = db['sensor_data']
    print("--- Connected to MongoDB successfully! ---")
except Exception as e:
    print(f"--- MongoDB Connection Error: {e} ---")

# --- 2. تحميل مودل الذكاء الاصطناعي ---
model_path = os.path.join(os.path.dirname(__file__), 'irrigation_model.pkl')
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("--- Model loaded successfully! ---")
else:
    print(f"--- Error: {model_path} not found! ---")

# --- 3. واجهة المستخدم (HTML/CSS/JS) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام الري الذكي | لوحة الاختبار</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 100%; max-width: 500px; border-top: 5px solid #27ae60; }
        h2 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 10px; border-right: 5px solid #3498db; }
        label { font-weight: bold; color: #34495e; display: block; margin-bottom: 8px; font-size: 14px; }
        input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; text-align: center; }
        button { width: 100%; padding: 15px; background-color: #27ae60; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px; }
        button:hover { background-color: #219150; transform: translateY(-2px); }
        #result { margin-top: 25px; padding: 20px; text-align: center; font-size: 22px; font-weight: bold; border-radius: 10px; display: none; }
        .yes { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .no { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .db-status { font-size: 12px; font-weight: normal; color: #666; margin-top: 10px; display: block; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🌱 نظام الري بالذكاء الاصطناعي</h2>
        <form id="predictForm">
            <div class="input-group">
                <label>🔌 مقاومة رطوبة التربة (Ohm):</label>
                <input type="number" step="any" id="soil_res" required placeholder="مثال: 600">
            </div>
            
            <div class="input-group">
                <label>🌡️ درجة حرارة الجو (C°):</label>
                <input type="number" step="any" id="temp" required placeholder="مثال: 30">
            </div>
            
            <div class="input-group">
                <label>💧 رطوبة الجو (%):</label>
                <input type="number" step="any" id="hum" required placeholder="مثال: 55">
            </div>
            
            <button type="submit">تحليل البيانات واتخاذ القرار</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('predictForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const resDiv = document.getElementById('result');
            resDiv.style.display = 'block';
            resDiv.innerHTML = 'جاري التحليل...';
            resDiv.className = '';

            const data = {
                soil_resistance: parseFloat(document.getElementById('soil_res').value),
                temperature: parseFloat(document.getElementById('temp').value),
                humidity: parseFloat(document.getElementById('hum').value)
            };

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if(result.status === 'success') {
                    if(result.pump_status === 1) {
                        resDiv.innerHTML = '💦 حالة المضخة: تشغيل (ON) <span class="db-status">✔️ تم الحفظ في MongoDB</span>';
                        resDiv.className = 'yes';
                    } else {
                        resDiv.innerHTML = '🚫 حالة المضخة: إيقاف (OFF) <span class="db-status">✔️ تم الحفظ في MongoDB</span>';
                        resDiv.className = 'no';
                    }
                } else {
                    resDiv.innerHTML = 'خطأ: ' + result.error;
                    resDiv.className = 'no';
                }
            } catch (err) {
                resDiv.innerHTML = 'فشل الاتصال بالسيرفر!';
                resDiv.className = 'no';
            }
        });
    </script>
</body>
</html>
"""

# --- 4. المسارات (Routes) ---

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_PAGE)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # التأكد من وصول جميع البيانات المطلوبة
        required_fields = ['soil_resistance', 'temperature', 'humidity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}', 'status': 'failed'})

        # تحضير البيانات للمودل (يجب أن يكون نفس الترتيب المستخدم في التدريب)
        features = np.array([[
            data['soil_resistance'],
            data['temperature'],
            data['humidity']
        ]])
        
        # إجراء التنبؤ
        prediction = int(model.predict(features)[0])
        
        # حفظ السجل في قاعدة البيانات
        record = {
            "soil_resistance": data['soil_resistance'],
            "temperature": data['temperature'],
            "humidity": data['humidity'],
            "pump_status": prediction,
            "timestamp": datetime.now()
        }
        collection.insert_one(record)
        
        return jsonify({
            'pump_status': prediction,
            'status': 'success',
            'message': 'Data processed and saved'
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

if __name__ == '__main__':
    # تشغيل السيرفر على بورت Railway أو البورت الافتراضي 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)