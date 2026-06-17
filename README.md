# LibraryManager 📚 — Sistema de Biblioteca RFID (Smart Campus)

Este é o projeto **LibraryManager**, uma solução integrada de Internet das Coisas (IoT) e desenvolvimento web para gerenciamento inteligente de fluxo de empréstimo e devolução de livros em uma biblioteca universitária utilizando tecnologia RFID.

O projeto consiste em três partes principais:
1.  **Firmware Arduino (`/arduino`)**: Código C++ para leitura de tags RFID (MFRC522) com feedback audiovisual (LEDs e Buzzer).
2.  **Back-end Flask (`/backend`)**: API REST em Python que se comunica via Porta Serial (USB) com o Arduino, armazena dados em um banco de dados SQLite e gerencia regras de negócio e de tempo (regra dos 15 segundos para atrasos).
3.  **Front-end Web (`/web`)**: Painel (Dashboard) responsivo feito em HTML5, CSS3 e JavaScript Vanilla com atualizações automáticas (Long Polling).

---

## 🔌 Esquema de Ligação do Hardware

Conecte os componentes ao seu Arduino Uno/Nano utilizando a seguinte configuração de pinos:

| Componente | Pino RFID | Pino Arduino | Observação |
| :--- | :--- | :--- | :--- |
| **Leitor MFRC522** | SDA (SS) | `10` | SPI Chip Select |
| **Leitor MFRC522** | SCK | `13` | SPI Clock |
| **Leitor MFRC522** | MOSI | `11` | SPI Master Out Slave In |
| **Leitor MFRC522** | MISO | `12` | SPI Master In Slave Out |
| **Leitor MFRC522** | RST | `5` | Reset |
| **Leitor MFRC522** | GND | `GND` | Terra |
| **Leitor MFRC522** | 3.3V | `3.3V` | **Atenção:** NÃO ligar no pino de 5V! |
| **LED Verde** | Ânodo (+) | `2` | Feedback de sucesso |
| **LED Vermelho** | Ânodo (+) | `3` | Feedback de erro/atraso |
| **Buzzer** | Positivo (+) | `4` | Avisos sonoros |

*Nota: Use resistores apropriados (220Ω ou 330Ω) em série com os LEDs para protegê-los de sobrecorrente.*

---

## 🛠️ Instalação Passo a Passo (Para máquina sem nada instalado)

Siga este guia para configurar o ambiente do zero no **Windows** (instruções adaptáveis para Linux/macOS).

### Passo 1: Instalar o Python e Dependências do Sistema

