const express = require('express');
const bodyParser = require('body-parser');
const fetch = require('node-fetch');
const cors = require('cors');

const app = express();
const PORT = 3000; // ajuste se necessário

app.use(cors());
app.use(bodyParser.json());

app.post('/chat', async (req, res) => {
    const { message } = req.body;
    if (!message) {
        return res.status(400).json({ response: 'Mensagem não fornecida.' });
    }

    try {
        // Envia para o Ollama local
        const ollamaRes = await fetch('http://localhost:11434/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: 'gemma3n:e4b',
                prompt: message,
                stream: false
            })
        });
        const data = await ollamaRes.json();
        res.json({ response: data.response });
    } catch (err) {
        res.status(500).json({ response: 'Erro ao conectar ao Ollama.' });
    }
});

app.listen(PORT, () => {
    console.log(`Servidor rodando em http://localhost:${PORT}`);
});
