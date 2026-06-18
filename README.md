# LibraryManager | Smart Campus

LibraryManager e um sistema de gerenciamento de biblioteca com RFID pensado para o contexto de Smart Campus. O projeto integra Arduino, Raspberry Pi, aplicacao Python com Flask, banco SQLite e dashboard web para demonstrar emprestimos, devolucoes, atrasos e feedbacks de livros.

## Arquitetura

O projeto e dividido em tres blocos:

1. `arduino/`
   Firmware responsavel pela leitura RFID, LEDs e buzzer.
2. `backend/`
   API Flask que concentra a regra de negocio, o banco SQLite, a comunicacao serial e o modo MOCK.
3. `web/`
   Dashboard web para acompanhar o acervo, aluno ativo, eventos do sistema, atrasos e avaliacoes.

Fluxo principal:

`Tag RFID -> Arduino -> Serial USB -> Raspberry Pi / Backend Flask -> SQLite -> Dashboard`

## O que o sistema entrega hoje

- Leitura de RFID para alunos e livros
- Emprestimo e devolucao automatizados
- Regra de atraso em 15 segundos para demonstracao
- Dashboard com:
  - aluno ativo
  - consulta de acervo
  - alertas de atraso
  - historico recente
  - eventos do sistema
  - ranking de livros
  - avaliacoes
- Modo `MOCK` para desenvolver sem hardware fisico
- Back-end preparado para rodar em Windows, macOS, Ubuntu e Raspberry Pi

## Execucao local sem hardware

O modo recomendado para desenvolvimento em casa e o `MOCK`.

### 1. Criar o ambiente do backend

Windows:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS / Ubuntu / Raspberry Pi:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite o arquivo `.env` para garantir:

```env
SERIAL_PORT=MOCK
LOAN_TIMEOUT_SECONDS=15
ACTIVE_STUDENT_WINDOW_SECONDS=30
```

### 2. Iniciar o backend

Windows:

```powershell
python app.py
```

macOS / Ubuntu / Raspberry Pi:

```bash
python app.py
```

O backend sobe em `http://localhost:5000`.

### 3. Abrir o dashboard

Na raiz do projeto:

Windows:

```powershell
python -m http.server 8000
```

macOS / Ubuntu / Raspberry Pi:

```bash
python3 -m http.server 8000
```

Abra:

`http://localhost:8000/web/`

## Como testar em MOCK

No dashboard, o painel de modo MOCK permite:

- ler uma tag como `ALUNO`
- ler uma tag como `LIVRO`
- testar leitura generica `RFID`, deixando o back-end decidir se e aluno ou livro

Fluxo recomendado:

1. Clique em `Resetar DB`
2. Leia um aluno
3. Leia um livro
4. Aguarde 15 segundos para ver o atraso
5. Leia o mesmo aluno novamente
6. Leia o mesmo livro para devolver
7. Registre uma avaliacao

## Rodando com Raspberry Pi e Arduino

Quando o hardware estiver em maos, basta trocar a porta serial no `.env`.

Exemplos:

- Windows: `SERIAL_PORT=COM3`
- macOS: `SERIAL_PORT=/dev/cu.usbmodemXXXX`
- Ubuntu / Raspberry Pi: `SERIAL_PORT=/dev/ttyACM0`

Depois:

1. Conecte o Arduino por USB na Raspberry Pi
2. Descubra a porta:
   - `ls /dev/ttyACM*`
   - `ls /dev/ttyUSB*`
3. Atualize `SERIAL_PORT`
4. Rode o backend Flask
5. Abra o dashboard pela rede local ou direto na Raspberry

Ha um guia resumido adicional em [README_RASPBERRY_PI.md](C:\Users\bernardo\Documents\github\library_manager\README_RASPBERRY_PI.md).

## Ligacao do hardware

Pinos usados no Arduino:

- RFID SDA -> pino `10`
- RFID SCK -> pino `13`
- RFID MOSI -> pino `11`
- RFID MISO -> pino `12`
- RFID RST -> pino `5`
- LED verde -> pino `2`
- LED vermelho -> pino `3`
- buzzer -> pino `4`

Importante:

- o modulo RC522 deve ser alimentado em `3.3V`
- use resistor para os LEDs

## Arquivos importantes

- [backend/app.py](C:\Users\bernardo\Documents\github\library_manager\backend\app.py)
- [backend/database.py](C:\Users\bernardo\Documents\github\library_manager\backend\database.py)
- [backend/serial_monitor.py](C:\Users\bernardo\Documents\github\library_manager\backend\serial_monitor.py)
- [web/index.html](C:\Users\bernardo\Documents\github\library_manager\web\index.html)
- [web/app.js](C:\Users\bernardo\Documents\github\library_manager\web\app.js)
- [web/style.css](C:\Users\bernardo\Documents\github\library_manager\web\style.css)
- [readme_tarefas.md](C:\Users\bernardo\Documents\github\library_manager\readme_tarefas.md)

## Proximos passos

As proximas melhorias planejadas foram consolidadas em [readme_tarefas.md](C:\Users\bernardo\Documents\github\library_manager\readme_tarefas.md) para que qualquer integrante da equipe ou outra IA consiga continuar a evolucao do projeto.
