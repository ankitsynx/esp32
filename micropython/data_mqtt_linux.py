import RPi.GPIO as io
import os
import json
from time import sleep
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

############### MQTT section ##################

Broker = "192.168.1.10"

rcv_topic = "home/groundfloor/livingroom/lights/lightx"    # receive messages on this topic
snd_topic = "home/groundfloor/kitchen/lights/lightx"       # send messages to this topic

def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))
    mqttc.subscribe(rcv_topic) #receving/subscriber    

#when receving a message:
def on_message(mqttc, obj, msg):
    print("sub") #this is not being executed on button push, but it is when I publish through the MQTTLens
    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
    try:
        p = msg.payload.decode("utf-8")
        print("decoded payload: " + p)
        x = json.loads(p)
        set_leds(leds, tuple(x['leds'])) #set leds to received value

        return
    except Exception as e:
        print(e)

# callback functie voor publish  event
def on_publish(mqttc, obj, mid):
    print("pub")
    return

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.connect(Broker, 1883, 60) #last could be a port too
mqttc.loop_start() #client.loop_forever()

############### led&button section ##################
def init_leds(leds):
    io.setup(leds, io.OUT)

def set_leds(leds, states):
    print("leds and states: " + str(leds) + " " + str(states))
    io.output(leds, states)

def snd_msg(led):
    dataToSend=json.dumps({"leds":[led1State,led2State]})
    print("data: " + dataToSend)
    mqttc.publish(snd_topic, dataToSend)

io.add_event_detect(btn1,io.FALLING,callback=lambda *a: snd_msg(1),bouncetime=500)

############### main ##################

def main():
    try:
        while True:
            init_leds(leds)
    except KeyboardInterrupt:
        pass
    finally:
        io.cleanup()

#toplevel script
#below will only execute if ran directly - above is always accessible
if __name__ == '__main__':
    main()
