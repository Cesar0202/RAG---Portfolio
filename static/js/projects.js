/* ==========================================
   AI RAG Portfolio - Projects Management Logic
   Fetch, Add, Edit (PUT), Delete Projects & Base64
   ========================================== */

// Cargar proyectos desde el backend
async function loadProjects() {
    const grid = document.getElementById('projects-grid');
    if (!grid) return;

    try {
        const response = await fetch('/projects');
        if (response.ok) {
            const projects = await response.json();
            window.loadedProjectsList = projects;
            if (projects.length === 0) {
                grid.innerHTML = `<p style="color: var(--text-secondary); text-align: center; grid-column: span 2; padding: 2rem;">No hay proyectos publicados aún.</p>`;
                return;
            }
            grid.innerHTML = projects.map((proj, idx) => {
                const techs = proj.technologies.split(',').map(t => t.trim());
                const hasImg = proj.image ? true : false;
                const cardStyle = hasImg ? `style="background-image: linear-gradient(to bottom, rgba(21, 22, 25, 0.45) 0%, rgba(21, 22, 25, 0.96) 100%), url(${proj.image}); background-size: cover; background-position: center; min-height: 220px;"` : '';
                
                const isAdmin = sessionStorage.getItem('admin_auth') === 'true';
                const deleteBtnHTML = isAdmin ? `
                    <button class="btn-delete-project" onclick="deleteProject(${idx})" title="Eliminar Proyecto">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                ` : '';
                const editBtnHTML = isAdmin ? `
                    <button class="btn-edit-project" onclick="startEditProject(${idx})" title="Editar Proyecto">
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                ` : '';
                
                return `
                    <div class="project-card-wrapper">
                        ${editBtnHTML}
                        ${deleteBtnHTML}
                        <div class="project-card-inner">
                            
                            <!-- Lado Frontal: Imagen y Título -->
                            <div class="project-card-front" style="${hasImg ? `background-image: linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.85) 100%), url(${proj.image});` : ''}">
                                <h4 style="color: ${hasImg ? '#ffffff' : 'var(--text-primary)'}; text-shadow: ${hasImg ? '0 2px 4px rgba(0,0,0,0.8)' : 'none'}; margin: 0;">${proj.title}</h4>
                            </div>

                            <!-- Lado Trasero: Descripción, Tecnologías y Enlaces -->
                            <div class="project-card-back">
                                <h4 style="color: var(--text-primary); margin-bottom: 0.25rem;">${proj.title}</h4>
                                <p class="project-desc" style="flex: 1;">${proj.description}</p>
                                
                                <div class="project-techs" style="margin-top: auto; margin-bottom: 1rem;">
                                    ${techs.map(t => `<span class="tech-badge">${t}</span>`).join('')}
                                </div>
                                
                                ${(proj.github || proj.demo) ? `
                                    <div style="display: flex; gap: 0.5rem; width: 100%;">
                                        ${proj.github ? `
                                            <a href="${proj.github}" target="_blank" class="project-link-btn" style="flex: 1; justify-content: center;">
                                                <i class="fa-brands fa-github"></i> GitHub
                                            </a>
                                        ` : ''}
                                        ${proj.demo ? `
                                            <a href="${proj.demo}" target="_blank" class="project-link-btn" style="flex: 1; justify-content: center;">
                                                <i class="fa-solid fa-globe"></i> Demo
                                            </a>
                                        ` : ''}
                                    </div>
                                ` : ''}
                            </div>

                        </div>
                    </div>
                `;
            }).join('');
        }
    } catch (err) {
        grid.innerHTML = `<p style="color: var(--danger-color); text-align: center; grid-column: span 2; padding: 2rem;">Error al conectar con la base de datos de proyectos.</p>`;
    }
}

