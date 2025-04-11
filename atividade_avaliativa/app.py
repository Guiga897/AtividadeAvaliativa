from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS
import random
import requests
import os
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Variáveis em memória
current_temperature = 0.0
current_humidity = 0.0
current_presence = False
data_lock = threading.Lock()

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    presence = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def generate_sensor_data():
    global current_temperature, current_humidity, current_presence
    with data_lock:
        current_temperature = round(random.uniform(20.0, 30.0), 2)
        current_humidity = round(random.uniform(40.0, 60.0), 2)
        current_presence = random.choice([True, False])
        new_data = SensorData(
            temperature=current_temperature,
            humidity=current_humidity,
            presence=current_presence
        )
        db.session.add(new_data)
        db.session.commit()

def send_to_thingspeak():
    with data_lock:
        temp = current_temperature
        hum = current_humidity
        pres = 1 if current_presence else 0
    api_key = os.getenv('THINGSPEAK_API_KEY')
    url = f'https://api.thingspeak.com/update?api_key={api_key}&field1={temp}&field2={hum}&field3={pres}'
    requests.get(url)

@app.before_first_request
def initialize():
    db.create_all()
    latest = SensorData.query.order_by(SensorData.timestamp.desc()).first()
    if latest:
        global current_temperature, current_humidity, current_presence
        with data_lock:
            current_temperature = latest.temperature
            current_humidity = latest.humidity
            current_presence = latest.presence
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_sensor_data, 'interval', seconds=5)
    scheduler.add_job(send_to_thingspeak, 'interval', seconds=15)
    scheduler.start()

@app.route('/dados', methods=['GET'])
def get_data():
    with data_lock:
        return jsonify({
            'temperature': current_temperature,
            'humidity': current_humidity,
            'presence': current_presence
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)