import paho.mqtt.client as mqtt
import os
import topics


class PlantMQTT:
    def __init__(self, broker, client_id, username, password, topic_handlers={}):
        self.client = mqtt.Client(client_id=client_id)
        self.client.username_pw_set(username=username, password=password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, 1883, 60)
        self.topic_handlers = topic_handlers

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        for topic in self.topic_handlers:
            client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        msg = msg.payload.decode()
        if topic in self.topic_handlers:
            self.topic_handlers[topic](topic, msg)
