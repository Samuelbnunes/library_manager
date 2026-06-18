# Frontend Web Dashboard - Library Manager

Esta é a interface gráfica (Dashboard) do **Library Manager**, desenvolvida de forma responsiva utilizando **HTML5**, **CSS3 (Vanilla)** e **JavaScript Vanilla**, com atualizações automáticas via Long Polling para refletir as leituras do leitor RFID em tempo real.

---

## 🚀 Como Executar

O frontend é composto apenas de arquivos estáticos. Portanto, ele não necessita de nenhuma build ou compilação e pode ser servido de forma muito leve. 

Para que as requisições AJAX de comunicação com o backend funcionem perfeitamente sem problemas de CORS ou bloqueios de segurança do navegador, **recomendamos fortemente iniciar um servidor web simples**.

### Rodando o Servidor Local via Python

Com o Python instalado no seu sistema, execute os comandos a seguir a partir do terminal.

1. **Abra o terminal na pasta `/web`:**
   ```bash
   cd web
   ```

2. **Inicie o servidor HTTP embutido do Python:**
   *No Windows (PowerShell/CMD):*
   ```powershell
      python -m http.server 8000
   ```
   *No Linux / Raspberry Pi:*
   ```bash
   python3 -m http.server 8000
   ```

3. **Acesse no seu navegador:**
   Abra o endereço abaixo para visualizar o painel:
   ```text
   http://localhost:8000
   ```

---

## 📁 Estrutura de Arquivos
- **`index.html`**: Estrutura HTML5 do painel contendo tabelas de acervo, histórico de logs, feedbacks e a barra lateral com as estatísticas de empréstimo.
- **`style.css`**: Estilos visuais personalizados, transições suaves, alertas piscantes de atraso e layouts responsivos para monitores e telas menores.
- **`app.js`**: Lógica JavaScript contendo as chamadas de API (Long Polling) para o backend, controle das modais de avaliação, renderização dinâmica de dados e manipulação da sessão do usuário.
