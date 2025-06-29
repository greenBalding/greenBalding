from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import socket
import json
import os
import uuid

app = Flask(__name__)
CORS(app)

# --- Configuração ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3n:e4b" # Certifique-se que este modelo está disponível no Ollama
CHAT_DIR = "chat_histories"

# Cria o diretório para salvar os históricos se ele não existir
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

# Configuração de logging para um arquivo
logging.basicConfig(
    filename='chat.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    encoding='utf-8'
)

# --- Funções de Utilitário de Chat ---

def list_chat_files():
    """Lista todos os arquivos de chat no diretório, ordenados por data de modificação."""
    try:
        files = [os.path.join(CHAT_DIR, f) for f in os.listdir(CHAT_DIR) if f.endswith('.json')]
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return [os.path.basename(f) for f in files]
    except OSError as e:
        logging.error(f"Erro ao listar arquivos de chat: {e}")
        return []

def save_chat(chat_id, messages):
    """Salva o histórico de mensagens de um chat em um arquivo JSON."""
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logging.error(f"Erro ao salvar o chat {chat_id}: {e}")

def load_chat(chat_id):
    """Carrega o histórico de mensagens de um chat a partir de um arquivo JSON."""
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Erro ao carregar o chat {chat_id}: {e}")
            return []
    return []

def create_new_chat(messages):
    """Cria um novo chat com um ID único."""
    chat_id = str(uuid.uuid4())
    save_chat(chat_id, messages)
    return chat_id

def check_ollama():
    """Verifica se o serviço Ollama está acessível."""
    try:
        # Usamos um timeout baixo para não bloquear a aplicação por muito tempo
        requests.get("http://localhost:11434", timeout=3)
        logging.info("Ollama está rodando e acessível.")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao conectar ao Ollama em http://localhost:11434: {e}")
        return False

# --- Rotas da API ---

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    new_chat = data.get('new_chat', False)

    logging.info(f"Recebida mensagem do usuário: '{message}' (chat_id={chat_id}, new_chat={new_chat})")

    if not message:
        logging.warning("Mensagem não fornecida pelo usuário.")
        return jsonify({'response': 'Mensagem não fornecida.'}), 400

    if not check_ollama():
        logging.error("Tentativa de chat enquanto Ollama está offline.")
        return jsonify({'response': 'O serviço Ollama não está acessível.'}), 503

    try:
        ollama_payload = {
            "model": MODEL,
            "prompt": message,
            "stream": False
        }
        logging.info(f"Enviando payload para Ollama: {ollama_payload}")

        ollama_response = requests.post(OLLAMA_URL, json=ollama_payload, timeout=120)
        ollama_response.raise_for_status()

        response_json = ollama_response.json()
        resposta_ia = response_json.get('response', '')
        logging.info(f"Resposta recebida do Ollama: '{resposta_ia[:80]}...'")

        user_message = {"role": "user", "text": message}
        ai_message = {"role": "ai", "text": resposta_ia}

        if new_chat or not chat_id:
            messages = [user_message, ai_message]
            chat_id = create_new_chat(messages)
            logging.info(f"Novo chat criado com ID: {chat_id}")
        else:
            messages = load_chat(chat_id)
            messages.extend([user_message, ai_message])
            save_chat(chat_id, messages)
            logging.info(f"Mensagens adicionadas ao chat existente: {chat_id}")

        return jsonify({'response': resposta_ia, 'chat_id': chat_id})

    except requests.exceptions.Timeout as te:
        logging.error(f"Timeout ao conectar ao Ollama: {te}")
        return jsonify({'response': 'O pedido ao Ollama demorou muito para responder (timeout).'}), 504
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de conexão com o Ollama: {e}")
        return jsonify({'response': 'Erro de comunicação com o serviço Ollama.'}), 500
    except Exception as e:
        logging.error(f"Erro inesperado no endpoint /chat: {e}", exc_info=True)
        return jsonify({'response': 'Ocorreu um erro inesperado no servidor.'}), 500


@app.route('/history', methods=['GET'])
def get_history_sidebar():
    """Retorna uma lista de chats para a barra lateral."""
    chat_files = list_chat_files()
    sidebar_list = []
    for fname in chat_files:
        chat_id = fname.replace('.json', '')
        messages = load_chat(chat_id)
        if messages:
            # Pega a primeira mensagem do usuário como preview
            first_user_message = next((m['text'] for m in messages if m['role'] == 'user'), 'Chat sem título')
            sidebar_list.append({'preview': first_user_message, 'chat_id': chat_id})
    return jsonify({'sidebar': sidebar_list})

@app.route('/history/<chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    """Retorna o histórico completo de um chat específico."""
    messages = load_chat(chat_id)
    if not messages:
        return jsonify({'error': 'Histórico do chat não encontrado.'}), 404
    return jsonify({'messages': messages})

@app.route('/history/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Apaga um arquivo de histórico de chat."""
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        try:
            os.remove(path)
            logging.info(f"Chat {chat_id} apagado com sucesso.")
            return jsonify({'ok': True})
        except OSError as e:
            logging.error(f"Erro ao apagar o chat {chat_id}: {e}")
            return jsonify({'ok': False, 'error': 'Erro ao apagar o arquivo.'}), 500
    return jsonify({'ok': False, 'error': 'Chat não encontrado.'}), 404

if __name__ == '__main__':
    logging.info("="*40)
    logging.info("Iniciando o servidor Flask do Chat...")
    # Checagem inicial do Ollama
    if not check_ollama():
        logging.warning("ATENÇÃO: Verificação inicial falhou. O serviço Ollama parece estar offline.")
    else:
        logging.info("Verificação inicial: Ollama detectado e online.")

    app.run(host='0.0.0.0', port=3000, debug=False)