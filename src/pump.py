import machine
from machine import Pin, ADC
import time
import ujson
import uasyncio
import topics
import moisturesensor
from moisturesensor import MoistureSensor

PUMP_WATER_DURATIONS = {
    moisturesensor.TOO_DRY: 3,
    moisturesensor.DRY: 2,
    moisturesensor.MEDIUM: 1,
    moisturesensor.WET: 0,
    moisturesensor.TOO_WET: 0,
}


class Pump:
    def __init__(self):
        self.pumpOutPin = Pin(12, Pin.OUT)
        self.pumpOutPin.off()
        self.moisture_read_frequency = 30

    def set_moisture_read_frequency(self, frequency):
        print("Setting moisture sensor read frequency to", frequency)
        self.moisture_read_frequency = frequency

    def check_moisture_and_water(self, moisture_sensor, mqtt=None):
        moisture_level = moisture_sensor.getMoistureLevel(mqtt)
        duration = PUMP_WATER_DURATIONS[moisture_level]
        if duration:
            self.water_for_duration(duration, mqtt)

    def water_for_duration(self, duration, mqtt=None):
        print("Pumping water for duration", duration)
        try:
            self.startPump()
            json_msg = {
                "duration": duration,
                "timestamp": time.time()
            }
            msg = ujson.dumps(json_msg)
            try:
                mqtt.client.publish(
                    topics.PUMP_WATER_TOPIC, ujson.dumps(msg))

            except Exception as e:
                print("Error while publishing on MQTT Topic",
                      topics.PUMP_WATER_TOPIC, "with message", msg)
                mqtt.restart_and_reconnect()

            time.sleep(duration)
            self.stopPump()
        except Exception as e:
            print("Error while pumping water:", e)
            raise(e)
        finally:
            self.stopPump()

    def startPump(self):
        print("Starting pump...")
        try:
            self.pumpOutPin.on()
        except Exception as e:
            print("Error while starting pump:", e)
            raise(e)

    def stopPump(self):
        print("Stopping pump...")
        try:
            self.pumpOutPin.off()
        except Exception as e:
            print("Error while stopping pump:", e)
            raise(e)
