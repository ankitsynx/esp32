#include <ESP32Time.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "certs.h" // include the connection infor for WiFi and MQTT
#include "sdkconfig.h" // used for log printing
#include "esp_system.h"
#include "freertos/FreeRTOS.h" //freeRTOS items to be used
#include "freertos/task.h"
#include <driver/adc.h>
#include <SimpleKalmanFilter.h>
////
WiFiClient      wifiClient; // do the WiFi instantiation thing
PubSubClient    MQTTclient( mqtt_server, mqtt_port, wifiClient ); //do the MQTT instantiation thing
ESP32Time       rtc;
////
#define evtDoParticleRead      ( 1 << 0 ) // declare an event
EventGroupHandle_t eg; // variable for the event group handle
////
SemaphoreHandle_t sema_MQTT_KeepAlive;
SemaphoreHandle_t sema_mqttOK;
////
int mqttOK = 0;
bool TimeSet = false;
////
// interrupt service routine for WiFi events put into IRAM
void IRAM_ATTR WiFiEvent(WiFiEvent_t event)
{
  switch (event) {
    case SYSTEM_EVENT_STA_CONNECTED:
      break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
      log_i("Disconnected from WiFi access point");
      break;
    case SYSTEM_EVENT_AP_STADISCONNECTED:
      log_i("WiFi client disconnected");
      break;
    default: break;
  }
} // void IRAM_ATTR WiFiEvent(WiFiEvent_t event)
////
void IRAM_ATTR mqttCallback(char* topic, byte * payload, unsigned int length)
{
  xSemaphoreTake( sema_mqttOK, portMAX_DELAY );
  mqttOK = 0;
  xSemaphoreGive( sema_mqttOK );
  //  Ugly, I know...
  if ( !TimeSet )
  {
    int i = 0;
    char strPayload[length + 1];
    String temp = "";
    for ( i; i < length; i++)
    {
      strPayload[i] = ((char)payload[i]);
    }
    strPayload[i] = NULL;
    temp = strPayload[0];
    temp += strPayload[1];
    temp += strPayload[2];
    temp += strPayload[3];
    int year =  temp.toInt();
    temp = "";
    temp = strPayload[5];
    temp += strPayload[6];
    int month =  temp.toInt();
    temp = "";
    temp = strPayload[8];
    temp += strPayload[9];
    int day =  temp.toInt();
    temp = "";
    temp = strPayload[11];
    temp += strPayload[12];
    int hour =  temp.toInt();
    temp = "";
    temp = strPayload[14];
    temp += strPayload[15];
    int min =  temp.toInt();
    rtc.setTime( 0, min, hour, day, month, year );
    log_i( "%s  ", rtc.getTime() );
    TimeSet = true;
  }
} // void mqttCallback(char* topic, byte* payload, unsigned int length)
////
void setup()
{
  sema_mqttOK    =  xSemaphoreCreateBinary();
  xSemaphoreGive( sema_mqttOK );
  gpio_config_t io_cfg = {}; // initialize the gpio configuration structure
  io_cfg.mode = GPIO_MODE_INPUT; // set gpio mode. GPIO_NUM_0 input from water level sensor
  io_cfg.pin_bit_mask = ( (1ULL << GPIO_NUM_0)); //bit mask of the pins to set, assign gpio number to be configured
  gpio_config(&io_cfg); // configure the gpio based upon the parameters as set in the configuration structure
  ////
  io_cfg = {};
  io_cfg.mode = GPIO_MODE_OUppTPUT;
  io_cfg.pin_bit_mask = ( (1ULL << GPIO_NUM_5) | (1ULL << GPIO_NUM_4) ); //bit mask of the pins to set, assign gpio number to be configured
  gpio_config(&io_cfg);
  gpio_set_level( GPIO_NUM_5, HIGH); // energize
  gpio_set_level( GPIO_NUM_4, LOW); // deenergize relay module
  // set up A:D channels  https://dl.espressif.com/doc/esp-idf/latest/api-reference/peripherals/adc.html
  adc1_config_width(ADC_WIDTH_12Bit);
  adc1_config_channel_atten(ADC1_CHANNEL_3, ADC_ATTEN_DB_11);// using GPIO 39
  //
  xTaskCreatePinnedToCore( MQTTkeepalive, "MQTTkeepalive", 20000, NULL, 6, NULL, 1 ); // create and start the two tasks to be used, set those task to use 20K stack
  xTaskCreatePinnedToCore( fDoMoistureDetector, "fDoMoistureDetector", 10000, NULL, 3, NULL, 1 ); // assign to core 1
  xTaskCreatePinnedToCore( fmqttWatchDog, "fmqttWatchDog", 3000, NULL, 3, NULL, 1 ); // assign all to core 1
} //void setup()
////
void fmqttWatchDog( void * paramater )
{
  int UpdateImeTrigger = 86400; //seconds in a day
  int UpdateTimeInterval = 86395;
  int maxNonMQTTresponse = 12;
  for (;;)
  {
    vTaskDelay( 5000 );
    xSemaphoreTake( sema_mqttOK, portMAX_DELAY ); // update mqttOK
    mqttOK++;
    xSemaphoreGive( sema_mqttOK );
    if ( mqttOK >= maxNonMQTTresponse )
    {
      ESP.restart();
    }
    UpdateTimeInterval++; // trigger new time get
    if ( UpdateTimeInterval >= UpdateImeTrigger )
    {
      TimeSet = false; // sets doneTime to false to get an updated time after a days count of seconds
      UpdateTimeInterval = 0;
    }
  }
  vTaskDelete( NULL );
} //void fmqttWatchDog( void * paramater )
////
void fDoMoistureDetector( void * parameter )
{
  //wait for a mqtt connection
  while ( !MQTTclient.connected() )
  {
    vTaskDelay( 250 );
  }
  /*
  */
  int      TimeToPublish = 5000000;
  int      TimeForADreading = 100 * 1000; // 100mS
  float    WetValue = 1.35f; // value found by putting sensor in water
  float    DryValue = 2.732f; // value of probe when held in air
  float    ADbits = 4095.0f;
  float    uPvolts = 3.3f;
  float    adcValue_b = 0.0f; //Jeanne's plant in yellow pot
  float    Range = DryValue - WetValue;
  float    RemainingMoisture = 100.0f; //prevents pump turn on during start up
  int      printCounts = 0;
  uint64_t TimePastKalman  = esp_timer_get_time(); // used by the Kalman filter
  uint64_t TimePastPublish = esp_timer_get_time(); // used by publish
  uint64_t TimeADreading   = esp_timer_get_time();
  TickType_t xLastWakeTime = xTaskGetTickCount();
  const TickType_t xFrequency = 10;
  SimpleKalmanFilter KF_ADC_b( 1.0f, 1.0f, .01f );
  for (;;)
  {
    //read AD values every 100mS.
    if ( (esp_timer_get_time() - TimeADreading) >= TimeForADreading )
    {
      adcValue_b = float( adc1_get_raw(ADC1_CHANNEL_3) ); //take a raw ADC reading
      adcValue_b = ( adcValue_b * uPvolts ) / ADbits; //calculate voltage
      KF_ADC_b.setProcessNoise( (esp_timer_get_time() - TimePastKalman) / 1000000.0f ); //get time, in microsecods, since last readings
      adcValue_b = KF_ADC_b.updateEstimate( adcValue_b ); // apply simple Kalman filter
      TimePastKalman = esp_timer_get_time(); // time of update complete
      RemainingMoisture = 100.0f * (1 - ((adcValue_b - WetValue) / (DryValue - WetValue))); //remaining moisture =  1-(xTarget - xMin) / (xMax - xMin) as a percentage of the sensor wet dry volatges
      TimeADreading = esp_timer_get_time();
    }
    //read gpio 0 is water level good. Yes: OK to run pump : no pump off.   remaining moisture good, denergize water pump otherwise energize water pump.
    if ( gpio_get_level( GPIO_NUM_0 ) )
    {
      if ( RemainingMoisture >= 40.0f ) {
        gpio_set_level( GPIO_NUM_4, LOW); //denergize relay module
      }
      if ( RemainingMoisture <= 20.0f )
      {
        gpio_set_level( GPIO_NUM_4, HIGH); //energize relay module
      }
    } else {
      gpio_set_level( GPIO_NUM_4, LOW); //denergize relay module
    }
    printCounts++;
    if ( printCounts == 100 )
    {
      log_i( "adcValue_b = %f remaining moisture %f%", adcValue_b, RemainingMoisture );
      printCounts = 0;
    }
    // publish to MQTT every 5000000uS
    if ( (esp_timer_get_time() - TimePastPublish) >= TimeToPublish )
    {
      //then publish
      xSemaphoreTake( sema_MQTT_KeepAlive, portMAX_DELAY ); // whiles MQTTlient.loop() is running no other mqtt operations should be in process
      MQTTclient.publish( topicRemainingMoisture_0, String(RemainingMoisture).c_str() );
      xSemaphoreGive( sema_MQTT_KeepAlive );
      TimePastPublish = esp_timer_get_time(); // get next publish time
    }
    xLastWakeTime = xTaskGetTickCount();
    vTaskDelayUntil( &xLastWakeTime, xFrequency );
  }
  vTaskDelete( NULL );
}// end fDoMoistureDetector()
////
/*
    Important to not set vTaskDelay to less then 10. Errors begin to develop with the MQTT and network connection.
    makes the initial wifi/mqtt connection and works to keeps those connections open.
*/
void MQTTkeepalive( void *pvParameters )
{
  sema_MQTT_KeepAlive   = xSemaphoreCreateBinary();
  xSemaphoreGive( sema_MQTT_KeepAlive ); // found keep alive can mess with a publish, stop keep alive during publish
  MQTTclient.setKeepAlive( 90 ); // setting keep alive to 90 seconds makes for a very reliable connection, must be set before the 1st connection is made.
  for (;;)
  {
    //check for a is-connected and if the WiFi 'thinks' its connected, found checking on both is more realible than just a single check
    if ( (wifiClient.connected()) && (WiFi.status() == WL_CONNECTED) )
    {
      xSemaphoreTake( sema_MQTT_KeepAlive, portMAX_DELAY ); // whiles MQTTlient.loop() is running no other mqtt operations should be in process
      MQTTclient.loop();
      xSemaphoreGive( sema_MQTT_KeepAlive );
    }
    else {
      log_i( "MQTT keep alive found MQTT status %s WiFi status %s", String(wifiClient.connected()), String(WiFi.status()) );
      if ( !(wifiClient.connected()) || !(WiFi.status() == WL_CONNECTED) )
      {
        connectToWiFi();
      }
      connectToMQTT();
    }
    vTaskDelay( 250 ); //task runs approx every 250 mS
  }
  vTaskDelete ( NULL );
}
////
void connectToMQTT()
{
  // create client ID from mac address
  byte mac[5];
  int count = 0;
  WiFi.macAddress(mac); // get mac address
  String clientID = String(mac[0]) + String(mac[4]);
  log_i( "connect to mqtt as client %s", clientID );
  while ( !MQTTclient.connected() )
  {
    MQTTclient.disconnect();
    MQTTclient.connect( clientID.c_str(), mqtt_username, mqtt_password );
    vTaskDelay( 250 );
    count++;
    if ( count == 5 )
    {
      ESP.restart();
    }
  }
  MQTTclient.setCallback( mqttCallback );
  MQTTclient.subscribe( topicOK );
}
//
void connectToWiFi()
{
  int TryCount = 0;
  while ( WiFi.status() != WL_CONNECTED )
  {
    TryCount++;
    WiFi.disconnect();
    WiFi.begin( SSID, PASSWORD );
    vTaskDelay( 4000 );
    if ( TryCount == 10 )
    {
      ESP.restart();
    }
  }
  WiFi.onEvent( WiFiEvent );
} // void connectToWiFi()
////
void loop() {}
