/* ==========================================
   AI RAG Portfolio - Feedback & Contact Logic
   ========================================== */

// Enviar formulario de contacto/comentarios
async function submitFeedback(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('fb-submit-btn');
    const originalHTML = submitBtn ? submitBtn.innerHTML : '';
    
    const name = document.getElementById('fb-name').value;
    const email = document.getElementById('fb-email').value;
    const message = document.getElementById('fb-message').value;

    setLoadingState(submitBtn, true, '<i class="fa-solid fa-spinner fa-spin"></i> Enviando...');

    try {
        const response = await fetch('/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, message })
        });

        if (response.ok) {
            showToast("¡Mensaje enviado con éxito! Gracias por tus comentarios.", "success");
            document.getElementById('feedback-form').reset();
        } else {
            showToast("Error al enviar el mensaje. Inténtalo de nuevo.", "error");
        }
    } catch (err) {
        showToast(`Error de conexión: ${err.message}`, "error");
    } finally {
        setLoadingState(submitBtn, false, originalHTML);
    }
}
