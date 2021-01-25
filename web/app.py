from flask import Flask, request, render_template
import os
import time
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
from collections import deque
from datetime import datetime
import topics
from handlers import Handler
from db import Database
from plantmqtt import PlantMQTT

PORT = os.environ["FLASK_PORT"]

app = Flask(__name__)

handler = Handler()


def initialize_mqtt():
    MQTT_BROKER = os.environ['MQTT_BROKER']
    MQTT_USER = os.environ['MQTT_USER']
    MQTT_PASSWORD = os.environ['MQTT_PASSWORD']
    MQTT_CLIENT_ID = os.environ['MQTT_CLIENT_ID']

    topic_handlers = {
        topics.BASIL_MOISTURE_ANALOG_TOPIC: handler.moisture_analog_topic,
        topics.PUMP_WATER_TOPIC: handler.pump_water_topic
    }

    plant_mqtt = PlantMQTT(
        MQTT_BROKER,
        MQTT_CLIENT_ID,
        MQTT_USER,
        MQTT_PASSWORD,
        topic_handlers=topic_handlers)

    return plant_mqtt


def initialize_mongodb():
    MONGO_CONNECTION_STRING = os.environ['MONGO_CONNECTION_STRING']
    mongodb = Database(MONGO_CONNECTION_STRING)
    return mongodb


@app.route('/')
def index():
    day_before_epoch = int(time.mktime(
        (datetime.now() - timedelta(days=1)).timetuple()))
    moisture_readings = handler.get_moisture_reading_data(
        day_before_epoch, "hourly")
    water_statuses = handler.get_water_status(10)
    return render_template("index.html", moisture_readings=moisture_readings, water_statuses=water_statuses)


@app.route('/moisture_sensor/frequency', methods=['POST'])
def set_moisture_reading_frequency():
    data = request.json
    frequency = data["frequency"]
    handler.set_moisture_reading_frequency(frequency)
    return "OK"


@app.route('/pump/start', methods=['POST'])
def start_pump():
    data = request.json
    duration = data["duration"]
    handler.start_pump(duration)
    return "OK"


@app.route('/pump/stop', methods=['POST'])
def stop_pump():
    handler.stop_pump()
    return "OK"


plant_mqtt = None
mongodb = None

if __name__ == '__main__':
    plant_mqtt = initialize_mqtt()
    plant_mqtt.client.loop_start()

    mongodb = initialize_mongodb()

    handler.set_mqtt_client(plant_mqtt)
    handler.set_basil_database(mongodb)

    app.run(host='0.0.0.0', port=PORT)