1.  **Baixar e Instalar o Python**:
    *   Acesse o site oficial: [python.org/downloads](https://www.python.org/downloads/)
    *   Baixe a versão mais recente (ex: Python 3.12 ou superior).
    *   **CRÍTICO:** Durante a instalação, marque a caixinha **"Add Python.exe to PATH"** na primeira tela antes de clicar em instalar.
2.  **Instalar Drivers USB do Arduino (se necessário)**:
    *   Se a sua placa Arduino for uma réplica/paralela (muito comum), você precisará instalar o driver **CH340**. Pesquise por *"Driver CH340 Windows"* no Google, baixe e instale para que o computador reconheça a porta USB (ex: `COM3`).

---

### Passo 2: Gravar o Firmware no Arduino

A pasta `arduino/bin/` contém binários específicos de sistema operacional, ela é ignorada pelo Git (`.gitignore`). Siga o passo a passo para compilar e enviar o código para a placa:

#### Usando a Ferramenta de Linha de Comando (`arduino-cli`)
Se você prefere continuar usando comandos de terminal:
1.  **Instalar o `arduino-cli`**:
    *   **Windows**: Baixe o arquivo ZIP da página oficial do [Arduino CLI Releases](https://arduino.github.io/arduino-cli/latest/installation/) ou instale via terminal usando o gerenciador do Windows:
        ```powershell
        winget install Arduino.ArduinoCLI
        ```
        Depois, crie uma pasta chamada `bin` dentro da pasta `arduino` e mova o executável `arduino-cli.exe` para dentro dela.
    *   **macOS / Linux / Raspberry Pi**: Instale rodando o script oficial:
        ```bash
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
        ```
        Crie a pasta `bin` dentro de `arduino/` e mova o executável gerado para lá.
2.  Abra o terminal na pasta `arduino/`.
3.  Instale o núcleo da placa Arduino Uno e a biblioteca necessária:
    ```powershell
    .\bin\arduino-cli core install arduino:avr
    .\bin\arduino-cli lib install MFRC522
    ```
4.  **Compilar o código**:
    ```powershell
    .\bin\arduino-cli compile --fqbn arduino:avr:uno rfid_reader
    ```
5.  **Enviar o código para a placa**:
    Substitua `COM3` pela sua porta:
    ```powershell
    .\bin\arduino-cli upload -p COM3 --fqbn arduino:avr:uno rfid_reader
    ```
    *(Dica: Para descobrir a porta no Windows, consulte a seção "Portas (COM e LPT)" no Gerenciador de Dispositivos).*

---

### Passo 3: Configurar e Rodar o Back-end Flask

1.  No seu terminal, navegue até a pasta `backend`:
    ```powershell
    cd ../backend
    ```
2.  **Criar um Ambiente Virtual (Venv)**:
    Isso isola as dependências do projeto para não poluir sua máquina.
    ```powershell
    python -m venv venv
    ```
3.  **Ativar o Ambiente Virtual**:
    *   No Windows (PowerShell):
        ```powershell
        .\venv\Scripts\activate
        ```
    *   No macOS/Linux (Terminal):
        ```bash
        source venv/bin/activate
        ```
4.  **Instalar os Pacotes Necessários**:
    ```powershell
    pip install -r requirements.txt
    ```
5.  **Configurar a Porta Serial**:
    Crie um arquivo chamado `.env` na pasta `/backend` e insira a porta COM do seu Arduino:
    ```env
    SERIAL_PORT=COM3
    ```
6.  **Iniciar o Servidor**:
    ```powershell
    python app.py
    ```
    O servidor iniciará no endereço `http://localhost:5000` e começará a escutar a porta serial em segundo plano.

---

### Passo 4: Abrir o Front-end Web Dashboard

Como o front-end foi desenvolvido em JavaScript Vanilla e CSS puro (sem frameworks pesados), você pode rodá-lo de duas formas extremamente simples:

*   **Opção A (Mais fácil)**: Abra a pasta `/web` no seu gerenciador de arquivos do Windows e dê dois cliques no arquivo `index.html` para abri-lo diretamente no navegador.
*   **Opção B (Recomendada via servidor local)**: Abra um novo terminal na pasta do projeto e inicie o servidor embutido do Python:
    ```powershell
    python -m http.server 8000
    ```
    Acesse no seu navegador: `http://localhost:8000/web/`

---

## 🕹️ Testando as Regras de Negócio (Fluxo Completo)

Com tudo rodando, você pode testar a lógica do sistema com as tags configuradas:

### Tags Cadastradas padrão (Mapeadas no Arduino e Banco de Dados):
*   **Alunos**:
    *   Ana Silva: `43 E1 5C FE`
    *   Bruno Santos: `83 6C C1 02`
    *   Carlos Oliveira: `33 14 11 FF`
*   **Livros**:
    *   Introdução a Bancos de Dados: `63 6F 2C FE`
    *   Docker Prático: `43 82 51 FE`
    *   Flask Web Development: `73 BD BF 02`
    *   Arquitetura Limpa: `63 34 63 FB`

### Teste Passo a Passo:
1.  **Resetar Banco**: No Dashboard, clique no botão **"Resetar DB"** no canto superior direito para carregar os dados de teste.
2.  **Identificar o Aluno**: Aproxime o cartão da **Ana Silva** (`43 E1 5C FE`) do leitor.
    *   *Arduino*: Acenderá o LED Verde e dará 1 bipe.
    *   *Dashboard*: O status do Arduino mudará e o sistema guardará a sessão da Ana por 30 segundos.
3.  **Realizar Empréstimo**: Dentro dos 30 segundos, aproxime o livro **Docker Prático** (`43 82 51 FE`) do leitor.
    *   *Arduino*: Acenderá o LED Verde e dará 1 bipe.
    *   *Dashboard*: O livro mudará para o status "Emprestado" em azul, e o histórico mostrará "Ana Silva emprestou 'Docker Prático'".
4.  **Testar Alerta de Atraso (Regra dos 15 segundos)**: Não faça nada por 15 segundos.
    *   *Dashboard*: Após 15 segundos, o status do livro e do empréstimo mudará automaticamente para "Em Atraso" (vermelho piscando) e o painel de métricas ativará o alerta vermelho.
    *   *Arduino*: Receberá um comando de erro do servidor e ativará o LED Vermelho e emitirá dois bipes graves.
5.  **Realizar Devolução**: Aproxime o cartão da **Ana Silva** novamente para reativar a sessão e, em seguida, aproxime o livro **Docker Prático**.
    *   *Arduino*: LED Verde e 1 bipe.
    *   *Dashboard*: O livro voltará para o status "Disponível". Um banner verde aparecerá no topo do Dashboard dizendo *"Ana Silva devolveu 'Docker Prático'. Que tal avaliá-lo?"*
6.  **Dar Feedback**: Clique no botão **"Avaliar Livro"** na notificação ou na tabela do acervo, escolha a quantidade de estrelas, digite um comentário e clique em salvar. O comentário aparecerá imediatamente na listagem de feedbacks e influenciará o ranking lateral.
