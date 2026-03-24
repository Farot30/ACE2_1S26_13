//Código reutiliizado del proyecto 1
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
bool emergenciaRemota = false;
bool emergenciaEnCurso = false;
int ultimo = -1;

int tonoActual = 500;
bool subiendo = true;

//CONTROL DE ESTADOS
enum Estado {
  NORMAL,
  ESPERANDO_RESPUESTA,
  MOSTRANDO_DENEGADO,
  MOSTRANDO_TIMEOUT,
  MOSTRANDO_MENSAJE,
  ABRIENDO_SERVO,
  ESPERANDO_ABIERTO,
  CERRANDO_SERVO
};

Estado estadoActual = NORMAL;

enum EstadoSalida {
  SALIDA_NORMAL,
  SALIDA_ABRIENDO,
  SALIDA_ESPERANDO,
  SALIDA_CERRANDO
};

EstadoSalida estadoSalida = SALIDA_NORMAL;
unsigned long tiempoSalida = 0;
int anguloSalida = 0;

//CONTROL TIEMPOS
unsigned long tiempoEstado = 0;
unsigned long tiempoServo = 0;

//CONTROL SERVO
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

#define RST 9
#define SS 10

Servo servoEntrada;
Servo servoSalida;

LiquidCrystal_I2C lcd(0x27,16,2);

String uidActual = "";
MFRC522 Mlector(SS, RST);

void setup() {

  Serial.begin(115200);

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
  servoSalida.write(90);

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

  //Leer comandos de la Raspberry
  leerSerial();

  ocupados = 0;

//Solo actualiza LEDs por ocupación si NO hay emergencia
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
    setColor(3, LOW, HIGH);
    ocupados++;
  } else setColor(3, HIGH, LOW);

  if (digitalRead(INFRA5) == LOW) {
    setColor(4, LOW, HIGH);
    ocupados++;
  } else setColor(4, HIGH, LOW);
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
  
  //Envío periódico del estado de sensores
  static unsigned long tiempoPublish = 0;
  if (millis() - tiempoPublish >= 1000) {
    tiempoPublish = millis();
    
    String payload = "\"spaces\":[";
    payload += String(!digitalRead(INFRA1)) + ",";
    payload += String(!digitalRead(INFRA2)) + ",";
    payload += String(!digitalRead(INFRA3)) + ",";
    payload += String(!digitalRead(INFRA4)) + ",";
    payload += String(!digitalRead(INFRA5));
    payload += "],\"gas\":" + String(digitalRead(MQ2));
    payload += ",\"fan\":" + String(digitalRead(VENTILADOR));
    payload += ",\"emergency\":" + String(emergenciaActiva ? 1 : 0);
    
    enviarSerial("sensor", payload);
  }

  //MAQUINA DE ESTADOS
  switch(estadoActual){

    case ESPERANDO_RESPUESTA:
      if (millis() - tiempoEstado >= 3000) {  // 3 segundos timeout
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Sin respuesta");
        
        estadoActual = MOSTRANDO_TIMEOUT;
        tiempoEstado = millis();
        
        enviarSerial("event", "\"action\":\"timeout\"");
      }
      break;

    case MOSTRANDO_DENEGADO:
      if(millis() - tiempoEstado >= 1500){
          estadoActual = NORMAL;
          ultimo = -1;
      }
      break;

    case MOSTRANDO_TIMEOUT:
      if(millis() - tiempoEstado >= 1000){
          estadoActual = NORMAL;
          ultimo = -1;
      }
      break;

    case MOSTRANDO_MENSAJE:
      if(millis() - tiempoEstado >= 1000){   //mostrar 1 segundo
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
      if(millis() - tiempoServo >= 70){
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
              ultimo = -1;  //forzar actualización LCD
          }
      }
    break;


    case NORMAL:
    break;
  }

  if(estadoActual != NORMAL){
      return;
  }

  if (!emergenciaActiva && estadoActual == NORMAL) {
    if(Mlector.PICC_IsNewCardPresent() && Mlector.PICC_ReadCardSerial()){
      // Convertir UID a formato hexadecimal
      uidActual = "";
      for(byte i = 0; i < Mlector.uid.size; i++){
        if(Mlector.uid.uidByte[i] < 10) uidActual += "0";
        uidActual += String(Mlector.uid.uidByte[i], HEX);
      }
      uidActual.toUpperCase();
      
      // Mostrar mensaje de lectura
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Leyendo tarjeta.");
      lcd.setCursor(0, 1);
      lcd.print(uidActual);
      
      // Enviar UID a Raspberry por Serial
      enviarSerial("rfid", "\"uid\":\"" + uidActual + "\"");
      
      // Cambiar a estado de espera
      estadoActual = ESPERANDO_RESPUESTA;
      tiempoEstado = millis();

      Mlector.PICC_HaltA();  // Finalizar lectura del RFID
      Mlector.PCD_StopCrypto1();
    }
  }
}


void setColor(int ledNumero, bool rojo, bool verde){
    digitalWrite(leds[ledNumero][0], rojo);
    digitalWrite(leds[ledNumero][1], verde);
}

void enviarSerial(String tipo, String payload) {
  String mensaje = "{\"type\":\"" + tipo + "\"," + payload + "}";
  Serial.println(mensaje);
}

void leerSerial() {
  static String buffer = "";

  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      procesarComando(buffer);
      buffer = "";
    } else if (c != '\r') {
      buffer += c;
    }
  }
}

