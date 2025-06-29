const messagesDiv = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const tokenCountSpan = document.getElementById('token-count');
const responseTimeSpan = document.getElementById('response-time');

function escapeHtml(text) {
    return text.replace(/[&<>"']/g, function (m) {
        return ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        })[m];
    });
}

// Markdown básico: **negrito**, *itálico*, `código`, [link](url)
function renderMarkdown(text) {
    let html = escapeHtml(text);
    // Links: [texto](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    // URLs soltas
    html = html.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
    // Negrito: **texto**
    html = html.replace(/\*\*([^\*]+)\*\*/g, '<b>$1</b>');
    // Itálico: *texto*
    html = html.replace(/\*([^\*]+)\*/g, '<i>$1</i>');
    // Código: `código`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Quebra de linha
    html = html.replace(/\n/g, '<br>');
    // Listas simples
    html = html.replace(/(^|\n)[\*\-] (.+)/g, '$1<li>$2</li>');
    return html;
}

function appendMessage(text, sender) {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    // Renderiza markdown para a IA
    if (sender === 'ai') {
        msg.innerHTML = renderMarkdown(text);
    } else {
        msg.textContent = text;
    }
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function countTokens(text) {
    // Aproximação simples: 1 token ≈ 1 palavra
    return text.trim().split(/\s+/).length;
}

function formatDuration(ms) {
    const totalMs = Math.round(ms);
    const hours = Math.floor(totalMs / 3600000);
    const minutes = Math.floor((totalMs % 3600000) / 60000);
    const seconds = Math.floor((totalMs % 60000) / 1000);
    const millis = totalMs % 1000;
    return (
        (hours > 0 ? String(hours).padStart(2, '0') + ':' : '') +
        String(minutes).padStart(2, '0') + ':' +
        String(seconds).padStart(2, '0') + '.' +
        String(millis).padStart(3, '0')
    );
}

let timerInterval = null;
let startTime = 0;

function startTimer() {
    startTime = performance.now();
    responseTimeSpan.textContent = `Tempo: 00:00.000`;
    timerInterval = setInterval(() => {
        const now = performance.now();
        responseTimeSpan.textContent = `Tempo: ${formatDuration(now - startTime)}`;
    }, 31); // Atualiza a cada ~30ms para suavidade
}

function stopTimerAndShow(finalMs) {
    clearInterval(timerInterval);
    responseTimeSpan.textContent = `Tempo: ${formatDuration(finalMs)}`;
}

let chatSidebarList = [];
let activeChatId = null;

async function loadSidebarList() {
    try {
        const res = await fetch('http://localhost:3000/history');
        if (!res.ok) throw new Error('Erro ao buscar histórico');
        const data = await res.json();
        chatSidebarList = data.sidebar;
        renderSidebarList();
    } catch (e) {
        document.getElementById('history-list').innerHTML = '<div style="color:#991b1b;padding:8px;">Erro ao carregar histórico</div>';
    }
}

function renderSidebarList() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';

    // Botão para criar novo chat (agora implícito ao clicar "Novo Chat")
    chatSidebarList.forEach((item) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'history-item-wrapper';
        const el = document.createElement('div');
        el.className = 'history-item' + (item.chat_id === activeChatId ? ' active' : '');
        const previewText = item.preview || 'Novo Chat';
        el.textContent = previewText.slice(0, 40) + (previewText.length > 40 ? '...' : '');
        el.title = previewText;
        el.onclick = () => {
            activeChatId = item.chat_id;
            renderSidebarList();
            renderChatMessages(item.chat_id);
        };
        // Botão de apagar
        const delBtn = document.createElement('button');
        delBtn.textContent = '🗑️';
        delBtn.title = 'Apagar chat';
        delBtn.className = 'delete-chat-btn';
        delBtn.onclick = (ev) => {
            ev.stopPropagation();
            if (confirm('Deseja apagar este chat?')) {
                deleteChatById(item.chat_id);
            }
        };
        wrapper.appendChild(el);
        wrapper.appendChild(delBtn);
        historyList.appendChild(wrapper);
    });
}

async function deleteChatById(chatId) {
    try {
        const res = await fetch(`http://localhost:3000/history/${chatId}`, { method: 'DELETE' });
        if (res.ok) {
            // Se o chat apagado era o atual, limpa a tela para um novo chat
            if (activeChatId === chatId) {
                messagesDiv.innerHTML = '';
                activeChatId = null;
                 userInput.value = '';
            }
            await loadSidebarList();
        } else {
             alert('Erro ao apagar chat. Verifique o console.');
        }
    } catch (e) {
        alert('Erro ao apagar chat.');
    }
}

async function renderChatMessages(chatId) {
    messagesDiv.innerHTML = '';
    if (!chatId) return;
    try {
        const res = await fetch(`http://localhost:3000/history/${chatId}`);
        if (res.ok) {
            const data = await res.json();
            data.messages.forEach(msg => appendMessage(msg.text, msg.role));
        }
    } catch(e) {
        appendMessage('Erro ao carregar mensagens do histórico.', 'ai');
    }
}

document.getElementById('new-chat-btn').onclick = () => {
    userInput.value = '';
    messagesDiv.innerHTML = '';
    activeChatId = null;
    renderSidebarList(); // Re-renderiza a lista para desmarcar o chat ativo
    tokenCountSpan.textContent = `Tokens: 0`;
    responseTimeSpan.textContent = `Tempo: 00:00.000`;
    userInput.focus();
};

window.addEventListener('DOMContentLoaded', () => {
    loadSidebarList();
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    userInput.value = '';
    userInput.focus();

    const placeholder = document.createElement('div');
    placeholder.className = 'message ai';
    placeholder.textContent = '...';
    messagesDiv.appendChild(placeholder);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;


    startTimer();
    try {
        const res = await fetch('http://localhost:3000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                chat_id: activeChatId,
                new_chat: activeChatId === null
            })
        });

        const end = performance.now();
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.response || 'Backend offline');
        }
        
        const data = await res.json();
        
        // Remove placeholder e adiciona a resposta final da IA
        placeholder.remove();
        appendMessage(data.response, 'ai');

        // Se era um novo chat, atualiza o ID ativo e recarrega a barra lateral
        if (activeChatId === null) {
            activeChatId = data.chat_id;
            await loadSidebarList(); // Recarrega a sidebar para mostrar o novo chat
        }
        
        // Atualiza stats
        const tokens = countTokens(data.response || '');
        tokenCountSpan.textContent = `Tokens: ${tokens}`;
        stopTimerAndShow(end - startTime);

        // Esconde alerta de erro se estava visível
        const alert = document.getElementById('backend-alert');
        if (alert) alert.style.display = 'none';

    } catch (err) {
        // Remove placeholder e mostra mensagem de erro no chat
        placeholder.remove();
        appendMessage(`Erro: ${err.message}`, 'ai');
        
        // Mostra alerta visual no topo
        const alert = document.getElementById('backend-alert');
        if (alert) alert.style.display = 'block';
        
        // Zera stats
        tokenCountSpan.textContent = `Tokens: 0`;
        stopTimerAndShow(0);
        console.error('Erro ao conectar ao backend:', err);
    }
});

// Opcional: envia mensagem com Enter, nova linha com Shift+Enter
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});