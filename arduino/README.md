# Gerenciador de Biblioteca (RFID)

Este projeto está sendo desenvolvido para integrar um leitor RFID ao sistema. No momento, o projeto conta com o código de leitura de tags utilizando o sensor RFID MFRC522, com feedback visual (LEDs) e sonoro (Buzzer) de acesso autorizado ou negado.

---

## 🔌 Esquema de Ligação (Pinos)

Conecte os componentes ao seu Arduino utilizando a seguinte configuração de pinos:

| Sinal / Componente | Pino Arduino Uno/Nano | Descrição |
| :--- | :--- | :--- |
| **SDA (RFID)** | `10` | SPI SS (Selector / Chip Select) |
| **SCK (RFID)** | `13` | SPI Clock |
| **MOSI (RFID)** | `11` | SPI Master Out Slave In |
| **MISO (RFID)** | `12` | SPI Master In Slave Out |
| **RST (RFID)** | `5` | Reset |
| **GND (RFID)** | `GND` | Terra / Ground |
| **3.3V (RFID)** | `3.3V` | **Atenção:** Alimentação de 3.3V (Não ligar no 5V!) |
| **LED Verde** | `2` | Sinaliza **Acesso Autorizado** |
| **LED Vermelho** | `3` | Sinaliza **Acesso Negado** |
| **Buzzer** | `4` | Emite alertas sonoros (Bipe agudo para sucesso, bipes graves para erro) |

*Nota: Não se esqueça de usar resistores apropriados (como 220Ω ou 330Ω) em série com os LEDs para protegê-los de sobrecorrente.*

---

## 📁 Estrutura do Projeto

*   `rfid_reader/rfid_reader.ino`: Código C++ principal com lógica de detecção de tags, controle de LEDs e Buzzer.
*   `bin/`: Contém a ferramenta `arduino-cli` utilizada para compilar e gravar os códigos diretamente pelo terminal (Antigravity).
*   `.clangd` & `compile_commands.json`: Arquivos de configuração do IntelliSense.

---

## 🚀 Como Usar via Terminal (Antigravity / PowerShell)

### 1. Compilar o Código
```powershell
.\bin\arduino-cli compile --fqbn arduino:avr:uno rfid_reader
```

### 2. Enviar o Código para a Placa
Grave o código no Arduino conectado à porta serial correta (ex: `COM3`):
```powershell
.\bin\arduino-cli upload -p COM3 --fqbn arduino:avr:uno rfid_reader
```

### 3. Monitorar no Terminal
Veja as leituras e mensagens de status do acesso diretamente na sua tela:
```powershell
.\bin\arduino-cli monitor -p COM3 -c baudrate=9600
```
*   **Para fechar**: Pressione `Ctrl + C` no terminal.
