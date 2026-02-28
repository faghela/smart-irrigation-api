# 🌱 Smart Irrigation System | نظام الري الذكي

An AI-powered smart irrigation system that uses machine learning to decide when to activate the water pump, based on real-time sensor data (soil moisture, temperature, humidity).

## 📁 Project Structure

```
Smart_Irrigation_Project/
├── Hardware/
│   └── smart_irrigation.ino      # Arduino/ESP code for sensors
├── Data/
│   └── irrigation_data.csv       # Training dataset
├── ML_Backend/
│   ├── app.py                    # Flask entry point
│   ├── config.py                 # Settings & environment variables
│   ├── database.py               # MongoDB connection
│   ├── auth.py                   # Authentication (login/logout)
│   ├── routes/
│   │   ├── dashboard.py          # Dashboard page
│   │   ├── api.py                # REST APIs (sensors, weather, pump)
│   │   └── predict.py            # AI prediction endpoint
│   ├── templates/
│   │   ├── login.html            # Login page (2026 Futuristic UI)
│   │   └── dashboard.html        # Dashboard (Neon Cyber theme)
│   ├── irrigation_model.pkl      # Trained ML model
│   ├── train_model.py            # Script to retrain the model
│   ├── requirements.txt          # Python dependencies
│   └── Procfile                  # For deployment (Railway/Heroku)
└── .gitignore
```

## 🚀 Quick Start

```bash
cd ML_Backend
pip install -r requirements.txt
python app.py
```

Open **http://localhost:8080** → Login with your credentials.

## ⚡ Features

- 🔐 Session-based authentication
- 📊 Real-time sensor monitoring (auto-refresh every 5s)
- 📈 Chart.js history visualization
- ⛅ Live weather from OpenWeatherMap (+ Open-Meteo fallback)
- 🤖 AI Testing Panel (test predictions without hardware)
- 🕹️ Manual pump control (Force Start / Emergency Stop)
- 🌍 Bilingual interface (Arabic + English)

## 🔑 Default Credentials

| Setting | Value |
|---|---|
| User ID | `mohamed_f` |
| Token | `123456` |

> Change via environment variables `USER_ID` and `USER_TOKEN`.
