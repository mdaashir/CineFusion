/**
 * Password and Authentication Management
 * Handles login functionality, password validation, and user session management
 */

// Configuration
const CONFIG = {
	minPasswordLength: 8,
	maxLoginAttempts: 3,
	lockoutDuration: 15 * 60 * 1000, // 15 minutes in milliseconds
	rememberMeDuration: 7 * 24 * 60 * 60 * 1000, // 7 days in milliseconds
};

// Temporary user storage (In production, this would be handled by a backend API)
const TEMP_USERS = {
	demo: {
		password: 'password123',
		email: 'demo@cinefusion.com',
		loginAttempts: 0,
		lockedUntil: null,
	},
};

/**
 * Initialize the login form
 */
function initializeLogin() {
	const loginForm = document.getElementById('login-form');
	const rememberCheckbox = document.getElementById('remember');

	if (loginForm) {
		loginForm.addEventListener('submit', handleLogin);

		// Check if user is already logged in
		checkExistingSession();

		// Add real-time validation
		const passwordInput = document.getElementById('password');
		if (passwordInput) {
			passwordInput.addEventListener('input', validatePasswordInput);
		}

		// Load remembered username if available
		loadRememberedCredentials();
	}
}

/**
 * Handle login form submission
 * @param {Event} event - Form submit event
 */
async function handleLogin(event) {
	event.preventDefault();

	const username = document.getElementById('username').value.trim();
	const password = document.getElementById('password').value;
	const rememberMe = document.getElementById('remember')?.checked || false;

	// Validate inputs
	if (!validateLoginInputs(username, password)) {
		return;
	}

	// Show loading state
	showLoading(true);

	try {
		// Simulate API call delay
		await new Promise((resolve) => setTimeout(resolve, 1000));

		// Authenticate user
		const authResult = authenticateUser(username, password);

		if (authResult.success) {
			// Handle successful login
			handleSuccessfulLogin(username, rememberMe);
		} else {
			// Handle failed login
			handleFailedLogin(username, authResult.message);
		}
	} catch (error) {
		console.error('Login error:', error);
		showAlert('An unexpected error occurred. Please try again.', 'error');
	} finally {
		showLoading(false);
	}
}

/**
 * Validate login inputs
 * @param {string} username - Username input
 * @param {string} password - Password input
 * @returns {boolean} - Whether inputs are valid
 */
function validateLoginInputs(username, password) {
	let isValid = true;

	// Clear previous errors
	clearFieldErrors();

	// Validate username
	if (!username) {
		showFieldError('username', 'Username is required');
		isValid = false;
	} else if (username.length < 3) {
		showFieldError('username', 'Username must be at least 3 characters');
		isValid = false;
	}

	// Validate password
	if (!password) {
		showFieldError('password', 'Password is required');
		isValid = false;
	} else if (password.length < CONFIG.minPasswordLength) {
		showFieldError(
			'password',
			`Password must be at least ${CONFIG.minPasswordLength} characters`
		);
		isValid = false;
	}

	return isValid;
}

/**
 * Authenticate user credentials
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Object} - Authentication result
 */
function authenticateUser(username, password) {
	const user = TEMP_USERS[username.toLowerCase()];

	if (!user) {
		return { success: false, message: 'Invalid username or password' };
	}

	// Check if account is locked
	if (user.lockedUntil && new Date() < user.lockedUntil) {
		const remainingTime = Math.ceil(
			(user.lockedUntil - new Date()) / 1000 / 60
		);
		return {
			success: false,
			message: `Account locked. Try again in ${remainingTime} minutes.`,
		};
	}

	// Verify password
	if (user.password === password) {
		// Reset login attempts on successful login
		user.loginAttempts = 0;
		user.lockedUntil = null;
		return { success: true, message: 'Login successful' };
	} else {
		// Increment login attempts
		user.loginAttempts = (user.loginAttempts || 0) + 1;

		if (user.loginAttempts >= CONFIG.maxLoginAttempts) {
			user.lockedUntil = new Date(Date.now() + CONFIG.lockoutDuration);
			return {
				success: false,
				message: `Too many failed attempts. Account locked for 15 minutes.`,
			};
		}

		const remainingAttempts = CONFIG.maxLoginAttempts - user.loginAttempts;
		return {
			success: false,
			message: `Invalid username or password. ${remainingAttempts} attempts remaining.`,
		};
	}
}

/**
 * Handle successful login
 * @param {string} username - Username
 * @param {boolean} rememberMe - Whether to remember user
 */
