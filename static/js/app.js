/* ==========================================
   AI RAG Portfolio - Application Core Logic
   Navigation, Theme Toggle & Toast Notifications
   ========================================== */

// Elementos Globales del DOM
let chatInput, messagesArea, fileList, ingestBtn, clearBtn, sendBtn, toast;

document.addEventListener('DOMContentLoaded', () => {
    chatInput = document.getElementById('chat-input');
    messagesArea = document.getElementById('messages');
    fileList = document.getElementById('file-list');
    ingestBtn = document.getElementById('ingest-btn');
    clearBtn = document.getElementById('clear-btn');
    sendBtn = document.getElementById('send-btn');
    toast = document.getElementById('toast');

    // Inicializaciones
    loadFiles();
    checkAdminSession();
});

// Navegación entre Pestañas (SPA)
function switchTab(navElement, tabId) {
    document.querySelectorAll('.nav-icon').forEach(icon => {
        icon.classList.remove('active');
    });
    navElement.classList.add('active');

    document.querySelectorAll('.tab-content').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');

    const workspaceTitle = document.getElementById('workspace-title');
    if (tabId === 'section-chat') {
        workspaceTitle.innerHTML = 'RAG Engine <span>Chat</span>';
    } else if (tabId === 'section-projects') {
        workspaceTitle.innerHTML = 'RAG Engine <span>Proyectos</span>';
        loadProjects();
    } else if (tabId === 'section-skills') {
        workspaceTitle.innerHTML = 'RAG Engine <span>Skills</span>';
    } else if (tabId === 'section-feedback') {
        workspaceTitle.innerHTML = 'RAG Engine <span>Contacto</span>';
    } else if (tabId === 'section-admin') {
        workspaceTitle.innerHTML = 'RAG Engine <span>Administración</span>';
    }
}


// Toast Notifications
function showToast(message, type = "success") {
    const toastEl = document.getElementById('toast') || toast;
    const icon = document.getElementById('toast-icon');
    const msg = document.getElementById('toast-message');
    if (!toastEl || !icon || !msg) return;
    
    toastEl.className = `toast toast-${type}`;
    msg.textContent = message;
    
    if (type === "success") {
        icon.className = "fa-solid fa-circle-check";
        icon.style.color = "var(--accent-green)";
    } else if (type === "error") {
        icon.className = "fa-solid fa-circle-xmark";
        icon.style.color = "var(--danger-color)";
    } else {
        icon.className = "fa-solid fa-circle-info";
        icon.style.color = "var(--accent-purple)";
    }
    
    toastEl.classList.add('show');
    setTimeout(() => {
        toastEl.classList.remove('show');
    }, 4000);
}

// Helper para Estados de Carga en Botones
function setLoadingState(btnEl, isLoading, text) {
    if (!btnEl) return;
    btnEl.disabled = isLoading;
    btnEl.innerHTML = text;
}

// Enviar sugerencia preestablecida
function sendSuggestion(question) {
    const chatTabIcon = document.querySelector('.nav-icon[onclick*="section-chat"]');
    if (chatTabIcon) {
        switchTab(chatTabIcon, 'section-chat');
    }
    
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = question;
        input.style.height = '24px';
        input.style.height = (input.scrollHeight - 4) + 'px';
        sendMessage();
    }
}
