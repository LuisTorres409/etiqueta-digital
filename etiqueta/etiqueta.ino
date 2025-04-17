#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

#define DEVICE_NAME "ETIQUETA-1"  // Nome do dispositivo BLE

LiquidCrystal_I2C lcd(0x27, 16, 2);  // Endereço do LCD, 16 colunas, 2 linhas

BLEServer* pServer;
BLECharacteristic* pCharacteristic;
bool deviceConnected = false;
bool oldDeviceConnected = false;

String lastLine1 = "";
String lastLine2 = "";

// Funções auxiliares de LCD
void printLCDLine(String text, int row) {
  lcd.setCursor(0, row);
  for (int i = 0; i < 16; i++) {
    if (i < text.length()) {
      lcd.print(text[i]);
    } else {
      lcd.print(" ");
    }
  }
}

void displayMessage(String message) {
  int splitIndex = message.indexOf("xxx");

  String line1 = "";
  String line2 = "";

  if (splitIndex != -1) {
    line1 = message.substring(0, splitIndex);
    line2 = message.substring(splitIndex + 3);
  } else {
    line1 = message;
    line2 = "";
  }


  if (line1 != lastLine1) {
    printLCDLine(line1, 0);
    lastLine1 = line1;
  }

  if (line2 != lastLine2) {
    printLCDLine(line2, 1);
    lastLine2 = line2;
  }

  Serial.println("Mensagem recebida:");
  Serial.println("L1: " + line1);
  Serial.println("L2: " + line2);
}

// Callbacks BLE
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("Dispositivo conectado");
    }

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("Dispositivo desconectado");
      pServer->startAdvertising();
      Serial.println("Aguardando nova conexão...");
    }
};

class MyCharacteristicCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* pCharacteristic) {
      String value = pCharacteristic->getValue();  // funciona no core ESP32 atual
      
      if (value.length() > 0) {
        Serial.println("*********");
        Serial.print("Novo valor recebido: ");
        Serial.println(value);  // mais simples do que o loop
        Serial.println("*********");

        displayMessage(value);  // supondo que essa função já trate a string corretamente
      }
    }
};

void setup() {
  Serial.begin(115200);

  // Inicializa LCD
  Wire.begin();
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Aguardando BLE");

  // Inicializa BLE
  BLEDevice::init(DEVICE_NAME);
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService* pService = pServer->createService("FFE0");

  pCharacteristic = pService->createCharacteristic(
                      "FFE1",
                      BLECharacteristic::PROPERTY_WRITE
                    );
  pCharacteristic->setCallbacks(new MyCharacteristicCallbacks());
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising* pAdvertising = pServer->getAdvertising();
  pAdvertising->addServiceUUID(pService->getUUID());
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // Compatibilidade iOS
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("Servidor BLE pronto!");
}

void loop() {
  // Trata reconexão BLE
  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    pServer->startAdvertising();
    Serial.println("Aguardando nova conexão...");
    oldDeviceConnected = deviceConnected;
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }

  delay(100);
}
