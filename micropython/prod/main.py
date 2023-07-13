import machine
from umqtt.simple import MQTTClient
import ubinascii
import machine
import time


## MQTT config
topic_sub = b'rcv_esp8266'
topic_pub = b'esp8266'
mqtt_server = '192.168.0.2' #Update IP as per network settings
client_id = ubinascii.hexlify(machine.unique_id())

def sub_cb(topic, msg):
  print((topic, msg))
  
def connect_and_subscribe():
  global client_id, mqtt_server, topic_sub
  print(client_id, mqtt_server, topic_sub)
  client = MQTTClient(client_id, mqtt_server,keepalive=30)
  client.set_callback(sub_cb)
  client.connect()
  client.subscribe(topic_sub)
  print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
  return client


def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

## MQTT Connect
try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

## Publish Message
msg = 'Message to test Publish'
try:
    client.publish(topic_pub, msg)
except OSError as e:
    restart_and_reconnect()
    
# Check for new message every second - Non Blocking
print('Waiting for new messages from topic - ',topic_pub) 
while True:
  try:
    new_message = client.check_msg()
    if new_message != 'None':
      client.publish(topic_pub, b'new message received')
    time.sleep(1)
  except OSError as e:
    print('Warning! Restarting process.')        
    restart_and_reconnect()
