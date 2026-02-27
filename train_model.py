import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# 1. اسم الملف (تأكد أن الاسم مطابق لما هو موجود في مجلدك)
file_name = 'irrigation_data.csv.csv' 

try:
    print(f"جاري قراءة الملف: {file_name}...")
    # استخدام sep=None يجعله يتعرف تلقائياً على الفاصل سواء كان فاصلة (,) أو نقطة فاصلة (;)
    df = pd.read_csv(file_name, sep=None, engine='python')

    # تنظيف أسماء الأعمدة من أي مسافات زائدة
    df.columns = df.columns.str.strip()

    print("--- الأعمدة التي تم العثور عليها ---")
    print(df.columns.tolist())
    
    # 2. تحديد المدخلات والمخرجات (بناءً على ملفك بالضبط)
    X_columns = ['Soil Moisture Resistance (Ohm)', 'Ambient Temperature (deg. C)', 'Atmospheric Humidity (%)']
    y_column = 'DC Water pump Status'

    X = df[X_columns].values
    y = df[y_column].values

    print("\nجاري تدريب المودل...")
    model = DecisionTreeClassifier()
    model.fit(X, y)

    # 3. حفظ المودل
    joblib.dump(model, 'irrigation_model.pkl')
    print("✅ تم بنجاح! تم حفظ المودل الجديد باسم irrigation_model.pkl")

except FileNotFoundError:
    print(f"❌ خطأ: لم يتم العثور على الملف '{file_name}'. تأكد من وجوده في نفس المجلد.")
except KeyError as e:
    print(f"❌ خطأ في أسماء الأعمدة: {e}")
except Exception as e:
    print(f"❌ حدث خطأ غير متوقع: {e}")