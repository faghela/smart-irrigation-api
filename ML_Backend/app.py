from flask import Flask, request, jsonify, render_template_string
import joblib
import numpy as np
import os
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# إعداد الاتصال بقاعدة بيانات MongoDB
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
try:
    client = MongoClient(MONGO_URI)
    db = client['irrigation_db']
    collection = db['sensor_data']
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

# ==========================================
# واجهة المستخدم التفاعلية (HTML & CSS & JS)
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Irrigation Tester</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f8ff; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h2 { text-align: center; color: #0056b3; margin-bottom: 20px; }
        label { font-weight: bold; color: #333; margin-top: 15px; display: block; font-size: 14px; }
        input { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; margin-top: 25px; background-color: #28a745; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background-color: #218838; }
        #result { margin-top: 20px; padding: 15px; text-align: center; font-size: 18px; font-weight: bold; border-radius: 6px; display: none; }
        .yes { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .no { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .db-msg { font-size: 12px; font-weight: normal; margin-top: 5px; display: block; }
    </style>
</head>
<body>
    <div class="card">
        <h2>💧 Smart Irrigation Tester</h2>
        <form id="predictForm">
            <label>🌡️ Temperature (°C):</label>
            <input type="number" step="any" id="temp" required value="28.5">
            
            <label>💧 Humidity (%):</label>
            <input type="number" step="any" id="hum" required value="45.0">
            
            <label>🌱 Soil Moisture (%):</label>
            <input type="number" step="any" id="soil" required value="30.0">
            
            <label>☀️ Light (Lux):</label>
            <input type="number" step="any" id="light" required value="800">
            
            <label>🌧️ Rainfall (mm):</label>
            <input type="number" step="any" id="rain" required value="0">
            
            <button type="submit">Test Prediction & Save to DB</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('predictForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = document.querySelector('button');
            btn.innerHTML = 'Processing...';
            btn.disabled = true;

            const data = {
                temperature: parseFloat(document.getElementById('temp').value),
                humidity: parseFloat(document.getElementById('hum').value),
                soil_moisture: parseFloat(document.getElementById('soil').value),
                light: parseFloat(document.getElementById('light').value),
                rainfall: parseFloat(document.getElementById('rain').value)
            };

            const resDiv = document.getElementById('result');
            resDiv.style.display = 'block';
            resDiv.className = '';
            resDiv.innerHTML = 'Connecting to AI...';

            try {
                const response = await fetch('/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if(result.status === 'success') {
                    if(result.irrigation_required === 1) {
                        resDiv.innerHTML = '💦 Irrigation: ON (1)<span class="db-msg">✔️ Saved to MongoDB</span>';
                        resDiv.className = 'yes';
                    } else {
                        resDiv.innerHTML = '🚫 Irrigation: OFF (0)<span class="db-msg">✔️ Saved to MongoDB</span>';
                        resDiv.className = 'no';
                    }
                } else {
                    resDiv.innerHTML = 'Error: ' + result.error;
                    resDiv.className = 'no';
                }
            } catch (err) {
                resDiv.innerHTML = 'Network Error!';
                resDiv.className = 'no';
            }
            btn.innerHTML = 'Test Prediction & Save to DB';
            btn.disabled = false;
        });
    </script>
</body>
</html>
"""

# مسار الصفحة الرئيسية (يعرض الواجهة التفاعلية)
@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_PAGE)

# مسار التنبؤ (يستقبل البيانات من الواجهة أو من Node-RED)
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        features = np.array([[
            data['temperature'],
            data['humidity'],
            data['soil_moisture'],
            data['light'],
            data['rainfall']
        ]])
        
        prediction = int(model.predict(features)[0])
        
        # حفظ البيانات في MongoDB
        record = {
            "temperature": data['temperature'],
            "humidity": data['humidity'],
            "soil_moisture": data['soil_moisture'],
            "light": data['light'],
            "rainfall": data['rainfall'],
            "irrigation_required": prediction,
            "timestamp": datetime.now()
        }
        collection.insert_one(record)
        
        return jsonify({
            'irrigation_required': prediction,
            'status': 'success',
            'message': 'Data saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)