/**
 * Sistema Inteligente de Triage - Hospital del Norte
 * JavaScript Principal
 */

document.addEventListener('DOMContentLoaded', function() {

    // =========================================================
    // SIDEBAR TOGGLE (responsive)
    // =========================================================
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });

        // Cerrar sidebar al hacer click fuera (móvil)
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 992 &&
                sidebar.classList.contains('show') &&
                !sidebar.contains(e.target) &&
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }

    // =========================================================
    // RELOJ EN TIEMPO REAL
    // =========================================================
    const reloj = document.getElementById('reloj');
    if (reloj) {
        function actualizarReloj() {
            const ahora = new Date();
            const opciones = {
                weekday: 'short',
                day: '2-digit',
                month: 'short',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };
            reloj.textContent = ahora.toLocaleDateString('es-BO', opciones);
        }
        actualizarReloj();
        setInterval(actualizarReloj, 1000);
    }

    // =========================================================
    // AUTO-DISMISS DE ALERTAS
    // =========================================================
    const alertas = document.querySelectorAll('.alert-dismissible');
    alertas.forEach(function(alerta) {
        setTimeout(function() {
            const btn = alerta.querySelector('.btn-close');
            if (btn) btn.click();
        }, 6000);
    });

});
