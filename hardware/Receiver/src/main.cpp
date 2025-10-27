/*********
 Rui Santos & Sara Santos - Random Nerd Tutorials
 Complete project details at https://RandomNerdTutorials.com/esp-now-many-to-one-esp32/
 Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files.
 The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
*********/

#include <Arduino.h>
#include <esp_now.h>
#include <WiFi.h>

uint8_t LED_PIN = LED_BUILTIN;

typedef struct struct_message
{
  int id;
  int awnser;
} struct_message;

struct_message myData;
struct_message board1;
struct_message board2;
struct_message board3;
struct_message boardsStruct[3] = {board1, board2, board3};

void OnDataRecv(const uint8_t *mac_addr, const uint8_t *incomingData, int len)
{
  // char macStr[18];
  // Serial.print("Packet received from: ");
  // snprintf(macStr, sizeof(macStr), "%02x:%02x:%02x:%02x:%02x:%02x",
  //          mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);
  // Serial.println(macStr);
  memcpy(&myData, incomingData, sizeof(myData));
  boardsStruct[myData.id - 1].awnser = myData.awnser;
  Serial.printf("%u,%d", myData.id, myData.awnser);
  Serial.println();
}

void setup()
{
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  WiFi.mode(WIFI_STA);

  delay(1500);

  if (esp_now_init() != ESP_OK)
  {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  delay(750);

  esp_now_register_recv_cb(esp_now_recv_cb_t(OnDataRecv));

  delay(750);

  Serial.println("Setup complete\n");
}

void loop()
{
}
