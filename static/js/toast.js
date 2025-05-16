/**
 * toast.js - Central notification system for the Aplikasi Uji Emisi
 */

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - success, error, info, warning
 * @param {number} duration - Duration in ms
 */
function showToast(message, type = 'success', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'fixed top-4 right-4 z-50 flex flex-col items-end';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `mb-3 p-4 rounded-md shadow-md flex items-center transition-all transform translate-x-0 ${
        type === 'success' ? 'bg-green-100 text-green-800 border-l-4 border-green-500' : 
        type === 'error' ? 'bg-red-100 text-red-800 border-l-4 border-red-500' : 
        type === 'warning' ? 'bg-yellow-100 text-yellow-800 border-l-4 border-yellow-500' :
        'bg-blue-100 text-blue-800 border-l-4 border-blue-500'
    }`;
    
    // Add icon based on type
    const iconClass = type === 'success' ? 'fa-check-circle' : 
                     type === 'error' ? 'fa-exclamation-circle' : 
                     type === 'warning' ? 'fa-exclamation-triangle' :
                     'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fas ${iconClass} mr-2"></i>
        <span>${message}</span>
        <button class="ml-auto text-gray-600 hover:text-gray-800 focus:outline-none">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add close functionality
    const closeButton = toast.querySelector('button');
    closeButton.addEventListener('click', () => {
        toast.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => toast.remove(), 300);
    });
    
    // Add animation
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after duration
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, duration);
} 