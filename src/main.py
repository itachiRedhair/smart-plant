import machine
from machine import Pin, ADC
import time
import ujson
import uasyncio
from mqttfactory import MQTTFactory
from pump import Pump
from moisturesensor import MoistureSensor
import configenv
import topics


moisture_sensor_frequency = 5


def create_mqtt_subscribe_callback(pump, moisture_sensor, mqtt):
    def mqtt_subscribe_callback(topic, msg):
        if topic.decode() == topics.PUMP_ONOFF_COMMAND_TOPIC:
            pump_command_topic_handler(topic, msg, pump, mqtt)
        elif topic.decode() == topics.BASIL_MOISTURE_FREQ_COMMAND_TOPIC:
            moisture_freq_command_topic_handler(topic, msg, pump)
    return mqtt_subscribe_callback


def pump_command_topic_handler(topic, msg, pump, mqtt):
    json_msg = ujson.loads(msg.decode())
    command = json_msg["command"]
    if command == "ON":
        if "duration" in json_msg:
            duration = json_msg["duration"]
            pump.water_for_duration(duration, mqtt)
        else:
            pump.water_for_duration(1, mqtt)
    elif command == "OFF":
        pump.stopPump()


def moisture_freq_command_topic_handler(topic, msg, pump):
    global moisture_sensor_frequency
    json_msg = ujson.loads(msg.decode())
    if "frequency" in json_msg:
        frequency = json_msg["frequency"]
        print("Setting moisture read frqeuency to", frequency)
        pump.set_moisture_read_frequency(frequency)


def initialize_mqtt(pump, moisture_sensor):
    mqtt = MQTTFactory()
    try:
        mqtt.connect_and_subscribe(create_mqtt_subscribe_callback(pump, moisture_sensor, mqtt), sub_topics=[
                                   topics.PUMP_ONOFF_COMMAND_TOPIC,
                                   topics.BASIL_MOISTURE_FREQ_COMMAND_TOPIC,
                                   ])
        return mqtt
    except OSError as e:
        print(e)
        mqtt.restart_and_reconnect()


pump = Pump()
moisture_sensor = MoistureSensor()
mqtt = initialize_mqtt(pump, moisture_sensor)


async def check_mqtt_msg():
    while True:
        # Non-blocking wait for message
        mqtt.client.check_msg()
        # Then need to sleep to avoid 100% CPU usage (in a real
        # app other useful actions would be performed instead)
        await uasyncio.sleep(5)


async def check_moisture_and_water():
    while True:
        pump.check_moisture_and_water(moisture_sensor, mqtt)
        await uasyncio.sleep(pump.moisture_read_frequency)


async def main():
    uasyncio.create_task(check_moisture_and_water())
    uasyncio.create_task(check_mqtt_msg())
    while True:
        await uasyncio.sleep(100)

uasyncio.run(main())

# check_moisture_loop = uasyncio.get_event_loop()
# check_moisture_loop.run_forever(check_moisture_and_water())

# mqtt_loop = uasyncio.get_event_loop()
# mqtt_loop.run_forever(check_mqtt_msg())
