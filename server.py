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

# Configuração de logging detalhado
logging.basicConfig(
    filename='chat.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3n:e4b"
CHAT_DIR = "chat_histories"
if not os.path.exists(CHAT_DIR):
    os.makedirs(CHAT_DIR)

def list_chat_files():
    return sorted([f for f in os.listdir(CHAT_DIR) if f.endswith('.json')])

def save_chat(chat_id, messages):
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def load_chat(chat_id):
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def create_new_chat(messages):
    chat_id = str(uuid.uuid4())
    save_chat(chat_id, messages)
    return chat_id

def check_ollama():
    try:
        resp = requests.get("http://localhost:11434")
        if resp.status_code == 200:
            logging.info("Ollama está rodando e respondeu ao GET /")
            return True
        else:
            logging.error(f"Ollama respondeu com status {resp.status_code}")
            return False
    except Exception as e:
        logging.error(f"Erro ao conectar ao Ollama em http://localhost:11434: {e}")
        return False

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    new_chat = data.get('new_chat', False)
    logging.info(f"Recebida mensagem do usuário: {message} (chat_id={chat_id}, new_chat={new_chat})")
    if not message:
        logging.warning("Mensagem não fornecida pelo usuário.")
        return jsonify({'response': 'Mensagem não fornecida.'}), 400

    if not check_ollama():
        logging.error("Ollama não está rodando no momento da requisição.")
        return jsonify({'response': 'Ollama não está rodando.'}), 500

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
        resposta = response_json.get('response', '')
        logging.info(f"Resposta recebida do Ollama: {resposta}")

        if new_chat or not chat_id:
            # Nova conversa
            messages = [{"role": "user", "text": message}, {"role": "ai", "text": resposta}]
            chat_id = create_new_chat(messages)
        else:
            # Conversa existente
            messages = load_chat(chat_id)
            messages.append({"role": "user", "text": message})
            messages.append({"role": "ai", "text": resposta})
            save_chat(chat_id, messages)

        return jsonify({'response': resposta, 'chat_id': chat_id})
    except requests.exceptions.ConnectionError as ce:
        logging.error(f"Erro de conexão ao Ollama: {ce}")
        return jsonify({'response': 'Erro de conexão ao Ollama.'}), 500
    except requests.exceptions.Timeout as te:
        logging.error(f"Timeout ao conectar ao Ollama: {te}")
        return jsonify({'response': 'Timeout ao conectar ao Ollama.'}), 500
    except Exception as e:
        logging.error(f"Erro inesperado ao conectar ao Ollama: {e}")
        return jsonify({'response': 'Erro inesperado ao conectar ao Ollama.'}), 500

@app.route('/history', methods=['GET'])
def get_history():
    chat_files = list_chat_files()
    sidebarList = []
    for fname in chat_files:
        messages = load_chat(fname[:-5])
        first_user = next((m['text'] for m in messages if m['role'] == 'user'), '')
        sidebarList.append({'preview': first_user, 'chat_id': fname[:-5]})
    return jsonify({'sidebar': sidebarList})

@app.route('/history/<chat_id>', methods=['GET'])
def get_chat_history(chat_id):
    messages = load_chat(chat_id)
    return jsonify({'messages': messages})

@app.route('/history/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    path = os.path.join(CHAT_DIR, f"{chat_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': 'Chat não encontrado'}), 404

if __name__ == '__main__':
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        logging.info(f"Servidor iniciado em http://{ip}:3000")
    except Exception as e:
        logging.warning(f"Não foi possível obter o IP local: {e}")
    # Checagem inicial do Ollama (apenas uma vez)
    if check_ollama():
        logging.info("Verificação inicial: Ollama OK.")
    else:
        logging.error("Verificação inicial: Ollama NÃO está rodando.")
    app.run(host='0.0.0.0', port=3000)