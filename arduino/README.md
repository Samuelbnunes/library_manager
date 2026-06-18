# Library Manager

Sistema de biblioteca com RFID composto por tres blocos:

1. `arduino/`: firmware do Arduino Uno com leitor MFRC522, LEDs e buzzer.
2. `backend/`: API Flask + SQLite + monitor serial via PySerial.
3. `web/`: dashboard em HTML, CSS e JavaScript.

## Arquitetura recomendada

Para Raspberry Pi, o fluxo correto e:

1. Compilar e gravar o firmware no Arduino em um PC ou notebook.
2. Conectar o Arduino ja gravado na Raspberry por USB.
3. Rodar na Raspberry apenas o backend Flask, o banco SQLite e o dashboard web.

Nao e necessario "rodar o Arduino na Raspberry". A Raspberry apenas consome a porta serial USB do Arduino.

## Hardware

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

Observacao: o RC522 deve ser alimentado em `3.3V`, nunca em `5V`.

## Gravar o firmware no Arduino

Consulte o passo a passo detalhado em [arduino/README.md](/abs/path/c:/Users/User/Documents/BernardoFaculdade/library_manager/arduino/README.md:1).

Resumo:

### Windows PowerShell

```powershell
cd arduino
.\bin\arduino-cli core install arduino:avr
.\bin\arduino-cli lib install MFRC522
.\bin\arduino-cli compile --fqbn arduino:avr:uno rfid_reader
.\bin\arduino-cli upload -p COM3 --fqbn arduino:avr:uno rfid_reader
```

## Rodar o backend no Windows

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Crie `backend/.env`:

```env
SERIAL_PORT=COM3
```

Suba o backend:

```powershell
python app.py
```

Testes uteis:

- `http://127.0.0.1:5000/`
- `http://127.0.0.1:5000/api/dashboard`

## Rodar o backend na Raspberry Pi

### 1. Descobrir a porta serial

Com o Arduino conectado por USB:

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
dmesg | tail
```

As portas mais comuns sao:

- `/dev/ttyACM0`
- `/dev/ttyUSB0`

### 2. Criar ambiente e instalar dependencias

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar `backend/.env`

Exemplo:

```env
SERIAL_PORT=/dev/ttyACM0
```

Se preferir, copie de `backend/.env.example`.

### 4. Subir o backend

```bash
python3 app.py
```

### 5. Se houver erro de permissao na serial

```bash
sudo usermod -aG dialout $USER
```

Depois faca logout/login ou reinicie a Raspberry.

## O que foi corrigido no backend

- O backend nao assume mais `COM3` como default.
- O monitor serial tenta autodetectar portas comuns como `/dev/ttyACM0`, `/dev/ttyUSB0` e `COMx`.
- A rota `/` agora responde `200` com informacoes basicas do servico, evitando `404` ao testar o backend pelo navegador.
- A rota `/api/dashboard` agora informa tambem a porta serial em uso.

## Rodar o frontend

O frontend e estatico e nao e servido pelo Flask.

Na raiz do projeto:

### Windows

```powershell
python -m http.server 8000
```

### Linux / Raspberry

```bash
python3 -m http.server 8000
```

Abra:

```text
http://127.0.0.1:8000/web/
```

## Validacao rapida ponta a ponta

1. Suba o backend e confirme `http://127.0.0.1:5000/`.
2. Abra `http://127.0.0.1:5000/api/dashboard` e confira `serial_connected`.
3. Suba o servidor estatico e abra `http://127.0.0.1:8000/web/`.
4. Clique em `Resetar DB`.
5. Aproxime um cartao RFID de aluno.
6. Aproxime uma tag RFID de livro dentro de 30 segundos.
7. Aguarde 15 segundos para validar a regra de atraso.

## Tags de teste cadastradas

### Alunos

- `43 E1 5C FE` -> Ana Silva
- `83 6C C1 02` -> Bruno Santos
- `33 14 11 FF` -> Carlos Oliveira

### Livros

- `63 6F 2C FE` -> Introducao a Bancos de Dados
- `43 82 51 FE` -> Docker Pratico
- `73 BD BF 02` -> Flask Web Development
- `63 34 63 FB` -> Arquitetura Limpa
