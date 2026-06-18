# LibraryManager 📚 — IoT & Smart Campus

O **LibraryManager** é uma solução de Internet das Coisas (IoT) desenvolvida para modernizar e otimizar o fluxo de gerenciamento de bibliotecas em ambientes de **Smart Campus** (Campi Inteligentes). Através da integração entre hardware, comunicação serial em tempo real e uma interface web interativa, o sistema automatiza processos cotidianos de empréstimo e devolução de livros, reduzindo filas e melhorando a experiência dos estudantes.

---

## 🌟 Principais Recursos e Benefícios

*   **Identificação RFID Inteligente**: Reconhecimento instantâneo de alunos e livros utilizando tecnologia RFID (MFRC522), eliminando a digitação manual ou leitura lenta de código de barras.
*   **Feedback Audiovisual em Tempo Real**: O terminal físico (Arduino) emite alertas visuais (LEDs Verde e Vermelho) e sonoros (Buzzer com diferentes frequências) para indicar o sucesso ou falha instantânea de cada operação.
*   **Controle Inteligente de Prazos**: Sistema automático de monitoramento de prazos (com regra demonstrativa de 15 segundos para alertas rápidos), acionando notificações imediatas na interface caso um empréstimo expire.
*   **Painel Administrativo Completo (Dashboard)**: Monitoramento dinâmico que exibe o estudante ativo na sessão, acervo disponível, histórico detalhado de logs e um ranking interativo de livros recomendados.
*   **Engajamento de Leitores**: Sistema integrado para que os alunos avaliem e deixem feedbacks/estrelas para os livros que acabaram de devolver, incentivando a comunidade de leitores do campus.
*   **Modo Simulação (MOCK)**: Possibilidade de testar toda a lógica do ecossistema e interface web mesmo sem ter o hardware conectado físico, facilitando o desenvolvimento offline.

---

## 🏗️ Arquitetura do Sistema

O projeto é construído em uma arquitetura modular dividida em três pilares principais:

```
[Módulo RFID / Arduino] ---> (Conexão Serial USB) ---> [Backend Flask / SQLite] ---> [Dashboard Web]
```

1.  **Firmware Arduino ([`/arduino`](file:///c:/Users/Samuel/Downloads/library_manager/arduino))**: Desenvolvido em C++, gerencia as leituras do leitor de cartão/tag RFID e controla as respostas físicas (LEDs/Buzzer) baseadas nos comandos enviados pelo servidor.
2.  **Back-end API ([`/backend`](file:///c:/Users/Samuel/Downloads/library_manager/backend))**: Desenvolvido em Python (Flask) integrado a um banco de dados SQLite. Gerencia a sessão de empréstimo (janela de 30 segundos), a regra de negócio para notificações de atraso, o histórico de ações e a comunicação com a porta serial (via PySerial).
3.  **Front-end Web ([`/web`](file:///c:/Users/Samuel/Downloads/library_manager/web))**: Painel visual construído com tecnologias web modernas (HTML5, CSS3, JavaScript Vanilla) que atualiza as informações automaticamente em tempo real através de técnicas de Long Polling.

---

## 🚀 Guia de Instalação e Execução

Para facilitar a configuração do ambiente, cada componente do ecossistema possui seu próprio guia de instalação detalhado e passo a passo. Acesse o guia do módulo desejado nos links abaixo:

*   📖 **Configurar o Hardware e Firmware**: Veja o [README do Arduino (arduino/README.md)](file:///c:/Users/Samuel/Downloads/library_manager/arduino/README.md).
*   ⚙️ **Instalar e Subir a API Flask**: Veja o [README do Backend (backend/README.md)](file:///c:/Users/Samuel/Downloads/library_manager/backend/README.md).
*   💻 **Visualizar o Dashboard Web**: Veja o [README do Frontend (web/README.md)](file:///c:/Users/Samuel/Downloads/library_manager/web/README.md).

---

## 📝 Tags de Teste Cadastradas (Padrão)

Caso esteja testando o sistema física ou virtualmente (modo MOCK), as seguintes tags já estão pré-configuradas no banco de dados para simulação rápida:

### 👤 Alunos Cadastrados
*   `43 E1 5C FE` — Ana Silva
*   `83 6C C1 02` — Bruno Santos
*   `33 14 11 FF` — Carlos Oliveira

### 📚 Livros no Acervo
*   `63 6F 2C FE` — Introdução a Bancos de Dados
*   `43 82 51 FE` — Docker Prático
*   `73 BD BF 02` — Flask Web Development
*   `63 34 63 FB` — Arquitetura Limpa
