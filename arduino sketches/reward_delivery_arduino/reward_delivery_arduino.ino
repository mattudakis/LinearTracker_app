//--------------------------------Created by Matt Udakis -------------------------------//
//                                                                                      //
// Load this script onto an arduino connected to 2 solenoid valves for reward delivery  //
// The corresponding matlab script is called reward_delivery.m                          //
// matlab script will enable GUI for connection to arduino                              //
// delivery of reward and also manual open and closing of solenoid valves for set up    //
//                                                                                      //
//--------------------------------------------------------------------------------------//

int solenoid1       = 12;
int solenoid2       = 10;
int solenoid3       = 8;
int TTL_1           = 2;
int TTL_2           = 3;
int TTL_3           = 4;
int TTL_4           = 5;

// TTL_1 output to the inscopix DAQ to signify when opto genetics is delivered.


int openTime1 = 50;
int openTime2 = 50;

String serialReceived;
int State;

bool BreakStatus = false;
boolean receiverState;

void setup() {

  pinMode(solenoid1, OUTPUT);
  pinMode(solenoid2, OUTPUT);
  pinMode(solenoid3, OUTPUT);
  
  pinMode(TTL_1, OUTPUT);
  pinMode(TTL_2, OUTPUT);
  pinMode(TTL_3, OUTPUT);
  pinMode(TTL_4, OUTPUT);


  Serial.begin(9600); //open serial port and set rate to 9600 baud

}

void loop() {
  // put your main code here, to run repeatedly:
  while (Serial.available()) {

    //serialReceived = Serial.readStringUntil('\n');
    //    serialReceived = Serial.parseInt();
    State =  Serial.read();
    if (State == '1') {
      
        digitalWrite(solenoid1, HIGH);
        delay(openTime1);
        digitalWrite(solenoid1, LOW);
        break;
        }
        
    if (State == '2') {
        digitalWrite(solenoid2, HIGH);
        delay(openTime2);
        digitalWrite(solenoid2, LOW);
        break;
    }
        
    if (State == '3') {
        digitalWrite(solenoid1, HIGH);
        break;
      }

    if (State == '4') {
        digitalWrite(solenoid1, LOW);
        break;
      }

    if (State == '5') { 
        digitalWrite(solenoid2, HIGH);
        break;
    }

    if (State == '6') {    
        digitalWrite(solenoid2, LOW);
        break;
    }

    if (State == '7') { 
      digitalWrite(TTL_1, HIGH);
      break;
    }
      
    if (State == '8') { 
      digitalWrite(TTL_1, LOW);
      break;
    }

    if (State == '9') { 
      digitalWrite(solenoid3, HIGH);
      break;
    }
    
    if (State == '10') { 
      digitalWrite(solenoid3, LOW);
      break;
    } 
    }
  }

