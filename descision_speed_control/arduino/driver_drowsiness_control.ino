// =====================================
// AI DRIVER DROWSINESS SYSTEM
// =====================================

// RIGHT MOTOR
const int ENA = 5;
const int IN1 = 7;
const int IN2 = 8;

// LEFT MOTOR
const int ENB = 6;
const int IN3 = 9;
const int IN4 = 10;

// LED PINS
const int GREEN_LED = A0;
const int YELLOW_LED = A1;
const int RED_LED = A2;

// BUZZER
const int BUZZER = A3;

// MOTOR SPEEDS
const int NORMAL_SPEED = 255;
const int MILD_SPEED = 60;


// =====================================
// MOTOR FUNCTIONS
// =====================================

void motorNormal() {
  analogWrite(ENA, NORMAL_SPEED);
  analogWrite(ENB, NORMAL_SPEED);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void motorMild() {
  analogWrite(ENA, MILD_SPEED);
  analogWrite(ENB, MILD_SPEED);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void motorStop() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}


// =====================================
// SETUP
// =====================================

void setup() {

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  pinMode(GREEN_LED, OUTPUT);
  pinMode(YELLOW_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);

  pinMode(BUZZER, OUTPUT);

  Serial.begin(9600);

  motorNormal();

  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(YELLOW_LED, LOW);
  digitalWrite(RED_LED, LOW);
  digitalWrite(BUZZER, LOW);
}


// =====================================
// MAIN LOOP
// =====================================

void loop() {

  if (Serial.available()) {

    char command = Serial.read();

    // NORMAL / AWAKE
    if (command == 'N') {

      motorNormal();

      digitalWrite(GREEN_LED, HIGH);
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(RED_LED, LOW);
      digitalWrite(BUZZER, LOW);
    }

    // MILD DROWSINESS
    else if (command == 'M') {

      motorMild();

      digitalWrite(GREEN_LED, LOW);
      digitalWrite(YELLOW_LED, HIGH);
      digitalWrite(RED_LED, LOW);
      digitalWrite(BUZZER, LOW);
    }

    // SEVERE DROWSINESS
    else if (command == 'S') {

      motorStop();

      digitalWrite(GREEN_LED, LOW);
      digitalWrite(YELLOW_LED, LOW);
      digitalWrite(RED_LED, HIGH);
      digitalWrite(BUZZER, HIGH);
    }
  }
}
