#include <SPI.h>
#include <MFRC522.h>

// Definição dos pinos de conexão do RFID
#define SDA_PIN 10
#define RST_PIN 5

// Definição dos pinos dos LEDs e do Buzzer
#define LED_GREEN_PIN 2
#define LED_RED_PIN   3
#define BUZZER_PIN    4

// Cria a instância do leitor RFID MFRC522
MFRC522 mfrc522(SDA_PIN, RST_PIN);

void setup() {
  // Inicializa a comunicação serial
  Serial.begin(9600);
  while (!Serial);

  // Configuração dos pinos dos LEDs e Buzzer como saída
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Garante que tudo comece desligado
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  // Inicializa o barramento SPI e o leitor MFRC522
  SPI.begin();
  mfrc522.PCD_Init();

  Serial.println("--- Leitor RFID Inicializado ---");
  Serial.println("Aproxime a sua tag ou cartao do leitor...");
  Serial.println();
}

void loop() {
  // 1. Verifica se há comandos chegando do backend (ex: 'R' para indicar atraso de empréstimo)
  if (Serial.available() > 0) {
    char incoming = Serial.read();
    if (incoming == 'R') {
      triggerFailure();
    }
  }

  // 2. Verifica se há um novo cartão/tag presente no leitor
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Tenta ler o UID do cartão
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Formata o UID lido
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) {
      uidString += " 0";
    } else {
      uidString += " ";
    }
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }
  
  uidString.toUpperCase();
  uidString.trim();
  
  // Envia a tag correspondente com base no tipo
  // Estudantes cadastrados:
  // Bernardo Heckler: 43 E1 5C FE
  // Gabriel Rico: 83 6C C1 02
  // Bento Martins: 33 14 11 FF
  if (uidString == "43 E1 5C FE" || uidString == "83 6C C1 02" || uidString == "33 14 11 FF") {
    Serial.print("ALUNO:");
  } else {
    Serial.print("LIVRO:");
  }
  Serial.println(uidString);
  
  // Aguarda a resposta do back-end por até 2 segundos
  unsigned long startWait = millis();
  char response = ' ';
  bool receivedResponse = false;
  
  while (millis() - startWait < 2000) {
    if (Serial.available() > 0) {
      response = Serial.read();
      if (response == 'V' || response == 'R') {
        receivedResponse = true;
        break;
      }
    }
    delay(10);
  }

  if (receivedResponse && response == 'V') {
    triggerSuccess();
  } else {
    triggerFailure();
  }

  // Para a leitura do cartão atual
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(500); // Pequeno intervalo antes da próxima leitura
}

// Função para indicar Acesso Autorizado (LED Verde + Som agudo curto)
void triggerSuccess() {
  digitalWrite(LED_GREEN_PIN, HIGH);
  digitalWrite(LED_RED_PIN, LOW);
  
  // Emite um bipe agudo (frequência de 2500Hz por 150ms)
  tone(BUZZER_PIN, 2500);
  delay(150);
  noTone(BUZZER_PIN);
  
  delay(1350); // Mantém o LED verde aceso pelo restante dos 1.5s
  digitalWrite(LED_GREEN_PIN, LOW);
}

// Função para indicar Acesso Negado (LED Vermelho + Dois bipes graves rápidos)
void triggerFailure() {
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, HIGH);
  
  // Primeiro bipe grave
  tone(BUZZER_PIN, 1000);
  delay(150);
  noTone(BUZZER_PIN);
  
  delay(100); // Intervalo entre os bipes
  
  // Segundo bipe grave
  tone(BUZZER_PIN, 1000);
  delay(150);
  noTone(BUZZER_PIN);
  
  delay(950); // Mantém o LED vermelho aceso pelo restante dos 1.5s
  digitalWrite(LED_RED_PIN, LOW);
}
