/**
 * Centralized notification utility
 * Replaces alert() calls with better UX
 */

export function showNotification(message, type = 'info') {
  if (typeof document === 'undefined' || !document.body) return;
  
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  
  const bgColor = type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#2196F3';
  
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    background: ${bgColor};
    color: white;
    border-radius: 4px;
    z-index: 10000;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px;
    max-width: 400px;
    word-wrap: break-word;
  `;
  
  document.body.appendChild(notification);
  
  // Auto-remove after 3 seconds
  setTimeout(() => {
    notification.style.opacity = '0';
    notification.style.transition = 'opacity 0.3s';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

