# Arduino RFID

Firmware do Arduino Uno para leitura RFID com `MFRC522`, `LED Verde`, `LED Vermelho` e `Buzzer`.

## Estrutura

- `rfid_reader/rfid_reader.ino`: firmware principal.
- `bin/arduino-cli`: opcional, caso você mantenha o executável localmente nessa pasta.

## Ligações

| Componente | Pino Arduino |
| --- | --- |
| RFID SDA (SS) | `10` |
| RFID SCK | `13` |
| RFID MOSI | `11` |
| RFID MISO | `12` |
| RFID RST | `5` |
| RFID GND | `GND` |
| RFID 3.3V | `3.3V` |
| LED Verde | `2` |
| LED Vermelho | `3` |
| Buzzer | `4` |

*Observação: O módulo RC522 deve ser alimentado na saída de `3.3V` do Arduino, nunca na de `5V`.*

---

## Como Compilar e Gravar o Firmware

### Windows (PowerShell)

1. **Acesse a pasta do Arduino:**
   ```powershell
   cd arduino
   ```

2. **Instale as dependências da placa e do leitor RFID:**
   ```powershell
   .\bin\arduino-cli core install arduino:avr
   .\bin\arduino-cli lib install MFRC522
   ```

3. **Compile o código:**
   ```powershell
   .\bin\arduino-cli compile --fqbn arduino:avr:uno rfid_reader
   ```

4. **Envie para a placa (substitua `COM3` pela porta do seu Arduino):**
   ```powershell
   .\bin\arduino-cli upload -p COM3 --fqbn arduino:avr:uno rfid_reader
   ```

5. **Monitore a porta serial:**
   ```powershell
   .\bin\arduino-cli monitor -p COM3 -c baudrate=9600
   ```

---

### Linux ou Raspberry Pi (Terminal)

Se você preferir compilar diretamente no Raspberry Pi ou em outra máquina Linux:

1. **Acesse a pasta do Arduino:**
   ```bash
   cd arduino
   ```

2. **Baixe o `arduino-cli` correto para a arquitetura do Linux (ex: ARM do Raspberry Pi):**
   ```bash
   curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
   ```

3. **Atualize o índice e instale as dependências:**
   ```bash
   ./bin/arduino-cli core update-index
   ./bin/arduino-cli core install arduino:avr
   ./bin/arduino-cli lib install "MFRC522"
   ```

4. **Compile o firmware:**
   ```bash
   ./bin/arduino-cli compile --fqbn arduino:avr:uno rfid_reader
   ```

5. **Envie para a placa (identifique a porta correta, ex: `/dev/ttyACM0`):**
   ```bash
   ./bin/arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno rfid_reader
   ```

6. **Monitore a porta serial:**
   ```bash
   ./bin/arduino-cli monitor -p /dev/ttyACM0 -c baudrate=9600
   ```

#### Como descobrir a porta serial correta no Linux:
```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
dmesg | tail
```

---

## Observação Importante

O projeto principal não exige que você compile o firmware do Arduino dentro do Raspberry Pi. A arquitetura recomendada é compilar e gravar no Arduino a partir de um computador pessoal (Windows/macOS) e depois conectar o Arduino pronto à porta USB do Raspberry Pi para que o backend Flask o consuma.
