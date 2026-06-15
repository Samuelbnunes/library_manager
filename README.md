# Gerenciador de Biblioteca (RFID)

Este projeto está sendo desenvolvido para integrar um leitor RFID ao sistema. No momento, o projeto conta **apenas com o código de leitura de tags utilizando o sensor RFID MFRC522** conectado a um Arduino.

---

## 🔌 Esquema de Ligação (Pinos)

Conecte o sensor RFID MFRC522 ao seu Arduino utilizando a seguinte configuração de pinos:

| Sinal RFID | Pino Arduino Uno/Nano | Descrição |
| :--- | :--- | :--- |
| **SDA** | `10` |
| **SCK** | `13` |
| **MOSI** | `11` |
| **MISO** | `12` |
| **RST** | `5` |
| **GND** | `GND` |
| **3.3V** | `3.3V` |

---

## 📁 Estrutura do Projeto

*   `rfid_reader/rfid_reader.ino`: Código C++ principal para ler a tag RFID e imprimir o ID (UID) na porta serial.
*   `bin/`: Contém a ferramenta `arduino-cli` utilizada para compilar e gravar os códigos diretamente pelo terminal (Antigravity).
*   `.clangd` & `compile_commands.json`: Arquivos de configuração automática do IntelliSense para suporte do editor de código.

---

## 🚀 Como Usar via Terminal (Antigravity / PowerShell)

Siga estes passos para compilar, enviar e ler as tags do Arduino conectado:

### 1. Compilar o Código
Para verificar o código e compilar o firmware:
```powershell
.\bin\arduino-cli compile --fqbn arduino:avr:uno rfid_reader
```

### 2. Identificar a Porta Serial (COM)
Conecte o Arduino ao USB e descubra em qual porta ele está listado (ex: `COM3`):
```powershell
.\bin\arduino-cli board list
```

### 3. Enviar o Código para a Placa
Grave o código compilado no Arduino (substitua `COM3` pela porta correta listada no passo anterior):
```powershell
.\bin\arduino-cli upload -p COM3 --fqbn arduino:avr:uno rfid_reader
```

### 4. Monitorar e Ler as Tags RFID no Terminal
Para rodar o monitor serial e ver as tags que estão sendo lidas pelo leitor RFID:
```powershell
.\bin\arduino-cli monitor -p COM3 -c baudrate=9600
```
*   **Nota**: Aproxime o cartão/chaveiro RFID do leitor para visualizar o UID no console.
*   **Para fechar**: Pressione `Ctrl + C` no terminal.
