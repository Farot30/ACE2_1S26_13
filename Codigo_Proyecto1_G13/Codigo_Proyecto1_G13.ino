#include <LiquidCrystal_I2C.h>
#include <Servo.h>  
#include <MFRC522.h>
#include <SPI.h>

//MQ2 
#define MQ2 19

//BUZZER
#define BUZZER 22

//RELÉ
#define VENTILADOR 23

//Botón de salida
#define BTN_Salida 18

int ocupados = 0;
volatile bool emergenciaActiva = false;
int ultimo = -1;

// ---- CONTROL DE ESTADOS ----
enum Estado {
  NORMAL,
  MOSTRANDO_MENSAJE,
  ABRIENDO_SERVO,
  ESPERANDO_ABIERTO,
  CERRANDO_SERVO
};

Estado estadoActual = NORMAL;

// ---- CONTROL TIEMPOS ----
unsigned long tiempoEstado = 0;
unsigned long tiempoServo = 0;

// ---- CONTROL SERVO ----
int anguloServo = 0;

unsigned long lastBeep = 0;

//Infrarrojos
#define INFRA1 24 
#define INFRA2 25 
#define INFRA3 26 
#define INFRA4 27
#define INFRA5 28

//Servomotores
#define PIN_servoEntrada 29
#define PIN_servoSalida 30

//Leds {R, G}
int leds[5][2] = {
  {31, 32},   //LED 0
  {33, 34},   //LED 1
  {35, 36},   //LED 2
  {37, 38},   //LED 3
  {39, 40}    //LED 4
};

#define RST 48
#define SS 49

Servo servoEntrada;
Servo servoSalida;

LiquidCrystal_I2C lcd(0x27,16,2);

byte lectura[4];
byte tarjeta[4] = {0xB9, 0x1E, 0x19, 0xB4};
MFRC522 Mlector(SS, RST);

void setup() {

  Serial.begin(9600);

  pinMode(53, OUTPUT);
  digitalWrite(53, HIGH);

  //LCD 
  lcd.init(); 
  lcd.backlight();
  lcd.clear();

  //SPI + RFID
  SPI.begin();
  Mlector.PCD_Init(); 

  //LEDs RGB (los 5)
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 2; j++) {
      pinMode(leds[i][j], OUTPUT);
    }
  }

  //Servos
  servoEntrada.attach(PIN_servoEntrada);
  servoSalida.attach(PIN_servoSalida);
  servoEntrada.write(0);
  servoSalida.write(0);

  //Sensores
  pinMode(MQ2, INPUT);
  attachInterrupt(digitalPinToInterrupt(MQ2), emergenciaISR, FALLING);

  //Bóton de salida (Talanquera) 
  pinMode(BTN_Salida, INPUT_PULLUP);

  pinMode(INFRA1, INPUT_PULLUP);
  pinMode(INFRA2, INPUT_PULLUP);
  pinMode(INFRA3, INPUT_PULLUP);
  pinMode(INFRA4, INPUT_PULLUP);
  pinMode(INFRA5, INPUT_PULLUP);

  //Actuadores
  pinMode(BUZZER, OUTPUT);
  pinMode(VENTILADOR, OUTPUT);

  digitalWrite(BUZZER, LOW);
  digitalWrite(VENTILADOR, LOW);
}