function handleSuccessfulLogin(username, rememberMe) {
	// Store session data
	const sessionData = {
		username: username,
		loginTime: new Date().toISOString(),
		rememberMe: rememberMe,
	};

	// Store in appropriate storage
	if (rememberMe) {
		localStorage.setItem('cinefusion_session', JSON.stringify(sessionData));
		localStorage.setItem('cinefusion_remember', username);
	} else {
		sessionStorage.setItem('cinefusion_session', JSON.stringify(sessionData));
	}

	// Show success message
	showAlert('Login successful! Redirecting...', 'success');

	// Redirect after short delay
	setTimeout(() => {
		window.location.href = 'homepage.html';
	}, 1500);
}

/**
 * Handle failed login
 * @param {string} username - Username
 * @param {string} message - Error message
 */
function handleFailedLogin(username, message) {
	showAlert(message, 'error');

	// Clear password field
	const passwordInput = document.getElementById('password');
	if (passwordInput) {
		passwordInput.value = '';
		passwordInput.focus();
	}
}

/**
 * Check for existing user session
 */
function checkExistingSession() {
	const sessionData =
		localStorage.getItem('cinefusion_session') ||
		sessionStorage.getItem('cinefusion_session');

	if (sessionData) {
		try {
			const session = JSON.parse(sessionData);
			// Optionally redirect if already logged in
			// window.location.href = 'homepage.html';
		} catch (error) {
			console.error('Invalid session data:', error);
			clearSession();
		}
	}
}

/**
 * Load remembered credentials
 */
function loadRememberedCredentials() {
	const rememberedUsername = localStorage.getItem('cinefusion_remember');
	if (rememberedUsername) {
		const usernameInput = document.getElementById('username');
		const rememberCheckbox = document.getElementById('remember');

		if (usernameInput) {
			usernameInput.value = rememberedUsername;
		}

		if (rememberCheckbox) {
			rememberCheckbox.checked = true;
		}
	}
}

/**
 * Clear user session
 */
function clearSession() {
	localStorage.removeItem('cinefusion_session');
	sessionStorage.removeItem('cinefusion_session');
	localStorage.removeItem('cinefusion_remember');
}

/**
 * Show/hide loading state
 * @param {boolean} show - Whether to show loading
 */
function showLoading(show) {
	const loadingDiv = document.getElementById('loading');
	const loginForm = document.getElementById('login-form');

	if (loadingDiv && loginForm) {
		if (show) {
			loadingDiv.style.display = 'block';
			loginForm.style.display = 'none';
		} else {
			loadingDiv.style.display = 'none';
			loginForm.style.display = 'block';
		}
	}
}

/**
 * Show alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, error, warning)
 */
function showAlert(message, type = 'info') {
	// Remove existing alerts
	const existingAlerts = document.querySelectorAll('.alert');
	existingAlerts.forEach((alert) => alert.remove());

	// Create new alert
	const alertDiv = document.createElement('div');
	alertDiv.className = `alert ${type}`;
	alertDiv.textContent = message;

	// Insert at the top of the login container
	const loginContainer = document.querySelector('.login');
	if (loginContainer) {
		loginContainer.insertBefore(alertDiv, loginContainer.firstChild);

		// Auto-remove after 5 seconds
		setTimeout(() => {
			if (alertDiv.parentNode) {
				alertDiv.remove();
			}
		}, 5000);
	}
}

/**
 * Show field-specific error
 * @param {string} fieldId - Field ID
 * @param {string} message - Error message
 */
function showFieldError(fieldId, message) {
	const field = document.getElementById(fieldId);
	const formGroup = field?.closest('.form-group');

	if (formGroup) {
		formGroup.classList.add('has-error');

		// Remove existing error message
		const existingError = formGroup.querySelector('.error-message');
		if (existingError) {
			existingError.remove();
		}

		// Add new error message
		const errorDiv = document.createElement('span');
		errorDiv.className = 'error-message';
		errorDiv.textContent = message;
		field.parentNode.appendChild(errorDiv);
	}
}

/**
 * Clear all field errors
 */
function clearFieldErrors() {
	const formGroups = document.querySelectorAll('.form-group');
	formGroups.forEach((group) => {
		group.classList.remove('has-error', 'has-success');
		const errorMessage = group.querySelector('.error-message');
		if (errorMessage) {
			errorMessage.remove();
		}
	});
}

/**
 * Validate password input in real-time
 * @param {Event} event - Input event
 */
function validatePasswordInput(event) {
	const password = event.target.value;
	const formGroup = event.target.closest('.form-group');

	if (password.length === 0) {
		formGroup?.classList.remove('has-error', 'has-success');
	} else if (password.length < CONFIG.minPasswordLength) {
		formGroup?.classList.add('has-error');
		formGroup?.classList.remove('has-success');
	} else {
		formGroup?.classList.add('has-success');
		formGroup?.classList.remove('has-error');
	}
}

/**
 * Logout function (for use on other pages)
 */
function logout() {
	clearSession();
	window.location.href = 'login.html';
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', initializeLogin);
} else {
	initializeLogin();
}

// Export functions for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		logout,
		clearSession,
		checkExistingSession,
	};
}
