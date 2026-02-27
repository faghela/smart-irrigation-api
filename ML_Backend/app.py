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
# واجهة المستخدم التفاعلية المحسنة
# ==========================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Irrigation Dashboard</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e9ecef; margin: 0; padding: 40px; display: flex; justify-content: center; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 10px 20px rgba(0,0,0,0.1); width: 100%; max-width: 450px; }
        h2 { text-align: center; color: #2c3e50; margin-bottom: 25px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .input-group { margin-bottom: 15px; background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }
        label { font-weight: bold; color: #34495e; display: block; font-size: 14px; margin-bottom: 5px;}
        input { width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; margin-top: 20px; background-color: #27ae60; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background-color: #219150; }
        #result { margin-top: 25px; padding: 20px; text-align: center; font-size: 20px; font-weight: bold; border-radius: 8px; display: none; box-shadow: inset 0 0 10px rgba(0,0,0,0.05);}
        .yes { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .no { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .db-msg { font-size: 13px; font-weight: normal; margin-top: 8px; display: block; color: #6c757d;}
        .note { text-align: center; font-size: 12px; color: #7f8c8d; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🌱 Smart Irrigation API Test</h2>
        <form id="predictForm">
            <div class="input-group">
                <label>🔌 Soil Moisture Resistance (Ohm):</label>
                <input type="number" step="any" id="soil_res" required placeholder="e.g., 300">
            </div>
            
            <div class="input-group">
                <label>🌡️ Ambient Temperature (°C):</label>
                <input type="number" step="any" id="temp" required placeholder="e.g., 25.5">
            </div>
            
            <div class="input-group">
                <label>💧 Atmospheric Humidity (%):</label>
                <input type="number" step="any" id="hum" required placeholder="e.g., 60">
            </div>
            
            <button type="submit">Run AI Prediction & Save</button>
        </form>
        <div id="result"></div>
        <div class="note">* This is an API testing interface. Full dashboard & manual control will be in Node-RED.</div>
    </div>

    <script>
        document.getElementById('predictForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = document.querySelector('button');
            btn.innerHTML = '⚙️ Processing...';
            btn.disabled = true;

            const data = {
                soil_resistance: parseFloat(document.getElementById('soil_res').value),
                temperature: parseFloat(document.getElementById('temp').value),
                humidity: parseFloat(document.getElementById('hum').value)
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
                    if(result.pump_status === 1) {
                        resDiv.innerHTML = '💦 Pump Status: ON (1)<span class="db-msg">✔️ Logged to MongoDB</span>';
                        resDiv.className = 'yes';
                    } else {
                        resDiv.innerHTML = '🚫 Pump Status: OFF (0)<span class="db-msg">✔️ Logged to MongoDB</span>';
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
            btn.innerHTML = 'Run AI Prediction & Save';
            btn.disabled = false;
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_PAGE)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        # الترتيب مهم جداً: يجب أن يطابق ترتيب الأعمدة في ملف التدريب
        features = np.array([[
            data['soil_resistance'],
            data['temperature'],
            data['humidity']
        ]])
        
        prediction = int(model.predict(features)[0])
        
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
            'message': 'Data saved successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)