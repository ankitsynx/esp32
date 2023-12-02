import machine
import ubinascii
import time
import BlynkLib


## Water Sensor
check_interval = 5
d_probe = machine.Pin(5,machine.Pin.IN)
probe_state = machine.Pin(4,machine.Pin.OUT)
motor = machine.Pin(14,machine.Pin.OUT)
a_probe = machine.ADC(0)

while True:
    probe_state.on()
    blynk.run()
    time.sleep(1)
    d_probe_in = d_probe.value()
    a_probe_in = a_probe.read()
    print('Current analog value : {}'.format(a_probe_in))
    hum_prcnt = round(100-(a_probe_in/1023)*100,1)
    print('Humidity : {}%'.format(hum_prcnt))
    blynk.virtual_write(0, hum_prcnt)
    blynk.virtual_write(1,d_probe_in)
    if d_probe_in == 1:
        print("Dry")
        blynk.virtual_write(1,"Dry")
        motor.off()  ## Inverted output for turning relay on
        print('Motor turned on')
        time.sleep(10)
        motor.on()  ## Inverted output for turning relay off
        print('Motor turned off')
    else:
        print("Wet")
        blynk.virtual_write(1,"Wet")
            
    probe_state.off()
    time.sleep(check_interval)
    #machine.deepsleep(5)



    

