import machine
from umqtt.simple import MQTTClient
import ubinascii
import machine
import time

time.sleep(1)

# Clear Oled and Print new text
def print_oled(display_text,x,y):
    oled.fill(0)
    oled.text(display_text,x,y,1)
    oled.show()



## MQTT config
topic_sub = b'rcv_esp8266'
topic_pub = b'esp8266'
mqtt_server = '192.168.0.2'
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
  print_txt = b'Connected to MQTT broker: '+mqtt_server+', subscribed to topic:' + topic_sub
  print(print_txt)
  print_oled(print_txt,1,1)
  return client


def restart_and_reconnect():
  print_txt = 'Failed to connect to MQTT broker. Reconnecting...'
  print(print_txt)
  print_oled(print_txt,3,3)
  time.sleep(10)
  machine.reset()

## MQTT Connect
try:
  client = connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()

    
# Check for new message every second - Non Blocking
listen_txt = b'Listening for new messages from topic - '+topic_sub
print(listen_txt)
print_oled(listen_txt,3,3)
while True:
  try:
    new_message = client.check_msg()
#    if new_message != 'None':
#        print('New message received :',new_message)
#      client.publish(topic_pub, b'new message received')
    time.sleep(10)
  except OSError as e:
    restart_and_reconnect()
    