void loop() {

  static unsigned long tiempoSerial = 0;
  if(millis() - tiempoSerial >= 500){
    tiempoSerial = millis();

    Serial.print(" | MQ2 pin19: ");
    Serial.print(digitalRead(MQ2));
    if (digitalRead(MQ2) == HIGH) {
      Serial.print(" → GAS DETECTADO (debería activar emergencia)");
    } else {
      Serial.print(" → sin gas");
    }
    Serial.print(" | EmergActiva: ");
    Serial.println(emergenciaActiva ? "ACTIVA" : "no");

    Serial.print("S1: ");
    Serial.print(digitalRead(INFRA1));
    Serial.print(" S2: ");
    Serial.print(digitalRead(INFRA2));
    Serial.print(" S3: ");
    Serial.print(digitalRead(INFRA3));
    Serial.print(" S4: ");
    Serial.print(digitalRead(INFRA4));
    Serial.print(" S5: ");
    Serial.println(digitalRead(INFRA5));
  }

  static unsigned long tiempoDebug = 0;
  if (millis() - tiempoDebug >= 1000) {  //Cada segundo
    tiempoDebug = millis();
    Serial.print("Estado actual: ");
    switch (estadoActual) {
      case NORMAL: Serial.println("NORMAL"); break;
      case MOSTRANDO_MENSAJE: Serial.println("MOSTRANDO_MENSAJE"); break;
      // Agrega los demás
    }
  }

  ocupados = 0;

ocupados = 0;

// Solo actualiza LEDs por ocupación si NO hay emergencia
if (!emergenciaActiva) {
  if (digitalRead(INFRA1) == LOW) {
    setColor(0, HIGH, LOW);
    ocupados++;
  } else setColor(0, LOW, HIGH);

  if (digitalRead(INFRA2) == LOW) {
    setColor(1, HIGH, LOW);
    ocupados++;
  } else setColor(1, LOW, HIGH);

  if (digitalRead(INFRA3) == LOW) {
    setColor(2, HIGH, LOW);
    ocupados++;
  } else setColor(2, LOW, HIGH);

  if (digitalRead(INFRA4) == LOW) {
    setColor(3, HIGH, LOW);
    ocupados++;
  } else setColor(3, LOW, HIGH);

  if (digitalRead(INFRA5) == LOW) {
    setColor(4, HIGH, LOW);
    ocupados++;
  } else setColor(4, LOW, HIGH);
}
  
  int libres = 5 - ocupados;

  if(estadoActual == NORMAL && libres != ultimo){

    lcd.clear();

    if(libres == 0){

      lcd.setCursor(3,0);
      lcd.print("CUPO LLENO");

      lcd.setCursor(0,1);
      lcd.print("ESPACIOS: 0   ");

    }else{

      lcd.setCursor(0,0);
      lcd.print("Libres: ");
      lcd.print(libres);
      lcd.print("   ");

      lcd.setCursor(0,1);
      lcd.print("Disponible  ");
    }

    ultimo = libres;
  }

  if(emergenciaActiva){
      activarEmergencia();
    }

  btnSalida();

  // ---- MAQUINA DE ESTADOS ----
  switch(estadoActual){

    case MOSTRANDO_MENSAJE:
      if(millis() - tiempoEstado >= 1000){   // mostrar 1 segundo
          estadoActual = ABRIENDO_SERVO;
          tiempoServo = millis();
          anguloServo = 0;
      }
    break;


    case ABRIENDO_SERVO:
      if(millis() - tiempoServo >= 10){
          tiempoServo = millis();
          servoEntrada.write(anguloServo);
          anguloServo++;

          if(anguloServo >= 90){
              estadoActual = ESPERANDO_ABIERTO;
              tiempoEstado = millis();
          }
      }
    break;


    case ESPERANDO_ABIERTO:
      if(millis() - tiempoServo >= 10){
          tiempoServo = millis();
          servoEntrada.write(anguloServo);
          anguloServo--;

          if(anguloServo <= 0){
              estadoActual = NORMAL;
              ultimo = -1;
              servoEntrada.write(0);  //asegura posición final
          }
      }
    break;


    case CERRANDO_SERVO:
      if(millis() - tiempoServo >= 5){
          tiempoServo = millis();
          servoEntrada.write(anguloServo);
          anguloServo--;

          if(anguloServo <= 0){
              estadoActual = NORMAL;
              ultimo = -1;  // forzar actualización LCD
          }
      }
    break;


    case NORMAL:
    break;
  }

  if(estadoActual != NORMAL){
      return;
  }

  if(Mlector.PICC_IsNewCardPresent() && Mlector.PICC_ReadCardSerial()){
    for(byte i=0; i<Mlector.uid.size; i++){
      lectura[i] = Mlector.uid.uidByte[i];
    }

    if(comprobacion(lectura, tarjeta)){
      if(libres > 0){

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Acceso concedido");
        lcd.setCursor(3, 1);
        lcd.print("Bienvenido");

        estadoActual = MOSTRANDO_MENSAJE;
        tiempoEstado = millis();

      } else{
          lcd.clear();
          lcd.setCursor(0,0);
          lcd.print("Parqueo lleno");
          delay(1500);
          lcd.clear();
          ultimo = -1;
      }

    } else{
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Tarjeta invalida");
        delay(1500);

        ultimo = -1;
    }

    Mlector.PICC_HaltA();  //usamos esta función para finalizar la lectura del RFID
    Mlector.PCD_StopCrypto1();
  }
}


