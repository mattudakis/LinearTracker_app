/*
Simple Arduino sketch to turn on two LEDs with serial input. 
Used for LinearTrack_er app to prototype
connect an LED to digital pin 12 and 13
*/

int led_pin_1       = 10;
int led_pin_2       = 13;

int openTime1 = 50;
int incomingByte;

// the setup function runs once when you press reset or power the board
void setup() {
  pinMode(led_pin_1 , OUTPUT);
  pinMode(led_pin_2 , OUTPUT);
  
  Serial.begin(9600); //open serial port and set rate to 9600 baud

}

void loop() {
  // put your main code here, to run repeatedly:
   while (Serial.available()) {
    
   
      incomingByte = Serial.read();
      //    serialReceived = Serial.parseInt();
      if (incomingByte == '1') {
      
          digitalWrite(led_pin_1, HIGH);
          delay(openTime1);
          digitalWrite(led_pin_1, LOW);
          break;
          }
          
      if (incomingByte == '2') {
          digitalWrite(led_pin_2, HIGH);
          delay(openTime1);
          digitalWrite(led_pin_2, LOW);
          break;
          }
          
      if (incomingByte == '3') {
          digitalWrite(led_pin_1, HIGH);
          break;
          }
      if (incomingByte == '4') {
          digitalWrite(led_pin_1, LOW);
          break;
          }
      if (incomingByte == '5') {
          digitalWrite(led_pin_2, HIGH);
          break;
          }    
     if (incomingByte == '6') {
          digitalWrite(led_pin_2, LOW);
          break;
          }
     }
     
  }