void procesarComando(String msg) {
  // Comando de acceso RFID
  if (msg.indexOf("\"cmd\":\"access\"") >= 0) {
    bool granted = msg.indexOf("\"granted\":true") >= 0;
    
    if (granted && estadoActual == ESPERANDO_RESPUESTA) {
      // Acceso concedido
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Acceso concedido");
      lcd.setCursor(4, 1);
      lcd.print("Grupo 13");
      
      estadoActual = MOSTRANDO_MENSAJE;
      tiempoEstado = millis();
      
      enviarSerial("event", "\"action\":\"entry_approved\"");
    } else if (estadoActual == ESPERANDO_RESPUESTA) {
      // Acceso denegado
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Acceso denegado");
      
      estadoActual = MOSTRANDO_DENEGADO;
      tiempoEstado = millis();
      
      enviarSerial("event", "\"action\":\"entry_denied\"");
    }
  }
  
  // Comando de ventilador
  if (msg.indexOf("\"cmd\":\"fan\"") >= 0) {
    bool state = msg.indexOf("\"state\":true") >= 0;
    digitalWrite(VENTILADOR, state ? HIGH : LOW);
  }
  
  // Comando de emergencia
  if (msg.indexOf("\"cmd\":\"emergency\"") >= 0) {
    bool state = msg.indexOf("\"state\":true") >= 0;
    emergenciaActiva = state;
    emergenciaRemota = state;
    
    // Si se apaga la emergencia desde el dashboard
    if (!state) {
      emergenciaEnCurso = false;
      noTone(BUZZER);
      digitalWrite(VENTILADOR, LOW);
      servoEntrada.write(0);
      servoSalida.write(90);
      lcd.clear();
      ultimo = -1;
      enviarSerial("event", "\"action\":\"emergency_off\"");
    }
  }
}

void activarEmergencia() {

  //Variables estáticas para recordar estado
  static unsigned long ultimoParpadeo = 0;  

  //Si recién se activó la flag (primera vez)
  if (emergenciaActiva && !emergenciaEnCurso) {
    digitalWrite(VENTILADOR, HIGH);
    servoEntrada.write(90);
    servoSalida.write(0);

    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("!! EMERGENCIA !!");
    lcd.setCursor(2,1);
    lcd.print("EVACUAR AREA");

    emergenciaEnCurso = true;
    lastBeep = millis();  //resetear para buzzer
    ultimoParpadeo = millis();
    tonoActual = 500;
    subiendo = true;
    
    enviarSerial("event", "\"action\":\"emergency_on\"");
  }

  //Si estamos en emergencia (cada loop)
  if (emergenciaActiva) {

    if (millis() - lastBeep >= 8) {       //cada 8 ms para que suene fluido
      lastBeep = millis();

      tone(BUZZER, tonoActual);           //genera el tono

      if (subiendo) {
        tonoActual += 6;                  //sube rápido
        if (tonoActual >= 1400) subiendo = false;
      } else {
        tonoActual -= 6;                  //baja rápido
        if (tonoActual <= 500) subiendo = true;
      }
    }
    

    //LEDs parpadeo (usa tu función o mueve la lógica aquí)
    if (millis() - ultimoParpadeo > 300) {
      static bool estadoLED = false;
      estadoLED = !estadoLED;
      for(int i = 0; i < 5; i++) {
        if (estadoLED) {
          setColor(i, HIGH, LOW);   //Rojo
        } else {
          setColor(i, LOW, LOW);    //Apagado
        }
      }
      ultimoParpadeo = millis();
    }
  }

  //Condición de salida: cuando ya no hay humo y no es emergencia remota
  if (emergenciaActiva && !emergenciaRemota && digitalRead(MQ2) == HIGH) {
    emergenciaActiva = false;
    emergenciaEnCurso = false;

    noTone(BUZZER);
    digitalWrite(VENTILADOR, LOW);
    servoEntrada.write(0);
    servoSalida.write(90);
    lcd.clear();
    ultimo = -1;  //refresh pantalla normal
    
    enviarSerial("event", "\"action\":\"emergency_off\"");
  }
}

void emergenciaISR() {
  emergenciaActiva = true;
}

void btnSalida(){
  static unsigned long ultimoPresion = 0;
  static bool botonAnterior = HIGH;  //Estado anterior del botón

  bool botonActual = digitalRead(BTN_Salida);

  //Solo detecta flanco descendente (HIGH -> LOW) + debounce
  if (botonActual == LOW && botonAnterior == HIGH && millis() - ultimoPresion > 400) {
    ultimoPresion = millis();

    if (estadoSalida == SALIDA_NORMAL && !emergenciaActiva) {
      estadoSalida = SALIDA_ABRIENDO;
      tiempoSalida = millis();
      anguloSalida = 90;
      enviarSerial("event", "\"action\":\"exit\"");
    }
  }

  botonAnterior = botonActual;  //Actualiza estado anterior

  //Resto de la máquina de estados
  switch (estadoSalida) {
    case SALIDA_ABRIENDO:
      if (millis() - tiempoSalida >= 10) {  // 10 ms por grado para más suave
        tiempoSalida = millis();
        servoSalida.write(anguloSalida);
        anguloSalida--;

        if (anguloSalida <= 0) {
          estadoSalida = SALIDA_ESPERANDO;
          tiempoSalida = millis();
        }
      }
      break;

    case SALIDA_ESPERANDO:
      if (millis() - tiempoSalida >= 2000) {
        estadoSalida = SALIDA_CERRANDO;
        tiempoSalida = millis();
        anguloSalida = 0;
      }
      break;

    case SALIDA_CERRANDO:
      if (millis() - tiempoSalida >= 10) {
        tiempoSalida = millis();
        servoSalida.write(anguloSalida);
        anguloSalida++;

        if (anguloSalida >= 90) {
          estadoSalida = SALIDA_NORMAL;
          enviarSerial("event", "\"action\":\"exit_closed\"");
        }
      }
      break;

    case SALIDA_NORMAL:
      break;
  }
}