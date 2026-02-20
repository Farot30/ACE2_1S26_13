#include <LiquidCrystal_I2C.h> 
#include <Servo.h>  
#include <MFRC522.h>
#include <SPI.h>


/*
  NOTA: Cambiaremos los pines de cada sensor y componente, esto por que ARDUINO UNO
        no tiene suficientes pines para todos los componentes, se usara ARDUINO MEGA.
        
        Código solo de prueba, la lógica esta bien, lo único que se cambiara es la declaración
        de los pines.
*/

#define INFRA1 2
#define INFRA2 3
//#define INFRA3 4
//#define INFRA4 5
//#define INFRA5 7
#define PIN_servoEntrada 5
#define PIN_servoSalida 6


int leds[2][3] = {
  {9, 10, 11},  //LED 0
  {6, 5, 3}     //LED 1
};

#define LED1 8
#define LED2 4
#define LED3 7
//#define LED4 11
//#define LED5 12

#define RST 9
#define SS 10

Servo servoEntrada;
Servo servoSalida;

LiquidCrystal_I2C lcd(0x27,16,2);

byte lectura[4];
byte tarjeta[4] = {0xB9, 0x1E, 0x19, 0xB4};
MFRC522 Mlector(SS, RST);

int ocupados = 0;

void setup() {
  lcd.init(); 
  lcd.backlight();
  lcd.clear();

  SPI.begin();
  Mlector.PCD_Init(); 

  pinMode(INFRA1, INPUT);
  pinMode(INFRA2, INPUT);
  //pinMode(INFRA3, INPUT);
  //pinMode(INFRA4, INPUT);
  //pinMode(INFRA5, INPUT);

  for(int i = 0; i < 2; i++) {
    for(int j = 0; j < 3; j++) {
      pinMode(leds[i][j], OUTPUT);
    }
  }

  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  /*pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);*/

  servoEntrada.attach(PIN_servoEntrada);
  servoSalida.attach(PIN_servoSalida);
  servoEntrada.write(0);
  servoSalida.write(0);

}

void loop() {
  ocupados = 0;

  if (digitalRead(INFRA1) == LOW) {
    setColor(0, 0, 255, 0);
    ocupados++;
  } else setColor(0, 255, 0, 0);

  if (digitalRead(INFRA2) == LOW) {
    setColor(1, 0, 255, 0);
    ocupados++;
  } else setColor(1, 255, 0, 0);

  /*if (digitalRead(INFRA3) == LOW) {
    digitalWrite(LED3, HIGH);
    ocupados++;
  } else digitalWrite(LED3, LOW);

  if (digitalRead(INFRA4) == LOW) {
    digitalWrite(LED4, HIGH);
    ocupados++;
  } else digitalWrite(LED4, LOW);

  if (digitalRead(INFRA5) == LOW) {
    digitalWrite(LED5, HIGH);
    ocupados++;
  } else digitalWrite(LED5, LOW);*/
  
  int libres = 2 - ocupados;

  static int ultimo = -1;

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
        digitalWrite(LED3, HIGH);
        delay(5000);
        servoEntrada.write(0);
        digitalWrite(LED3, LOW);
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