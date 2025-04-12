// Constants
const API_BASE_URL = 'http://localhost:5000/api';
const TOKEN_KEY = 'gold_trader_token';
const USER_KEY = 'gold_trader_user';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const errorModal = document.getElementById('errorModal');
const errorModalMessage = document.getElementById('errorModalMessage');
const closeErrorModal = document.getElementById('closeErrorModal');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        redirectToDashboard();
    }

    // Setup event listeners
    loginForm.addEventListener('submit', handleLogin);
    closeErrorModal.addEventListener('click', () => {
        errorModal.classList.add('hidden');
    });
});

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }

        // Store token and user data
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify({
            id: data.user_id,
            username: data.username
        }));

        // Redirect to dashboard
        redirectToDashboard();

    } catch (error) {
        showError(error.message);
    }
}

// Show error modal
function showError(message) {
    errorModalMessage.textContent = message;
    errorModal.classList.remove('hidden');
}

// Redirect to dashboard
function redirectToDashboard() {
    window.location.href = 'index.html';
}

// Utility function to check if token is expired
function isTokenExpired(token) {
    if (!token) return true;

    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const expiryTime = payload.exp * 1000; // Convert to milliseconds
        return Date.now() >= expiryTime;
    } catch (error) {
        console.error('Error checking token expiry:', error);
        return true;
    }
}

// Handle network errors
window.addEventListener('offline', () => {
    showError('Network connection lost. Please check your internet connection.');
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

// Add input validation
document.getElementById('username').addEventListener('input', function(e) {
    this.value = this.value.trim();
    validateInput(this, 'Username must be at least 3 characters long', value => value.length >= 3);
});

document.getElementById('password').addEventListener('input', function(e) {
    validateInput(this, 'Password must be at least 6 characters long', value => value.length >= 6);
});

function validateInput(element, errorMessage, validationFn) {
    const isValid = validationFn(element.value);
    element.classList.toggle('border-red-500', !isValid);
    
    // Find or create error message element
    let errorElement = element.parentElement.querySelector('.error-message');
    if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.className = 'error-message text-red-500 text-xs mt-1';
        element.parentElement.appendChild(errorElement);
    }
    
    errorElement.textContent = isValid ? '' : errorMessage;
}

// Add loading state to login button
loginForm.addEventListener('submit', function() {
    const submitButton = this.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <i class="fas fa-spinner fa-spin mr-2"></i>
        Signing In...
    `;
});

// Security measures
document.addEventListener('contextmenu', function(e) {
    if (process.env.NODE_ENV === 'production') {
        e.preventDefault(); // Disable right-click in production
    }
});

// Prevent multiple rapid login attempts
let lastLoginAttempt = 0;
const MIN_LOGIN_INTERVAL = 2000; // 2 seconds

loginForm.addEventListener('submit', function(event) {
    const now = Date.now();
    if (now - lastLoginAttempt < MIN_LOGIN_INTERVAL) {
        event.preventDefault();
        showError('Please wait a moment before trying again');
        return;
    }
    lastLoginAttempt = now;
});

// Clear sensitive data when leaving the page
window.addEventListener('beforeunload', () => {
    document.getElementById('password').value = '';
});

// Handle session timeout
let sessionTimeout;

function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    sessionTimeout = setTimeout(() => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token && isTokenExpired(token)) {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            window.location.href = 'login.html?session=expired';
        }
    }, 30 * 60 * 1000); // 30 minutes
}

// Reset timeout on user activity
['click', 'keypress', 'scroll', 'mousemove'].forEach(event => {
    document.addEventListener(event, resetSessionTimeout);
});

// Check for session expired parameter
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('session') === 'expired') {
        showError('Your session has expired. Please log in again.');
    }
});
