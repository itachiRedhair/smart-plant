import machine
from machine import Pin, ADC
import time
import topics
import ujson

TOO_DRY = "TOO_DRY"
DRY = "DRY"
MEDIUM = "MEDIUM"
WET = "WET"
TOO_WET = "TOO_WET"

MOISTURE_THRESHOLDS = [
    {"level": TOO_DRY, "value": 950},
    {"level": DRY, "value": 800},
    {"level": MEDIUM, "value": 600},
    {"level": WET, "value": 300},
    {"level": TOO_WET, "value": 0},
]


class MoistureSensor:
    def __init__(self):
        self.moistureDigitalPin = Pin(14, Pin.IN)
        self.moistureAnalogPin = ADC(0)

    def isDryDigitally(self):
        return False if self.moistureDigitalPin.value() == 0 else False

    def getMoistureLevel(self, mqtt=None):
        analog_value = self.moistureAnalogPin.read()

        moisture_level = MOISTURE_THRESHOLDS[-1]["level"]

        for moisture_threshold in MOISTURE_THRESHOLDS:
            if analog_value > moisture_threshold["value"]:
                moisture_level = moisture_threshold["level"]

        if mqtt:
            json_msg = {
                "moisture_level": moisture_level,
                "analog_value": analog_value,
                "timestamp": time.time()
            }
            msg = ujson.dumps(json_msg)
            try:
                mqtt.client.publish(
                    topics.BASIL_MOISTURE_ANALOG_TOPIC, ujson.dumps(msg))
            except Exception as e:
                print("Error while publishing on MQTT Topic",
                      topics.BASIL_MOISTURE_ANALOG_TOPIC, "with message", msg)
                mqtt.restart_and_reconnect()

        print("Moisture Level", moisture_level, "Analog Value", analog_value)
        return moisture_level
