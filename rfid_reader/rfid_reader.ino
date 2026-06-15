#include <MFRC522.h>
#include <SPI.h>

// Definição dos pinos de conexão
#define SDA_PIN 10
#define RST_PIN 5

// Cria a instância do leitor RFID MFRC522
MFRC522 mfrc522(SDA_PIN, RST_PIN);

void setup() {
  // Inicializa a comunicação serial com o computador
  Serial.begin(9600);
  while (!Serial)
    ; // Aguarda a abertura da porta serial (necessário para placas como
      // Leonardo, Micro, etc.)

  // Inicializa o barramento SPI (SCK: 13, MOSI: 11, MISO: 12 já são padrões no
  // Arduino Uno/Nano)
  SPI.begin();

  // Inicializa o leitor MFRC522
  mfrc522.PCD_Init();

  Serial.println("--- Leitor RFID Inicializado ---");
  Serial.println("Aproxime a sua tag ou cartao do leitor...");
  Serial.println();
}

void loop() {
  // Verifica se há um novo cartão/tag presente no leitor
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Tenta ler o UID (identificador único) do cartão
  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  // Exibe o UID lido na porta serial
  Serial.print("UID da Tag:");
  String uidString = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    // Formata o UID em hexadecimal com dois dígitos (ex: " 0A" em vez de " A")
    if (mfrc522.uid.uidByte[i] < 0x10) {
      Serial.print(" 0");
      uidString += " 0";
    } else {
      Serial.print(" ");
      uidString += " ";
    }
    Serial.print(mfrc522.uid.uidByte[i], HEX);
    uidString += String(mfrc522.uid.uidByte[i], HEX);
  }

  Serial.println();
  uidString.toUpperCase();
  uidString.trim(); // Remove espaços em branco extras nas pontas

  // Exibe o UID formatado
  Serial.print("UID Formatado: ");
  Serial.println(uidString);

  // Exemplo de verificação de Tag específica (Acesso Autorizado)
  // Substitua "XX XX XX XX" pelo UID real da sua tag
  if (uidString == "A1 B2 C3 D4") {
    Serial.println("Status: Acesso Autorizado!");
  } else {
    Serial.println("Status: Tag desconhecida.");
  }
  Serial.println("--------------------------------");

  // Instrua o leitor a parar de ler o cartão atual (evita leituras duplicadas
  // contínuas)
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  // Pequeno delay antes da próxima leitura
  delay(1000);
}
