#Particle density reader https://github.com/sharpsensoruser/sharp-sensor-demos/tree/master/sharp_gp2y1014au0f_demo
##Connections on GP2Y1014
# Pin 1 - starting from the pin closer to the sensor edge
# Pin 1 - V-Led
# Pin 2 - LED-GND
# Pin 3 - LED
# Pin 4 - S-GND
# Pin 5 - Vo
# Pin 6 - Vcc
## 

from machine import Pin, ADC
from time import sleep

reading = ADC(0)
##For ESP32 add below for Full range: 3.3v
#pot.atten(ADC.ATTN_11DB)       

#Setting LED pin D1(GPIO5)
led = Pin(5, Pin.OUT)

# Offset correction, update as required - typically 0.6V (Analog voltage reading in no dust conditions)
vo_c = 2.0

# dust density sensitivity constant from sharp (scalar coefficient) [0.5 Volts/(100 ug/m3)]
k = 0.5
##No of samples to be taken for average
n=100
vo_raw_sum = 0
vo_raw_count = 0
vo_volts = vo_c

while True:
  led.value(1)
  sleep(0.00028)
  #Read raw reading (0-1023)
  vo_raw = reading.read()
  vo_raw_sum += vo_raw
  vo_raw_count += 1
  if vo_raw_count >= n:
      vo_avg = vo_raw_sum/vo_raw_count
      #Voltage conversion
      vo_volts = (vo_avg/1024*3.3)
      dust_density = (vo_volts-vo_c)/k*100.0
      print(vo_raw, vo_c, vo_volts,"V",dust_density,"ug/m3")
      vo_raw_sum = 0
      vo_raw_count = 0      
  led.value(0)
  sleep(0.00968)
  
  #print("\nAnalog reading:", vo_raw, "\nOffset Voltage:", vo_c, "\nDetected Voltage:",vo_volts,"\nDust Densiy:", dust_density,"ug/m3")
  #print("----------------------------")
  if vo_volts < vo_c:
      vo_c=vo_volts
  
