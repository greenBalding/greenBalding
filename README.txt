# Instruções para instalar e rodar o chat com Ollama (gemma3n:e4b) usando Python

1. Instale o Python 3 (https://www.python.org/downloads/).
   - Certifique-se de marcar a opção "Add Python to PATH" durante a instalação.
   - Após instalar, feche e reabra o terminal/PowerShell.
   - Verifique se o comando `python` está disponível digitando:
     python --version

2. Clone ou copie este repositório para sua máquina.

3. Instale as dependências do backend (Flask, requests, flask-cors):
   pip install flask requests flask-cors

4. Certifique-se de que o Ollama está instalado e rodando:
   - Baixe em https://ollama.com/download
   - Inicie o Ollama

5. Baixe o modelo gemma3n:e4b no Ollama:
   ollama pull gemma3n:e4b

6. Inicie o backend Python:
   python server.py

7. Abra o arquivo index.html no navegador para acessar o chat.

8. Como verificar se o Ollama está rodando:
   - No terminal, execute:
     ollama list

     Se o Ollama estiver rodando, aparecerá uma lista de modelos disponíveis ou uma mensagem indicando que está pronto.
     Se aparecer erro de conexão, o Ollama não está rodando.

   - Você também pode testar o endpoint HTTP do Ollama:
     Abra o navegador e acesse: http://localhost:11434

     Ou use curl:
     curl http://localhost:11434

     Se retornar uma resposta JSON, o Ollama está rodando.

   - Para iniciar manualmente:
     ollama serve

9. Como testar o backend manualmente:

   - **No PowerShell**, use:
     Invoke-RestMethod -Uri http://localhost:3000/chat -Method Post -Body '{"message":"Olá"}' -ContentType "application/json"

   - **No CMD ou Git Bash**, use:
     curl -X POST http://localhost:3000/chat -H "Content-Type: application/json" -d "{\"message\":\"Olá\"}"

     Se receber uma resposta JSON com a mensagem da IA, o backend está funcionando corretamente.

# Como rodar o backend e testar tudo

1. Instale as dependências do Python:
   pip install flask requests flask-cors

2. Certifique-se de que o Ollama está rodando:
   - No terminal, execute:
     ollama list
   - Se aparecer a lista de modelos, está OK.
   - Se não, rode:
     ollama serve

3. Baixe o modelo necessário (se ainda não baixou):
   ollama pull gemma3n:e4b

4. Inicie o backend Python:
   python server.py

5. (Opcional) Rode um servidor local para o frontend:
   python -m http.server 8080
   # Acesse http://localhost:8080 no navegador e abra o index.html

6. Teste o backend manualmente:
   # No PowerShell:
   Invoke-RestMethod -Uri http://localhost:3000/chat -Method Post -Body '{"message":"Olá"}' -ContentType "application/json"
   # No CMD ou Git Bash:
   curl -X POST http://localhost:3000/chat -H "Content-Type: application/json" -d "{\"message\":\"Olá\"}"

# Sobre o arquivo de log (chat.log)

- O arquivo chat.log será criado/atualizado automaticamente.
- Ele registra:
  - Início do backend
  - Se Ollama está rodando ou não
  - Cada mensagem recebida do usuário
  - Payload enviado para o Ollama
  - Resposta recebida do Ollama
  - Erros de conexão, timeout ou outros problemas
- Use o chat.log para identificar rapidamente onde está o problema se algo não funcionar.

# Dicas rápidas de solução de problemas

- Se o Ollama não estiver rodando, rode: ollama serve
- Se o backend não responder, veja o chat.log para detalhes do erro
- Se o frontend não conectar, rode um servidor local (python -m http.server 8080)
- Sempre confira o chat.log após cada tentativa de uso

Obs:
- O backend escuta na porta 3000 por padrão.
- O Ollama deve estar rodando na porta padrão (11434).
- O frontend se comunica com o backend via /chat.

# Dicas de solução de problemas de conexão

- Certifique-se de que o Ollama está rodando antes de iniciar o backend Python.
- Verifique se o backend Python está rodando sem erros (deve aparecer "Running on http://0.0.0.0:3000").
- Se abrir o index.html diretamente e não funcionar, tente rodar um servidor local para servir os arquivos estáticos (por exemplo, com Python: `python -m http.server 8080`) e acesse via navegador em http://localhost:8080.
- Se aparecer erro de CORS, mantenha o backend rodando com flask-cors instalado.
- Se o Ollama não estiver rodando, inicie pelo terminal com o comando `ollama serve` ou abra o aplicativo Ollama.
- Teste o endpoint do backend acessando http://localhost:3000/chat com uma ferramenta como Postman ou curl.
- Se estiver usando WSL ou Docker, verifique se as portas estão expostas corretamente.