// Convierte un archivo de imagen a Base64 y lo redimensiona/comprime
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = (event) => {
            const img = new Image();
            img.onload = () => {
                const maxWidth = 800;
                const maxHeight = 800;
                let width = img.width;
                let height = img.height;

                if (width > maxWidth || height > maxHeight) {
                    if (width > height) {
                        height = Math.round(height * (maxWidth / width));
                        width = maxWidth;
                    } else {
                        width = Math.round(width * (maxHeight / height));
                        height = maxHeight;
                    }
                }

                const canvas = document.createElement('canvas');
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);

                // Comprimir como JPEG para reducir drásticamente el peso
                resolve(canvas.toDataURL('image/jpeg', 0.8));
            };
            img.onerror = error => reject(error);
            img.src = event.target.result;
        };
        reader.onerror = error => reject(error);
    });
}

// Publicar o Editar Proyecto desde Panel Admin (POST o PUT)
async function submitNewProject(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('proj-submit-btn');
    const originalHTML = submitBtn.innerHTML;
    
    const editIndex = document.getElementById('proj-edit-index').value;
    const isEdit = editIndex !== "";
    const url = isEdit ? `/projects/${editIndex}` : '/projects';
    const method = isEdit ? 'PUT' : 'POST';

    const title = document.getElementById('proj-title').value;
    const description = document.getElementById('proj-desc').value;
    const technologies = document.getElementById('proj-techs').value;
    const github = document.getElementById('proj-github').value;
    const demo = document.getElementById('proj-demo').value;
    
    const fileInput = document.getElementById('proj-image');
    let imageBase64 = "";

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Guardando...';

    try {
        if (fileInput && fileInput.files.length > 0) {
            const file = fileInput.files[0];
            imageBase64 = await fileToBase64(file);
        }

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                title, 
                description, 
                technologies, 
                github, 
                demo, 
                image: imageBase64 
            })
        });

        if (response.ok) {
            showToast(isEdit ? "¡Proyecto actualizado con éxito!" : "¡Proyecto publicado con éxito!", "success");
            cancelProjectEdit();
            loadProjects();
        } else {
            showToast(isEdit ? "Error al actualizar el proyecto." : "Error al publicar el proyecto.", "error");
        }
    } catch (err) {
        showToast(`Error al conectar con la API: ${err.message}`, "error");
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = isEdit ? '<i class="fa-solid fa-arrows-rotate"></i> Actualizar Proyecto' : originalHTML;
    }
}

// Iniciar edición de un proyecto
function startEditProject(index) {
    if (!window.loadedProjectsList || !window.loadedProjectsList[index]) return;
    const proj = window.loadedProjectsList[index];

    document.getElementById('proj-edit-index').value = index;
    document.getElementById('proj-title').value = proj.title || '';
    document.getElementById('proj-desc').value = proj.description || '';
    document.getElementById('proj-techs').value = proj.technologies || '';
    document.getElementById('proj-github').value = proj.github || '';
    document.getElementById('proj-demo').value = proj.demo || '';

    const submitBtn = document.getElementById('proj-submit-btn');
    if (submitBtn) submitBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Actualizar Proyecto';

    const cancelBtn = document.getElementById('proj-cancel-btn');
    if (cancelBtn) cancelBtn.style.display = 'block';

    const adminBtn = document.getElementById('nav-admin-btn');
    if (adminBtn) switchTab(adminBtn, 'section-admin');
    showToast(`Editando proyecto: "${proj.title}"`, "info");
}

// Cancelar edición de un proyecto
function cancelProjectEdit() {
    document.getElementById('proj-edit-index').value = '';
    const form = document.getElementById('admin-project-form');
    if (form) form.reset();

    const submitBtn = document.getElementById('proj-submit-btn');
    if (submitBtn) submitBtn.innerHTML = '<i class="fa-solid fa-circle-plus"></i> Publicar Proyecto';

    const cancelBtn = document.getElementById('proj-cancel-btn');
    if (cancelBtn) cancelBtn.style.display = 'none';
}

// Eliminar un proyecto del portafolio
async function deleteProject(index) {
    if (!confirm("¿Estás seguro de que deseas eliminar este proyecto del portafolio?")) {
        return;
    }
    try {
        const response = await fetch(`/projects/${index}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            showToast("Proyecto eliminado con éxito.", "success");
            loadProjects();
        } else {
            showToast("Error al eliminar el proyecto.", "error");
        }
    } catch (err) {
        showToast(`Error al conectar con la API: ${err.message}`, "error");
    }
}
