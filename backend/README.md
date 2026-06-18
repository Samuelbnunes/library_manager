# Backend - Library Manager

Esta é a API backend do **Library Manager**, construída em **Flask (Python)** com banco de dados **SQLite** e monitoramento em tempo real da porta serial (comunicação com o Arduino) usando **PySerial**.

---

## 🛠️ Requisitos
- Python 3.8 ou superior instalado.
- Porta serial/USB ativa e conectada ao Arduino com o firmware do leitor RFID gravado.

---

## ⚙️ Instalação e Execução

### No Windows (PowerShell)

1. **Acesse a pasta do backend:**
   ```powershell
   cd backend
   ```

2. **Crie um ambiente virtual (venv):**
   ```powershell
   python -m venv venv
   ```

3. **Ative o ambiente virtual:**
   ```powershell
   .\venv\Scripts\activate
   ```

4. **Instale as dependências:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configuração da Porta Serial (.env):**
   Crie um arquivo chamado `.env` na pasta `/backend` e insira a porta COM do seu Arduino (ex: `COM3`):
   ```env
   SERIAL_PORT=COM3
   ```

6. **Inicie o servidor:**
   ```powershell
   python app.py
   ```

---

### No Linux ou Raspberry Pi (Terminal)

1. **Identifique a porta do Arduino:**
   Com o Arduino conectado ao USB da Raspberry Pi, execute um dos comandos abaixo para identificar o nome da porta serial:
   ```bash
   ls /dev/ttyACM*
   ls /dev/ttyUSB*
   # Ou verifique os logs do sistema
   dmesg | tail
   ```
   *As portas comuns no Linux são `/dev/ttyACM0` ou `/dev/ttyUSB0`.*

2. **Acesse a pasta do backend:**
   ```bash
   cd backend
   ```

3. **Crie o ambiente virtual (venv):**
   ```bash
   python3 -m venv venv
   ```

4. **Ative o ambiente virtual:**
   ```bash
   source venv/bin/activate
   ```

5. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Configuração da Porta Serial (.env):**
   Crie ou edite o arquivo `.env` com o caminho da porta que você identificou no passo 1:
   ```env
   SERIAL_PORT=/dev/ttyACM0
   ```

7. **Permissões de acesso à Serial (se necessário):**
   Caso ocorra algum erro de permissão negada ao tentar acessar a porta serial, adicione o seu usuário ao grupo `dialout`:
   ```bash
   sudo usermod -aG dialout $USER
   ```
   *Após rodar este comando, é necessário fazer logout/login ou reiniciar a Raspberry para aplicar as alterações.*

8. **Inicie o servidor:**
   ```bash
   python3 app.py
   ```

---

## 📡 Endpoints Úteis
Após iniciar o backend, ele estará disponível por padrão em `http://localhost:5000/`.

- **`GET /`**: Retorna informações básicas de status e saúde do serviço.
- **`GET /api/dashboard`**: Retorna o estado atual do dashboard (sessão ativa do estudante, livros emprestados, logs recentes, alertas e a porta serial conectada).
- **`POST /api/reset`**: Reseta o banco de dados SQLite para o estado padrão de testes.
