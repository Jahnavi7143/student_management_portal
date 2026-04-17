// // SecureLearn — JS helpers

// // Click on restricted code tags to navigate
// document.querySelectorAll('.restricted-links code').forEach(el => {
//     el.addEventListener('click', () => {
//         window.location.href = el.textContent.trim();
//     });
// });

// // Auto-dismiss alerts after 5 seconds
// document.querySelectorAll('.alert').forEach(el => {
//     setTimeout(() => {
//         el.style.transition = 'opacity 0.5s';
//         el.style.opacity = '0';
//         setTimeout(() => el.remove(), 500);
//     }, 5000);
// });

// // Highlight active nav link on page load
// const path = window.location.pathname;
// document.querySelectorAll('.nav-link').forEach(link => {
//     if (link.getAttribute('href') === path) {
//         link.classList.add('active');
//     }
// });

// Auto-dismiss alerts after 5 seconds
document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
        el.style.transition = 'opacity 0.4s';
        el.style.opacity = '0';
        setTimeout(() => el.remove(), 400);
    }, 5000);
});