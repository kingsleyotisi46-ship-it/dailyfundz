// DAILYFUNDZBOOST - Main JavaScript

// Toggle user dropdown menu
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('show');
}

// Toggle mobile menu
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    menu.classList.toggle('show');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('userDropdown');
    
    if (userMenu && !userMenu.contains(e.target) && dropdown) {
        dropdown.classList.remove('show');
    }
    
    const mobileBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileBtn && !mobileBtn.contains(e.target) && mobileMenu && !mobileMenu.contains(e.target)) {
        mobileMenu.classList.remove('show');
    }
});

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Format currency
function formatCurrency(amount, currency = 'NGN') {
    const symbol = currency === 'NGN' ? '₦' : '$';
    return symbol + parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Calculate service price
function calculatePrice(pricePerK, quantity) {
    return (pricePerK / 1000) * quantity;
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(10, 10, 18, 0.98)';
    } else {
        navbar.style.background = 'rgba(15, 15, 26, 0.95)';
    }
});

// Image preview for file uploads
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!', 'success');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const container = document.querySelector('.messages-container') || createMessagesContainer();
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">&times;</button>`;
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

function createMessagesContainer() {
    const container = document.createElement('div');
    container.className = 'messages-container';
    document.body.appendChild(container);
    return container;
}

// Quantity input validation
document.addEventListener('DOMContentLoaded', function() {
    const quantityInputs = document.querySelectorAll('input[name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const min = parseInt(this.min) || 0;
            const max = parseInt(this.max) || Infinity;
            let value = parseInt(this.value) || min;
            
            if (value < min) value = min;
            if (value > max) value = max;
            
            this.value = value;
        });
    });
});