void setColor(int ledNumero, bool rojo, bool verde){
    digitalWrite(leds[ledNumero][0], rojo);
    digitalWrite(leds[ledNumero][1], verde);
}


boolean comprobacion(byte lectura[], byte tarjeta[]){
  for(byte x=0; x<Mlector.uid.size; x++){
    if(lectura[x] != tarjeta[x]){
      return false;
    }
  }
  return true;
}

void activarEmergencia() {

  // Variables estáticas para recordar estado
  static bool emergenciaEnCurso = false;
  static unsigned long ultimoParpadeo = 0;  // si quieres mover lastBlink aquí

  // Si recién se activó la flag (primera vez)
  if (emergenciaActiva && !emergenciaEnCurso) {
    digitalWrite(VENTILADOR, HIGH);
    servoEntrada.write(90);
    servoSalida.write(90);

    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("!!! EMERGENCIA !!!");
    lcd.setCursor(2,1);
    lcd.print("EVACUAR AREA");

    emergenciaEnCurso = true;
    lastBeep = millis();  // resetear para buzzer
    ultimoParpadeo = millis();  // si usas otro nombre para blink
  }

  // Si estamos en emergencia (cada loop)
  if (emergenciaActiva) {

    static int tonoActual = 500;          // Hz inicial (bajo)
    static bool subiendo = true;

    if (millis() - lastBeep >= 8) {       // cada 8 ms para que suene fluido
      lastBeep = millis();

      tone(BUZZER, tonoActual);           // genera el tono

      if (subiendo) {
        tonoActual += 6;                  // sube rápido
        if (tonoActual >= 1400) subiendo = false;
      } else {
        tonoActual -= 6;                  // baja rápido
        if (tonoActual <= 500) subiendo = true;
      }
    }
    

    // LEDs parpadeo (usa tu función o mueve la lógica aquí)
    if (millis() - ultimoParpadeo > 300) {
      static bool estadoLED = false;
      estadoLED = !estadoLED;
      for(int i = 0; i < 5; i++) {
        if (estadoLED) {
          setColor(i, HIGH, LOW);   // Rojo
        } else {
          setColor(i, LOW, LOW);    // Apagado
        }
      }
      ultimoParpadeo = millis();
    }
  }

  // Condición de salida: cuando ya no hay humo
  if (emergenciaActiva && digitalRead(MQ2) == HIGH) {
    emergenciaActiva = false;
    emergenciaEnCurso = false;

    noTone(BUZZER);
    digitalWrite(VENTILADOR, LOW);
    servoEntrada.write(0);
    servoSalida.write(0);
    lcd.clear();
    ultimo = -1;  // refresh pantalla normal
  }
}

void emergenciaISR() {
  emergenciaActiva = true;
}

void parpadearLEDsEmergencia() {
  static unsigned long lastBlink = 0;
  static bool estadoLED = false;
  
  if (millis() - lastBlink > 300) {
    estadoLED = !estadoLED;
    
    for(int i = 0; i < 5; i++) {
      if (estadoLED) {
        setColor(i, HIGH, LOW);   //Rojo
      } else {
        setColor(i, LOW, LOW);    //Apagado
      }
    }

    lastBlink = millis();
  }
}

void btnSalida(){
  if(digitalRead(BTN_Salida) == LOW){
    for(int i=0;i<=90;i++){
      servoSalida.write(i);
      delay(5);
    }

    delay(3000);

    for(int i=90;i>=0;i++){
      servoSalida.write(i);
      delay(5);
    }
  }
}