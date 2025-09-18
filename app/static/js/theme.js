/**
 * Technical Analyst - Theme JavaScript
 * Provides common functionality across all pages
 */

// Theme utilities and common functions
const Theme = {
    // Notification system
    showNotification: function(message, type = 'info', duration = 5000) {
        // Remove existing notification
        const existing = document.querySelector('.notification');
        if (existing) {
            existing.remove();
        }

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification alert alert-${type}`;
        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()"
                        style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; margin-left: 15px;">
                    <span class="material-icons" style="font-size: 20px;">close</span>
                </button>
            </div>
        `;

        // Add to page
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
        }

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    },

    // Loading state management
    setLoading: function(element, loading = true) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }

        if (!element) return;

        if (loading) {
            element.disabled = true;
            const originalText = element.innerHTML;
            element.dataset.originalText = originalText;
            element.innerHTML = `
                <span class="material-icons" style="animation: spin 1s linear infinite; font-size: 18px;">refresh</span>
                Loading...
            `;
        } else {
            element.disabled = false;
            element.innerHTML = element.dataset.originalText || element.innerHTML;
        }
    },

    // Form validation helpers
    validateRequired: function(selector) {
        const element = document.querySelector(selector);
        if (!element) return false;

        const value = element.value.trim();
        if (!value) {
            element.style.borderColor = 'var(--danger-color)';
            return false;
        }

        element.style.borderColor = '';
        return true;
    },

    // API request helper
    request: async function(url, options = {}) {
        const defaults = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const config = { ...defaults, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    // Format numbers with commas
    formatNumber: function(num) {
        return new Intl.NumberFormat().format(num);
    },

    // Format date
    formatDate: function(dateString) {
        if (!dateString || dateString === 'Never') return 'Never';
        try {
            return new Date(dateString).toLocaleString();
        } catch (error) {
            return dateString;
        }
    },

    // Exchange segment helper
    getExchangeName: function(segment) {
        const names = {
            'nse_cm': 'NSE Cash Market',
            'bse_cm': 'BSE Cash Market',
            'nse_fo': 'NSE F&O',
            'bse_fo': 'BSE F&O',
            'cde_fo': 'Currency Derivatives',
            'mcx_fo': 'MCX Derivatives'
        };
        return names[segment] || segment;
    },

    // Local storage helpers
    storage: {
        get: function(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                console.error('Error reading from localStorage:', error);
                return defaultValue;
            }
        },

        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                console.error('Error writing to localStorage:', error);
                return false;
            }
        },

        remove: function(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.error('Error removing from localStorage:', error);
                return false;
            }
        }
    }
};

// Add spinning animation to CSS if not already present
if (!document.querySelector('#theme-animations')) {
    const style = document.createElement('style');
    style.id = 'theme-animations';
    style.textContent = `
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 300px;
            max-width: 500px;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }

    // Initialize navigation active states
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Add click handlers for buttons with loading states
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-loading]')) {
            const button = e.target.closest('[data-loading]');
            if (!button.disabled) {
                Theme.setLoading(button, true);

                // Auto-reset after 10 seconds if not manually reset
                setTimeout(() => {
                    if (button.disabled) {
                        Theme.setLoading(button, false);
                    }
                }, 10000);
            }
        }
    });
});

// Global error handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    Theme.showNotification('An unexpected error occurred. Please try again.', 'error');
});

// Export theme for global access
window.Theme = Theme;