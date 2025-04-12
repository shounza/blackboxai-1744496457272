// Constants
const API_BASE_URL = 'http://localhost:5000/api';
const TOKEN_KEY = 'gold_trader_token';
const USER_KEY = 'gold_trader_user';

// DOM Elements
const registerForm = document.getElementById('registerForm');
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
    registerForm.addEventListener('submit', handleRegistration);
    closeErrorModal.addEventListener('click', () => {
        errorModal.classList.add('hidden');
    });

    // Setup input validation
    setupInputValidation();
});

// Handle registration form submission
async function handleRegistration(event) {
    event.preventDefault();

    // Get form values
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const apiKey = document.getElementById('apiKey').value;
    const apiSecret = document.getElementById('apiSecret').value;

    // Validate passwords match
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    // Validate password strength
    if (!isPasswordStrong(password)) {
        showError('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password,
                api_key: apiKey,
                api_secret: apiSecret
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Registration failed');
        }

        // Show success message
        showSuccess('Registration successful! Redirecting to login...');

        // Redirect to login page after a short delay
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);

    } catch (error) {
        showError(error.message);
    }
}

// Input validation setup
function setupInputValidation() {
    // Username validation
    document.getElementById('username').addEventListener('input', function(e) {
        this.value = this.value.trim();
        validateInput(this, 'Username must be at least 3 characters long', value => value.length >= 3);
    });

    // Email validation
    document.getElementById('email').addEventListener('input', function(e) {
        validateInput(this, 'Please enter a valid email address', value => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(value);
        });
    });

    // Password validation
    document.getElementById('password').addEventListener('input', function(e) {
        validateInput(this, 'Password must meet strength requirements', isPasswordStrong);
    });

    // Confirm password validation
    document.getElementById('confirmPassword').addEventListener('input', function(e) {
        const password = document.getElementById('password').value;
        validateInput(this, 'Passwords must match', value => value === password);
    });

    // API Key validation
    document.getElementById('apiKey').addEventListener('input', function(e) {
        this.value = this.value.trim();
        validateInput(this, 'API Key is required', value => value.length > 0);
    });

    // API Secret validation
    document.getElementById('apiSecret').addEventListener('input', function(e) {
        this.value = this.value.trim();
        validateInput(this, 'API Secret is required', value => value.length > 0);
    });
}

// Validate individual input
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
    return isValid;
}

// Password strength validation
function isPasswordStrong(password) {
    const minLength = 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    return (
        password.length >= minLength &&
        hasUpperCase &&
        hasLowerCase &&
        hasNumbers &&
        hasSpecialChar
    );
}

// Show error modal
function showError(message) {
    errorModalMessage.textContent = message;
    errorModal.classList.remove('hidden');
}

// Show success message
function showSuccess(message) {
    const successModal = document.createElement('div');
    successModal.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg';
    successModal.textContent = message;
    document.body.appendChild(successModal);

    setTimeout(() => {
        successModal.remove();
    }, 3000);
}

// Redirect to dashboard
function redirectToDashboard() {
    window.location.href = 'index.html';
}

// Handle network errors
window.addEventListener('offline', () => {
    showError('Network connection lost. Please check your internet connection.');
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}

// Add loading state to register button
registerForm.addEventListener('submit', function() {
    const submitButton = this.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.innerHTML = `
        <i class="fas fa-spinner fa-spin mr-2"></i>
        Creating Account...
    `;
});

// Security measures
document.addEventListener('contextmenu', function(e) {
    if (process.env.NODE_ENV === 'production') {
        e.preventDefault(); // Disable right-click in production
    }
});

// Prevent multiple rapid registration attempts
let lastRegistrationAttempt = 0;
const MIN_REGISTRATION_INTERVAL = 2000; // 2 seconds

registerForm.addEventListener('submit', function(event) {
    const now = Date.now();
    if (now - lastRegistrationAttempt < MIN_REGISTRATION_INTERVAL) {
        event.preventDefault();
        showError('Please wait a moment before trying again');
        return;
    }
    lastRegistrationAttempt = now;
});

// Clear sensitive data when leaving the page
window.addEventListener('beforeunload', () => {
    document.getElementById('password').value = '';
    document.getElementById('confirmPassword').value = '';
    document.getElementById('apiSecret').value = '';
});
