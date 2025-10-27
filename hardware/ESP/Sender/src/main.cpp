/*********
  Rui Santos & Sara Santos - Random Nerd Tutorials
  Complete project details at https://RandomNerdTutorials.com/esp-now-many-to-one-esp32/
  Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.
  The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*********/

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

//#define CHILL
//#define DEBUG
#define ID_REMOTE 0

#define LED_PIN LED_BUILTIN
#define LED_1 18
#define LED_2 19

#define VOLT_PIN 0

int buttons[5] = {1, 17, 23, 16, 20};
bool pressed[5] = {false, false, false, false, false};

uint8_t broadcastAddress[] = {0xB4, 0x3A, 0x45, 0x8A, 0x4C, 0x18};

typedef struct struct_message
{
  int id;
  int awnser;
} struct_message;

struct_message myData;
esp_now_peer_info_t peerInfo;

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status);
void sendData();
void send_on_button_press(int button_nr);
void checkBattery();

void setup()
{
  #ifdef CHILL
  return;
  #endif

  myData.id = ID_REMOTE;

  #ifdef DEBUG
  Serial.begin(115200);
  #endif

  WiFi.mode(WIFI_STA);

  pinMode(buttons[0], INPUT_PULLUP);
  pinMode(buttons[1], INPUT_PULLUP);
  pinMode(buttons[2], INPUT_PULLUP);
  pinMode(buttons[3], INPUT_PULLUP);
  pinMode(buttons[4], INPUT_PULLUP);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  pinMode(LED_1, OUTPUT);
  pinMode(LED_2, OUTPUT);

  pinMode(VOLT_PIN, INPUT);

  delay(1500);

  #ifdef DEBUG
  if (esp_now_init() != ESP_OK)
  {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  #else
  esp_now_init();
  #endif

  delay(750);

  #ifdef DEBUG
  esp_now_register_send_cb(OnDataSent);
  delay(750);
  #endif

  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;

  #ifdef DEBUG
  if (esp_now_add_peer(&peerInfo) != ESP_OK)
  {
    Serial.println("Failed to add peer");
    return;
  }

  Serial.println("Setup complete");
  #else
  esp_now_add_peer(&peerInfo);
  #endif

  digitalWrite(LED_1, HIGH);
}

void loop()
{
  #ifdef CHILL
  delay(100000);
  return;
  #endif

  for (int i = 0; i < 5; i++)
  {
    send_on_button_press(i);
  }

  #ifdef DEBUG
  checkBattery();
  #endif

  delay(24);
}

void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status)
{
  #ifdef DEBUG
  Serial.print("Last Packet Send Status:\t");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success\r\n" : "Delivery Fail\r\n");
  #else
  return;
  #endif
}

void sendData()
{
  #ifdef DEBUG
  if (esp_now_send(broadcastAddress, (uint8_t *)&myData, sizeof(myData)) != ESP_OK)
  {
    Serial.println("Error sending the data");
  }
  #else
  esp_now_send(broadcastAddress, (uint8_t *)&myData, sizeof(myData));
  #endif
}

void send_on_button_press(int button_nr)
{
  if (!digitalRead(buttons[button_nr]))
  {
    if (pressed[button_nr] == false)
    {
      pressed[button_nr] = true;
      myData.awnser = button_nr;
      sendData();

      Serial.print("Button ");
      Serial.println(button_nr);
    }
  }
  else
  {
    pressed[button_nr] = false;
  }
}

unsigned long battery_check_time = 0;
void checkBattery()
{
  float Vbattf = 0;
  
  // Check battery voltage every minute
  if (millis() - battery_check_time > 1000 * 3)
  {
    uint32_t Vbatt = 0;
    for (int i = 0; i < 16; i++)
    {
      Vbatt += analogReadMilliVolts(VOLT_PIN); // Read and accumulate ADC voltage
    }
    float Vbattf = 2 * Vbatt / 16 / 1000.0; // Adjust for 1:2 divider and convert to volts
    battery_check_time = millis();

    if (Vbattf > 3.9f)
    {
      digitalWrite(LED_2, HIGH);
    } else
    {
      digitalWrite(LED_2, LOW);
    }

    #ifdef DEBUG
    Serial.println(Vbattf, 3); // Output voltage to 3 decimal places
    myData.awnser = (Vbattf * 100000.0);
    sendData();
    #endif
  }
}