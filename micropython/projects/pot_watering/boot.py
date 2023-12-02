# This file is executed on every boot (including wake-boot from deepsleep)
import uos, machine
import sys
import gc
import webrepl
import time
import network
import esp
import BlynkLib

## WiFi Config
ssid = 'Ankit'
password = 'Password'

print("Connecting to Wifi Network: ",ssid)
## Wifi Connection
station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connected to Wifi network: ',ssid)
print(station.ifconfig())

## WebREPL run
webrepl.start()
gc.collect()
sys.path.reverse()
# Disable debug output to avoid issues with Webrepl
esp.osdebug(None)


##Blynk
# Fill-in information from Blynk Device Info here 
BLYNK_TEMPLATE_ID = "TMPL3ocj5gXoX"
BLYNK_TEMPLATE_NAME = "Quickstart Template"
BLYNK_AUTH_TOKEN = "sjWj7u-LOoovHvqSgWmB-Pu5wh6efwbz"

blynk = BlynkLib.Blynk(BLYNK_AUTH_TOKEN)

@blynk.on("connected")
def blynk_connected(ping):
    print('Blynk ready. Ping:', ping, 'ms')

@blynk.on("disconnected")
def blynk_disconnected():
    print('Blynk disconnected')
    
    

