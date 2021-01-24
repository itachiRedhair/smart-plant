import json
import topics
import datetime
import pytz
import time


class Handler:
    def __init__(self):
        pass

    def set_mqtt_client(self, mqtt):
        self.mqtt_client = mqtt.client

    def set_basil_database(self, mongodbclient):
        self.basil_db = mongodbclient.basil_db
        self.moisture_sensor_reading = self.basil_db.moisture_sensor_reading
        self.pump_water_status = self.basil_db.pump_water_status

    def moisture_analog_topic(self, topic, msg):
        # FIXME: For some reasons json.loads converting string to string, not dict
        # As a workaround I am being forced to call it twice
        # Find what's the bug, and fix it.
        json_msg = json.loads(json.loads(msg))
        # In embedded systems, epoch time is from year 2000, that's why +946684800
        json_msg["timestamp"] = json_msg["timestamp"]+946684800
        try:
            id = self.moisture_sensor_reading.insert_one(json_msg).inserted_id
            print("New Moisture sensor reading added", id)
        except Exception as e:
            print("Error while inserting moisture sensor reading", e)
            raise(e)

    def pump_water_topic(self, topic, msg):
        # FIXME: For some reasons json.loads converting string to string, not dict
        # As a workaround I am being forced to call it twice
        # Find what's the bug, and fix it.
        json_msg = json.loads(json.loads(msg))
        # In embedded systems, epoch time is from year 2000, that's why +946684800
        json_msg["timestamp"] = json_msg["timestamp"]+946684800
        try:
            id = self.pump_water_status.insert_one(json_msg).inserted_id
            print("New pump water status added", id)
        except Exception as e:
            print("Error while inserting pump water status", e)
            raise(e)

    def set_moisture_reading_frequency(self, frequency=30):
        json_msg = {
            "frequency": frequency
        }
        try:
            print("Publishing set moisture read frequency command")
            self.mqtt_client.publish(
                topics.BASIL_MOISTURE_FREQ_COMMAND_TOPIC, json.dumps(json_msg))
        except Exception as e:
            print("Error while publishing set moisture read frequency with msg", json_msg)

    def start_pump(self, duration=0):
        json_msg = {
            "command": "ON",
            "duration": duration
        }
        try:
            print("Publishing start pump command")
            self.mqtt_client.publish(
                topics.PUMP_ONOFF_COMMAND_TOPIC, json.dumps(json_msg))
        except Exception as e:
            print("Error while publishing start pump comamnd with msg", json_msg)

    def stop_pump(self):
        json_msg = {
            "command": "OFF",
        }
        try:
            print("Publishing stop pump command")
            self.mqtt_client.publish(
                topics.PUMP_ONOFF_COMMAND_TOPIC, json.dumps(json_msg))
        except Exception as e:
            print("Error while publishing stop pump comamnd with msg", json_msg)

    def get_moisture_reading_data(self, from_time, interval="hourly"):
        common_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gt": from_time},
                }
            },
            {
                "$project": {
                    "timestamp": {
                        "$toDate": {
                            "$multiply": [
                                '$timestamp', 1000]
                        }
                    },
                    "analog_value":1,
                    "moisture_level":1
                }
            },
        ]
        pipeline = {
            "minutely": [
                *common_pipeline,
                {
                    "$project": {
                        "timestamp": 1, "timestampMinute": {
                            "$minute": "$timestamp"
                        },
                        "timestampHour": {
                            "$hour": "$timestamp"
                        }, "analog_value": 1, "moisture_level": 1
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "minute": "$timestampMinute",
                            "hour": "$timestampHour"
                        },
                        "value": {
                            "$avg": "$analog_value"
                        }
                    }
                },
                {
                    "$sort": {
                        "_id.hour": 1, "_id.minute": 1
                    }
                }
            ],
            "hourly": [
                *common_pipeline,
                {
                    "$project": {
                        "timestamp": 1,
                        "timestampHour": {
                            "$hour": "$timestamp"
                        },
                        "timestampDay": {
                            "$dayOfMonth": "$timestamp"
                        },
                        "analog_value": 1,
                        "moisture_level": 1
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "hour": "$timestampHour",
                            "day": "$timestampDay"
                        },
                        "value": {
                            "$avg": "$analog_value"
                        }
                    }
                },
                {
                    "$sort": {
                        "_id.day": 1, "_id.hour": 1
                    }
                }
            ]
        }
        data = self.moisture_sensor_reading.aggregate(pipeline[interval])
        return list(data)

    def get_water_status(self, count):
        data = self.pump_water_status.find({}).sort("timestamp").limit(count)
        return map(lambda x: {"timestamp": time.strftime('%d %b %H:%M', time.localtime(x["timestamp"])), "duration": x["duration"]}, list(data))
