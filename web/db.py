import paho.mqtt.client as mqtt
import os
import pymongo


class Database:
    def __init__(self, connection_string):
        self.client = pymongo.MongoClient(connection_string)
        self.basil_db = self.client.basil
