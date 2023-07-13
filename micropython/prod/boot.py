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
#ESP8266 Pin Assignment
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=100000)
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)


## WiFi Config
ssid = 'Ankit'
password = 'Password123'



## Wifi Connect
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connected to Wifi network: ',ssid)
oled.fill_rect(0, 0, 32, 32, 1)
oled.fill_rect(2, 2, 28, 28, 0)
oled.vline(9, 8, 22, 1)
oled.vline(16, 2, 22, 1)
oled.vline(23, 8, 22, 1)
oled.fill_rect(26, 24, 2, 4, 1)
oled.text('MicroPython', 40, 0, 1)
oled.text('SSD1306', 40, 12, 1)
oled.text('OLED 128x64', 40, 24, 1)
oled.show()
print(station.ifconfig())

## WebREPL run
webrepl.start()
gc.collect()
sys.path.reverse()
# Disable debug output to avoid issues with Webrepl
esp.osdebug(None)


