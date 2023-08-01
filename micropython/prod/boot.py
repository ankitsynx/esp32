# This file is executed on every boot (including wake-boot from deepsleep)
import uos, machine
import sys
import gc
import webrepl
import time
import network
import esp
import ssd1306
from machine import Pin, SoftI2C


## OLED Config Ref- https://docs.micropython.org/en/latest/esp8266/tutorial/ssd1306.html#ssd1306
# Connect SCl - D1 SDA -D2 ESP8266//SCL-GPIO 22 SDA GPIO 21 ESP32
# ESP32 Pin assignment 
#i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
# ESP8266 Pin Assignment
try:
    i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)
    oled_width = 128
    oled_height = 64
    oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
    oled.fill(0)
except:
    print('OLED display not connected')
## WiFi Config
ssid = 'Ankit'
password = 'Password'

## Wifi Connection
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connected to Wifi network: ',ssid)
oled.text('Connected to Wifi network: ', 3, 3, 1)
oled.show()
print(station.ifconfig())

## WebREPL run
webrepl.start()
gc.collect()
sys.path.reverse()
# Disable debug output to avoid issues with Webrepl
esp.osdebug(None)


