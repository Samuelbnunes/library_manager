# Raspberry Pi Guide

Este guia resume como rodar o LibraryManager direto na Raspberry Pi conectada ao Arduino.

## Requisitos

- Raspberry Pi 4
- Raspberry Pi OS com acesso ao terminal
- Python 3 instalado
- Arduino ja gravado com o firmware RFID
- Arduino conectado via USB

## Instalar dependencias

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

## Clonar o projeto

```bash
git clone <URL_DO_REPOSITORIO>
cd library_manager/backend
```

## Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configurar a porta serial

Descubra a porta:

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
```

Edite o `.env`:

```env
SERIAL_PORT=/dev/ttyACM0
LOAN_TIMEOUT_SECONDS=15
ACTIVE_STUDENT_WINDOW_SECONDS=30
```

## Rodar o backend

```bash
python app.py
```

O servico ficara acessivel em:

`http://<ip-da-raspberry>:5000`

## Abrir o dashboard

Na raiz do projeto:

```bash
python3 -m http.server 8000
```

Abra:

`http://<ip-da-raspberry>:8000/web/`

## Checklist de demo

1. Validar conexao serial no dashboard
2. Resetar o banco
3. Identificar um aluno
4. Ler um livro
5. Aguardar o atraso de demonstracao
6. Fazer a devolucao
7. Registrar uma avaliacao

## Fallback de desenvolvimento

Se o Arduino nao estiver conectado no momento, troque temporariamente para:

```env
SERIAL_PORT=MOCK
```

Assim o mesmo software roda na Raspberry Pi mesmo sem o hardware presente.
