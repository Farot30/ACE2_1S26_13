#include <LiquidCrystal_I2C.h> 
#include <Servo.h>  
#include <MFRC522.h>
#include <SPI.h>

//MQ2 
#define MQ2 A0

//BUZZER
#define BUZZER 22

//RELÉ
#define VENTILADOR 23

//Umbrales para el MQ2
#define UMBRAL_ADVERTENCIA 300
#define UMBRAL_PELIGRO 500
#define UMBRAL_CRITICO 700

int ocupados = 0;
bool emergenciaActiva = false;
int ultimo = -1;
int estadoGasActual = -1;
// -1 = sin estado inicial
// 0 = normal
// 1 = advertencia
// 2 = peligro
// 3 = critico

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

//Leds RGB {R, G, B}
int leds[5][3] = {
  {2, 3, 4},      //LED 0
  {5, 6, 7},      //LED 1
  {8, 9, 10},     //LED 2
  {11, 12, 13},   //LED 3
  {44, 45, 46}    //LED 4
};

#define RST 48
#define SS 53

Servo servoEntrada;
Servo servoSalida;

LiquidCrystal_I2C lcd(0x27,16,2);

byte lectura[4];
byte tarjeta[4] = {0xB9, 0x1E, 0x19, 0xB4};
MFRC522 Mlector(SS, RST);

void setup() {
  //LCD 
  lcd.init(); 
  lcd.backlight();
  lcd.clear();

  //SPI + RFID
  SPI.begin();
  Mlector.PCD_Init(); 

  //LEDs RGB (los 5)
  for(int i = 0; i < 5; i++) {
    for(int j = 0; j < 3; j++) {
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

  pinMode(INFRA1, INPUT);
  pinMode(INFRA2, INPUT);
  pinMode(INFRA3, INPUT);
  pinMode(INFRA4, INPUT);
  pinMode(INFRA5, INPUT);

  //Actuadores
  pinMode(BUZZER, OUTPUT);
  pinMode(VENTILADOR, OUTPUT);

  digitalWrite(BUZZER, LOW);
  digitalWrite(VENTILADOR, LOW);
}

void loop() {
  ocupados = 0;

  verificarGas();

  if (emergenciaActiva) {
    return;   
  }

  if (digitalRead(INFRA1) == LOW) {
    setColor(0, 255, 0, 0);
    ocupados++;
  } else setColor(0, 0, 255, 0);

  if (digitalRead(INFRA2) == LOW) {
    setColor(1, 255, 0, 0);
    ocupados++;
  } else setColor(1, 0, 255, 0);

  if (digitalRead(INFRA3) == LOW) {
    setColor(2, 255, 0, 0);
    ocupados++;
  } else setColor(2, 0, 255, 0);

  if (digitalRead(INFRA4) == LOW) {
    setColor(3, 255, 0, 0);
    ocupados++;
  } else setColor(3, 0, 255, 0);

  if (digitalRead(INFRA5) == LOW) {
    setColor(4, 255, 0, 0);
    ocupados++;
  } else setColor(4, 0, 255, 0);
  
  int libres = 5 - ocupados;

  if(libres != ultimo){

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
        delay(500);

        servoEntrada.write(90);
        //digitalWrite(LED3, HIGH);  se elimina luego, solo esta de prueba
        delay(5000);
        servoEntrada.write(0);
        //digitalWrite(LED3, LOW);  se elimina luego, solo esta de prueba
        lcd.clear();

        ultimo = -1;
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
  delay(200);

}


void setColor(int ledNumero, int r, int g, int b){
    analogWrite(leds[ledNumero][0], r);
    analogWrite(leds[ledNumero][1], g);
    analogWrite(leds[ledNumero][2], b);
}


boolean comprobacion(byte lectura[], byte tarjeta[]){
  for(byte x=0; x<Mlector.uid.size; x++){
    if(lectura[x] != tarjeta[x]){
      return false;
    }
  }
  return true;
}


void verificarGas() {

  int nivelGas = analogRead(MQ2);
  int nuevoEstado;

  //Determinar estado según nivel
  if (nivelGas < UMBRAL_ADVERTENCIA) {
    nuevoEstado = 0;
  }
  else if (nivelGas < UMBRAL_PELIGRO) {
    nuevoEstado = 1;
  }
  else if (nivelGas < UMBRAL_CRITICO) {
    nuevoEstado = 2;
  }
  else {
    nuevoEstado = 3;
  }

  //SOLO actuar si el estado cambió
  if (nuevoEstado != estadoGasActual) {

    estadoGasActual = nuevoEstado;
    lcd.clear();

    switch (estadoGasActual) {

      case 0: //NORMAL
        emergenciaActiva = false;
        digitalWrite(BUZZER, LOW);
        digitalWrite(VENTILADOR, LOW);
        ultimo = -1; //Forzar actualización normal del parqueo
        break;

      case 1: //ADVERTENCIA
        digitalWrite(VENTILADOR, HIGH);
        lcd.setCursor(0, 0);
        lcd.print("ADVERTENCIA GAS");
        lcd.setCursor(0, 1);
        lcd.print("Nivel: ");
        break;

      case 2: //PELIGRO
        emergenciaActiva = true;
        digitalWrite(VENTILADOR, HIGH);
        servoEntrada.write(90);
        servoSalida.write(90);

        lcd.setCursor(0, 0);
        lcd.print("!! PELIGRO !!");
        lcd.setCursor(0, 1);
        lcd.print("EVACUAR AREA");
        break;

      case 3: //CRITICO
        emergenciaActiva = true;
        digitalWrite(VENTILADOR, HIGH);
        servoEntrada.write(90);
        servoSalida.write(90);

        lcd.setCursor(0, 0);
        lcd.print("!!!CRITICO!!!");
        lcd.setCursor(0, 1);
        lcd.print("Gas: ");
        break;
    }
  }

  //ACCIONES CONTINUAS (sin limpiar LCD)

  if (estadoGasActual == 1) {
    //Mostrar nivel sin borrar todo
    lcd.setCursor(7, 1);
    lcd.print("    "); //borrar número anterior
    lcd.setCursor(7, 1);
    lcd.print(nivelGas);

    //Buzzer lento
    if (millis() - lastBeep > 1000) {
      digitalWrite(BUZZER, !digitalRead(BUZZER));
      lastBeep = millis();
    }
  }

  else if (estadoGasActual == 2) {
    //Buzzer rápido
    if (millis() - lastBeep > 500) {
      digitalWrite(BUZZER, !digitalRead(BUZZER));
      lastBeep = millis();
    }

    parpadearLEDsEmergencia();
  }

  else if (estadoGasActual == 3) {
    //Buzzer muy rápido
    if (millis() - lastBeep > 200) {
      digitalWrite(BUZZER, !digitalRead(BUZZER));
      lastBeep = millis();
    }

    parpadearLEDsEmergencia();
  }
}

void parpadearLEDsEmergencia() {
  static unsigned long lastBlink = 0;
  static bool estadoLED = false;
  
  if (millis() - lastBlink > 300) {
    estadoLED = !estadoLED;
    
    //Todos los LEDs RGB en rojo parpadeante
    for(int i = 0; i < 5; i++) {
      if (estadoLED) {
        setColor(i, 255, 0, 0);  // Rojo
      } else {
        setColor(i, 0, 0, 0);    // Apagado
      }
    }
    
    //LED3 también parpadea (solo de prueba)
    //digitalWrite(LED3, estadoLED);
    
    lastBlink = millis();
  }
}