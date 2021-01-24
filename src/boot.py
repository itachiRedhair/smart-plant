import network
import configenv
import time
from machine import Pin

wifi_ssid = configenv.get_wifi_ssid()
wifi_password = configenv.get_wifi_password()


def configure_wifi():
    station = network.WLAN(network.STA_IF)
    access_point = network.WLAN(network.AP_IF)

    # access_point.active(False)

    if not station.isconnected():
        print('connecting to network...')
        station.active(True)

        station.connect(wifi_ssid, wifi_password)
        while not station.isconnected():
            pass
    print('Station Network config:', station.ifconfig())
    print('Access Point Network config:', access_point.ifconfig())


def configure_gpio():
    Pin(12, Pin.OUT).off()


configure_wifi()

configure_gpio()
