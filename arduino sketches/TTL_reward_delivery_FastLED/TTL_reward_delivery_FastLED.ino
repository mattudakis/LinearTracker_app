/*
Simple Arduino sketch to turn on two LEDs with serial input. 
Used for LinearTrack_er app to prototype

Used addressable LEDs as this easily allows more LEDs to be added to the circuit for additional 
logic testing.

requires the FastLED library to run. could easily switch out the FastLED for simple LEDS
*/

#include <FastLED.h>
#define LED_PIN 12
#define NUM_LEDS 2

int openTime1 = 250;
int incomingByte;


CRGB leds[NUM_LEDS];

// the setup function runs once when you press reset or power the board
void setup() {
  FastLED.addLeds<WS2812, LED_PIN, RGB>(leds, NUM_LEDS);
  FastLED.clear();
  leds[0] = CRGB(0, 0, 0);
  leds[1] = CRGB(0, 0, 0);
  FastLED.show();
  Serial.begin(9600); //open serial port and set rate to 9600 baud

}

void loop() {
  // put your main code here, to run repeatedly:
   while (Serial.available()) {
    
   
      incomingByte = Serial.read();
      //    serialReceived = Serial.parseInt();
      if (incomingByte == '1') {
      
          leds[0] = CRGB(255, 0, 0);
          FastLED.show();
          delay(openTime1);
          FastLED.clear();
          leds[0] = CRGB(0, 0, 0);
          FastLED.show();
          break;
          }
          
      if (incomingByte == '2') {
          leds[1] = CRGB(0, 255, 0);
          FastLED.show();
          delay(openTime1);
          FastLED.clear();
          leds[1] = CRGB(0, 0, 0);
          FastLED.show();
          break;
          }
          
      if (incomingByte == '3') {
          leds[0] = CRGB(255, 0, 0);
          FastLED.show();
          break;
          }
      if (incomingByte == '4') {
          leds[0] = CRGB(0, 0, 0);
          FastLED.show();
          break;
          }
      if (incomingByte == '5') {
          leds[1] = CRGB(0, 255, 0);
          FastLED.show();
          break;
          }    
     if (incomingByte == '6') {
          leds[1] = CRGB(0, 0, 0);
          FastLED.show();
          break;
          }
     }
     
  }
