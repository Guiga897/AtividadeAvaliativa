from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import random
import requests
import os
from datetime import datetime
import threading

app = Flask(__name__)

# Configuração do Banco de Dados (Pontos de substituição)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://USUARIO:SENHA@HOST/NOME_DO_BANCO'  # <--- Substituir aqui
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Variáveis globais com lock
current_data = {
    'temperature': 0.0,
    'humidity': 0.0,
    'presence': False,
    'voltage': 0.0
}
data_lock = threading.Lock()

# Modelo do Banco de Dados
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    presence = db.Column(db.Boolean)
    voltage = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def generate_sensor_data():
    with data_lock:
        # Gera dados simulados
        current_data.update({
            'temperature': round(random.uniform(20.0, 30.0), 2),
            'humidity': round(random.uniform(40.0, 60.0), 2),
            'presence': random.choice([True, False]),
            'voltage': round(random.uniform(210.0, 230.0), 2)
        })
        
        # Persiste no banco
        new_entry = SensorData(**current_data)
        db.session.add(new_entry)
        db.session.commit()

def send_to_thingspeak():
    with data_lock:
        payload = current_data.copy()
    payload['presence'] = 1 if payload['presence'] else 0
    
    requests.get(
        f'https://api.thingspeak.com/update?api_key=CGUAWWUJC80DT21Y&field1=0'
        f'&field1={payload["temperature"]}'
        f'&field2={payload["humidity"]}'
        f'&field3={payload["presence"]}'
        f'&field4={payload["voltage"]}'
    )

@app.before_first_request
def initialize():
    # Cria tabelas se não existirem
    db.create_all()
    
    # Configura agendadores
    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_sensor_data, 'interval', seconds=5)
    scheduler.add_job(send_to_thingspeak, 'interval', seconds=15)
    scheduler.start()

@app.route('/dados', methods=['GET'])
def get_data():
    with data_lock:
        return jsonify(current_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)