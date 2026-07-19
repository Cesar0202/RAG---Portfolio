/* ==========================================
   AI RAG Portfolio - Chat & Messaging Logic
   Message Streaming, Markdown & Admin Unlock
   ========================================== */

// Autoajustar la altura del textarea de chat al escribir
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('input', function() {
            this.style.height = '24px';
            this.style.height = (this.scrollHeight - 4) + 'px';
        });
    }
});

// Enviar chat con tecla Enter
function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// Enviar Mensaje del Chat
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const area = document.getElementById('messages');
    if (!input || !area) return;

    const query = input.value.trim();
    if (!query) return;

    // Interceptar contraseña para acceso administrativo discreto
    try {
        const authResponse = await fetch('/admin/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: query })
        });
        
        if (authResponse.ok) {
            input.value = '';
            input.style.height = '24px';
            
            sessionStorage.setItem('admin_auth', 'true');
            sessionStorage.setItem('admin_pass', query);
            
            const adminBtn = document.getElementById('nav-admin-btn');
            if (adminBtn) adminBtn.style.display = 'flex';
            
            document.getElementById('admin-login').style.display = 'none';
            document.getElementById('admin-dashboard').style.display = 'flex';
            
            loadProjects();
            
            if (adminBtn) {
                switchTab(adminBtn, 'section-admin');
            }
            return;
        }
    } catch (err) {
        console.error("Error al validar contraseña en chat:", err);
    }

    input.value = '';
    input.style.height = '24px';

    appendMessage(query, 'user');
    const loadingBubbleId = appendLoadingBubble();
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: query })
        });

        removeLoadingBubble(loadingBubbleId);

        if (response.ok) {
            const data = await response.json();
            appendMessage(data.response, 'bot', data.sources);
        } else {
            appendMessage("❌ Lo siento, ocurrió un error en el servidor al intentar responder.", 'bot');
        }
    } catch (err) {
        removeLoadingBubble(loadingBubbleId);
        appendMessage(`❌ Error de red: No se pudo conectar con el backend (${err.message}).`, 'bot');
    }
}

// Agregar mensaje en pantalla
function appendMessage(text, sender, sources = []) {
    const area = document.getElementById('messages');
    if (!area) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender === 'user' ? 'message-user' : ''}`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar avatar-${sender}`;
    avatar.innerHTML = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-user-tie"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    
    if (sender === 'bot') {
        bubble.innerHTML = window.marked ? marked.parse(text) : text;
    } else {
        bubble.textContent = text;
    }


    
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    area.appendChild(msgDiv);
    area.scrollTop = area.scrollHeight;
}

// Burbuja de Carga (...)
function appendLoadingBubble() {
    const area = document.getElementById('messages');
    if (!area) return;

    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message';
    msgDiv.id = id;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar avatar-bot';
    avatar.innerHTML = '<i class="fa-solid fa-user-tie"></i>';
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = `
        <div class="typing-loader" style="display: flex; gap: 4px; padding: 4px 8px; align-items: center;">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--text-secondary); animation: pulse 1s infinite alternate;"></span>
            <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--text-secondary); animation: pulse 1s infinite alternate 0.2s;"></span>
            <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--text-secondary); animation: pulse 1s infinite alternate 0.4s;"></span>
        </div>
    `;
    
    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);
    area.appendChild(msgDiv);
    area.scrollTop = area.scrollHeight;
    return id;
}

function removeLoadingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Limpiar el chat actual
function clearChat() {
    const area = document.getElementById('messages');
    if (!area) return;
    area.innerHTML = `
        <div class="message">
            <div class="avatar avatar-bot">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="bubble">
                <p>¡Hola! He limpiado la conversación. ¿En qué te puedo ayudar ahora?</p>
            </div>
        </div>
    `;
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = '';
        input.style.height = '24px';
    }
}
