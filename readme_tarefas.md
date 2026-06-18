# Tarefas Futuras

Este arquivo serve como backlog tecnico para os proximos passos do LibraryManager. A ideia e permitir que qualquer integrante da equipe, ou outra IA, entenda rapidamente o que ainda pode ser melhorado.

## Objetivo

Evoluir o projeto para uma versao mais robusta para apresentacao final, mantendo compatibilidade com:

- Arduino real
- Raspberry Pi real
- modo MOCK para desenvolvimento

## Prioridade Alta

### 1. Ajustar o Arduino para enviar apenas o UID

Situacao atual:

- o Arduino ainda pode enviar prefixos como `ALUNO:` e `LIVRO:`
- o back-end ja sabe classificar a tag sozinho pelo banco

Proximo passo:

- simplificar o firmware para enviar apenas o UID bruto
- deixar toda a decisao de classificacao no back-end

Impacto:

- menos logica hardcoded no Arduino
- mais flexibilidade para cadastrar novas tags sem regravar a placa

### 2. Melhorar a consistencia visual do dashboard

Ideias:

- refinamento visual dos cards de evento e atraso
- feedback melhor para operacoes negadas
- responsividade ainda mais forte para telas menores

### 3. Criar testes automatizados do backend

Cobrir pelo menos:

- classificacao de RFID
- emprestimo
- devolucao
- atraso
- reset do banco
- rota de avaliacao

## Prioridade Media

### 4. Exportar relatorio simples do acervo

Sugestao:

- rota para exportar status atual em JSON ou CSV
- util para demonstracao e para o relatorio tecnico

### 5. Criar autenticacao basica para administracao

Nao precisa ser complexo. Pode ser algo simples apenas para proteger futuras acoes administrativas.

### 6. Registrar mais metadados nos eventos

Sugestoes:

- IP ou origem da requisicao
- tempo de processamento
- nome amigavel da operacao

## Prioridade Baixa

### 7. Preparar deploy automatizado na Raspberry Pi

Exemplos:

- script `setup_pi.sh`
- servico `systemd` para iniciar o backend automaticamente

### 8. Criar pagina publica de rankings

Separar:

- dashboard operacional
- pagina publica de livros mais emprestados e mais avaliados

## Sugestao de ordem de implementacao

1. Firmware com UID puro
2. Testes automatizados do backend
3. Refinamento visual do dashboard
4. Exportacao de relatorio
5. Deploy automatizado na Raspberry Pi

## Arquivos que devem ser revisados nesses proximos passos

- `arduino/rfid_reader/rfid_reader.ino`
- `backend/app.py`
- `backend/database.py`
- `backend/serial_monitor.py`
- `web/index.html`
- `web/app.js`
- `web/style.css`
