from flask import Flask, request, jsonify
import joblib
import numpy as np
import os

app = Flask(__name__)

# تحديد المسار الصحيح للمودل
model_path = os.path.join(os.path.dirname(__file__), 'irrigation_model.pkl')

# تحميل المودل
if os.path.exists(model_path):
    model = joblib.load(model_path)
    print("--- Model loaded successfully! ---")
else:
    print(f"--- Error: {model_path} not found! ---")

# الصفحة الرئيسية للتأكد من عمل السيرفر
@app.route('/', methods=['GET'])
def home():
    return """
    <h1>Smart Irrigation Server is Online!</h1>
    <p>The AI model is ready. Send your data to <b>/predict</b> using a POST request.</p>
    """

# مسار التنبؤ (يستقبل البيانات ويرجع النتيجة)
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # استقبال البيانات من Node-RED أو أي مصدر آخر
        data = request.json
        
        # التأكد من ترتيب المدخلات (يجب أن يكون بنفس ترتيب التدريب)
        features = np.array([[
            data['temperature'],
            data['humidity'],
            data['soil_moisture'],
            data['light'],
            data['rainfall']
        ]])
        
        # التنبؤ
        prediction = model.predict(features)[0]
        
        # إرسال النتيجة
        return jsonify({
            'irrigation_required': int(prediction),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'})

# تشغيل السيرفر
if __name__ == '__main__':
    # أخذ البورت من بيئة Railway، وإذا لم يجده (مثل التشغيل المحلي) يستخدم 5000
    port = int(os.environ.get('PORT', 5000))
    # إيقاف وضع التطوير (debug=False) لأنه السيرفر الآن في مرحلة الإنتاج (Production)
    app.run(host='0.0.0.0', port=port, debug=False)