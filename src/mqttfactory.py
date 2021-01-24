from lib.umqttsimple import MQTTClient
import time
import machine
import ubinascii
import configenv


class MQTTFactory:
    def __init__(self):
        self.mqtt_server = configenv.get_mqtt_broker()

    def connect_and_subscribe(self, subscribe_callback=None, sub_topics=[]):
        client_id = ubinascii.hexlify(machine.unique_id())
        print("Client ID used to connect to MQTT broke:", client_id)
        mqtt_user = configenv.get_mqtt_user()
        mqtt_password = configenv.get_mqtt_password()
        client = MQTTClient(client_id, self.mqtt_server,
                            user=mqtt_user, password=mqtt_password)

        if subscribe_callback:
            client.set_callback(subscribe_callback)

        client.connect()

        for topic in sub_topics:
            client.subscribe(topic)

        print('Connected to %s MQTT broker, subscribed to %s topics' %
              (self.mqtt_server, ",".join(sub_topics)))
        self.client = client
        return client

    def restart_and_reconnect(self):
        print('Failed to connect to MQTT broker. Reconnecting...')
        time.sleep(10)
        machine.reset()
