import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

# تحديد مسار ملف البيانات
data_path = 'irrigation_data.csv'

if os.path.exists(data_path):
    # 1. تحميل البيانات
    df = pd.read_csv(data_path)
    print("--- تم تحميل البيانات بنجاح ---")

    # 2. تحديد المدخلات والمخرجات
    X = df[['temperature', 'humidity', 'soil_moisture', 'light', 'rainfall']]
    y = df['irrigation_required']

    # 3. تقسيم البيانات
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. تدريب النموذج
    model = DecisionTreeClassifier()
    model.fit(X_train, y_train)

    # 5. حساب الدقة
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"--- دقة النموذج هي: {accuracy * 100:.2f}% ---")

    # 6. حفظ النموذج
    joblib.dump(model, 'ML_Backend/irrigation_model.pkl')
    print("--- تم حفظ الملف باسم irrigation_model.pkl داخل مجلد ML_Backend ---")
else:
    print(f"خطأ: لم يتم العثور على ملف {data_path}. تأكد من تشغيل generate_data.py أولاً.")