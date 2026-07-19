/* ==========================================
   AI RAG Portfolio - Admin Panel Logic
   Auth, Document Upload, Ingest & Database Clear
   ========================================== */

// Verificar contraseña de Administrador
async function verifyAdminPassword() {
    const passwordInput = document.getElementById('admin-password');
    if (!passwordInput) return;
    const password = passwordInput.value;
    
    if (!password) {
        showToast("Por favor, ingresa una contraseña.", "error");
        return;
    }

    try {
        const response = await fetch('/admin/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            showToast("Panel administrativo desbloqueado con éxito.", "success");
            
            document.getElementById('admin-login').style.display = 'none';
            document.getElementById('admin-dashboard').style.display = 'flex';
            
            sessionStorage.setItem('admin_auth', 'true');
            sessionStorage.setItem('admin_pass', password);
            
            const adminBtn = document.getElementById('nav-admin-btn');
            if (adminBtn) adminBtn.style.display = 'flex';
            
            loadProjects();
            loadFiles();
        } else {
            showToast("Contraseña incorrecta. Inténtalo de nuevo.", "error");
            passwordInput.value = '';
        }
    } catch (err) {
        showToast(`Error de conexión: ${err.message}`, "error");
    }
}

// Enviar login con Enter
function handleAdminLoginKey(e) {
    if (e.key === 'Enter') {
        verifyAdminPassword();
    }
}

// Cerrar sesión
function logoutAdmin() {
    sessionStorage.removeItem('admin_auth');
    sessionStorage.removeItem('admin_pass');
    
    const dashboard = document.getElementById('admin-dashboard');
    const login = document.getElementById('admin-login');
    const passInput = document.getElementById('admin-password');
    
    if(dashboard) dashboard.style.display = 'none';
    if(login) login.style.display = 'block';
    if(passInput) passInput.value = '';
    
    showToast("Sesión cerrada.", "success");
    
    // Regresar al inicio
    const chatBtn = document.querySelector('.nav-icon[onclick*="section-chat"]');
    if (chatBtn) {
        switchTab(chatBtn, 'section-chat');
    }
}

// Verificar sesión administrativa activa
function checkAdminSession() {
    const isAuth = sessionStorage.getItem('admin_auth');
    const adminBtn = document.getElementById('nav-admin-btn');
    if (isAuth === 'true') {
        document.getElementById('admin-login').style.display = 'none';
        document.getElementById('admin-dashboard').style.display = 'flex';
        if (adminBtn) adminBtn.style.display = 'flex';
    } else {
        if (adminBtn) adminBtn.style.display = 'none';
    }
}

// Cargar archivos indexados
async function loadFiles() {
    const fileListEl = document.getElementById('file-list');
    if (!fileListEl) return;

    try {
        const response = await fetch('/files');
        if (response.ok) {
            const data = await response.json();
            const files = data.files || [];
            
            if (files.length === 0) {
                fileListEl.innerHTML = `<li class="empty-files">No hay archivos indexados.<br>Usa el botón superior para indexar PDFs.</li>`;
            } else {
                fileListEl.innerHTML = files.map(file => `
                    <li class="file-item">
                        <i class="fa-solid fa-file-pdf"></i>
                        <span>${file}</span>
                    </li>
                `).join('');
            }
        }
    } catch (err) {
        console.error("Error al cargar archivos:", err);
        fileListEl.innerHTML = `<li class="empty-files" style="color: var(--danger-color);">Error de conexión</li>`;
    }
}

// Subir archivo e ingestar automáticamente
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const uploadBtn = document.getElementById('upload-btn');
    const originalHTML = uploadBtn ? uploadBtn.innerHTML : '';
    
    setLoadingState(uploadBtn, true, '<i class="fa-solid fa-spinner fa-spin"></i> Subiendo...');
    showToast(`Subiendo archivo: ${file.name}...`, "info");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            showToast(`Archivo "${file.name}" subido. Iniciando ingesta automática...`, "success");
            await triggerIngest();
        } else {
            const errData = await response.json();
            showToast(`Error al subir archivo: ${errData.detail || 'Error desconocido'}`, "error");
        }
    } catch (err) {
        showToast(`Error al conectar con el servidor: ${err.message}`, "error");
    } finally {
        setLoadingState(uploadBtn, false, originalHTML);
        event.target.value = '';
    }
}

// Ingestar documentos en la base de datos vectorial ChromaDB
async function triggerIngest() {
    const btn = document.getElementById('ingest-btn');
    setLoadingState(btn, true, '<i class="fa-solid fa-spinner fa-spin"></i> Ingestando...');
    showToast("Iniciando ingesta de documentos...", "info");
    
    try {
        const response = await fetch('/ingest', { method: 'POST' });
        if (response.ok) {
            const data = await response.json();
            showToast(`¡Ingesta completada! ${data.processed_files_count} archivos procesados.`, "success");
            loadFiles();
        } else {
            showToast("Error en el backend al procesar la ingesta.", "error");
        }
    } catch (err) {
        showToast(`Error al conectar con la API: ${err.message}`, "error");
    } finally {
        setLoadingState(btn, false, '<i class="fa-solid fa-arrows-rotate"></i> Ingestar Documentos');
    }
}

// Vaciar la base de datos de conocimiento
async function triggerClear() {
    if (!confirm("¿Estás seguro de que quieres borrar todo el conocimiento indexado? Esta acción no se puede deshacer.")) {
        return;
    }
    
    const btn = document.getElementById('clear-btn');
    setLoadingState(btn, true, '<i class="fa-solid fa-spinner fa-spin"></i> Borrando...');
    try {
        const response = await fetch('/clear', { method: 'POST' });
        if (response.ok) {
            showToast("Base de datos vectorial vaciada correctamente.", "success");
            loadFiles();
        } else {
            showToast("Error al vaciar la base de datos.", "error");
        }
    } catch (err) {
        showToast(`Error de conexión: ${err.message}`, "error");
    } finally {
        setLoadingState(btn, false, '<i class="fa-solid fa-trash-can"></i> Vaciar Base de Datos');
    }
}
