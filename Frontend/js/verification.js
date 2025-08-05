/**
 * User Registration and Verification System
 * Handles signup functionality, password validation, and user verification
 */

// Configuration
const SIGNUP_CONFIG = {
	minPasswordLength: 8,
	maxPasswordLength: 128,
	minUsernameLength: 3,
	maxUsernameLength: 30,
	passwordStrengthRegex: {
		weak: /^.{8,}$/,
		medium: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
		strong: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/,
	},
	emailRegex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
	usernameRegex: /^[a-zA-Z0-9_-]+$/,
};

// Temporary user storage (In production, this would be handled by a backend API)
let registeredUsers =
	JSON.parse(localStorage.getItem('cinefusion_users')) || {};

/**
 * Initialize the signup form
 */
function initializeSignup() {
	const signupForm = document.getElementById('signup-form');

	if (signupForm) {
		signupForm.addEventListener('submit', handleSignup);

		// Add real-time validation
		setupRealTimeValidation();
	}
}

/**
 * Setup real-time validation for form fields
 */
function setupRealTimeValidation() {
	const emailInput = document.getElementById('email');
	const usernameInput = document.getElementById('username');
	const passwordInput = document.getElementById('password');
	const confirmPasswordInput = document.getElementById('confirmPassword');

	if (emailInput) {
		emailInput.addEventListener('blur', () => validateEmail(emailInput.value));
		emailInput.addEventListener('input', clearFieldError.bind(null, 'email'));
	}

	if (usernameInput) {
		usernameInput.addEventListener('blur', () =>
			validateUsername(usernameInput.value)
		);
		usernameInput.addEventListener(
			'input',
			clearFieldError.bind(null, 'username')
		);
	}

	if (passwordInput) {
		passwordInput.addEventListener('input', (e) => {
			validatePassword(e.target.value);
			updatePasswordStrength(e.target.value);
		});
	}

	if (confirmPasswordInput) {
		confirmPasswordInput.addEventListener('input', () => {
			const password = passwordInput?.value || '';
			const confirmPassword = confirmPasswordInput.value;
			validatePasswordMatch(password, confirmPassword);
		});
	}
}

/**
 * Handle signup form submission
 * @param {Event} event - Form submit event
 */
async function handleSignup(event) {
	event.preventDefault();

	const formData = getFormData();

	// Validate all inputs
	if (!validateAllInputs(formData)) {
		return;
	}

	// Show loading state
	showLoading(true);

	try {
		// Simulate API call delay
		await new Promise((resolve) => setTimeout(resolve, 1500));

		// Register user
		const registrationResult = registerUser(formData);

		if (registrationResult.success) {
			handleSuccessfulRegistration(formData.username);
		} else {
			showAlert(registrationResult.message, 'error');
		}
	} catch (error) {
		console.error('Registration error:', error);
		showAlert('An unexpected error occurred. Please try again.', 'error');
	} finally {
		showLoading(false);
	}
}

/**
 * Get form data
 * @returns {Object} Form data object
 */
function getFormData() {
	return {
		email: document.getElementById('email')?.value.trim() || '',
		username: document.getElementById('username')?.value.trim() || '',
		password: document.getElementById('password')?.value || '',
		confirmPassword: document.getElementById('confirmPassword')?.value || '',
		agreeTerms: document.getElementById('agreeTerms')?.checked || false,
	};
}

/**
 * Validate all form inputs
 * @param {Object} formData - Form data object
 * @returns {boolean} Whether all inputs are valid
 */
function validateAllInputs(formData) {
	let isValid = true;

	// Clear previous errors
	clearAllErrors();

	// Validate email
	if (!validateEmail(formData.email)) {
		isValid = false;
	}

	// Validate username
	if (!validateUsername(formData.username)) {
		isValid = false;
	}

	// Validate password
	if (!validatePassword(formData.password)) {
		isValid = false;
	}

	// Validate password match
	if (!validatePasswordMatch(formData.password, formData.confirmPassword)) {
		isValid = false;
	}

	// Validate terms agreement
	if (!formData.agreeTerms) {
		showAlert(
			'You must agree to the Terms of Service and Privacy Policy',
			'error'
		);
		isValid = false;
	}

	return isValid;
}

/**
 * Validate email address
 * @param {string} email - Email address
 * @returns {boolean} Whether email is valid
 */
function validateEmail(email) {
	if (!email) {
		showFieldError('email', 'Email address is required');
		return false;
	}

	if (!SIGNUP_CONFIG.emailRegex.test(email)) {
		showFieldError('email', 'Please enter a valid email address');
		return false;
	}

	// Check if email already exists
	const existingUser = Object.values(registeredUsers).find(
		(user) => user.email === email
	);
	if (existingUser) {
		showFieldError('email', 'This email address is already registered');
		return false;
	}

	showFieldSuccess('email');
	return true;
}

/**
 * Validate username
 * @param {string} username - Username
 * @returns {boolean} Whether username is valid
 */
function validateUsername(username) {
	if (!username) {
		showFieldError('username', 'Username is required');
		return false;
	}

	if (username.length < SIGNUP_CONFIG.minUsernameLength) {
		showFieldError(
			'username',
			`Username must be at least ${SIGNUP_CONFIG.minUsernameLength} characters`
		);
		return false;
	}

	if (username.length > SIGNUP_CONFIG.maxUsernameLength) {
		showFieldError(
			'username',
			`Username must be no more than ${SIGNUP_CONFIG.maxUsernameLength} characters`
		);
		return false;
	}

	if (!SIGNUP_CONFIG.usernameRegex.test(username)) {
		showFieldError(
			'username',
			'Username can only contain letters, numbers, hyphens, and underscores'
		);
		return false;
	}

	// Check if username already exists
	if (registeredUsers[username.toLowerCase()]) {
		showFieldError('username', 'This username is already taken');
		return false;
	}

	showFieldSuccess('username');
	return true;
}

/**
 * Validate password
 * @param {string} password - Password
 * @returns {boolean} Whether password is valid
 */
function validatePassword(password) {
	if (!password) {
		showFieldError('password', 'Password is required');
		return false;
	}

	if (password.length < SIGNUP_CONFIG.minPasswordLength) {
		showFieldError(
			'password',
			`Password must be at least ${SIGNUP_CONFIG.minPasswordLength} characters`
		);
		return false;
	}

	if (password.length > SIGNUP_CONFIG.maxPasswordLength) {
		showFieldError(
			'password',
			`Password must be no more than ${SIGNUP_CONFIG.maxPasswordLength} characters`
		);
		return false;
	}

	// Check password strength
	if (!SIGNUP_CONFIG.passwordStrengthRegex.weak.test(password)) {
		showFieldError('password', 'Password is too weak');
		return false;
	}

	showFieldSuccess('password');
	return true;
}

/**
 * Validate password confirmation
 * @param {string} password - Original password
 * @param {string} confirmPassword - Confirmation password
 * @returns {boolean} Whether passwords match
 */
function validatePasswordMatch(password, confirmPassword) {
	if (!confirmPassword) {
		showFieldError('confirmPassword', 'Please confirm your password');
		return false;
	}

	if (password !== confirmPassword) {
		showFieldError('confirmPassword', 'Passwords do not match');
		return false;
	}

	showFieldSuccess('confirmPassword');
	return true;
}

/**
 * Update password strength indicator
 * @param {string} password - Password string
 */
function updatePasswordStrength(password) {
	const strengthIndicator = document.getElementById('passwordStrength');
	if (!strengthIndicator) return;

	let strengthClass = '';
	let strengthText = '';

	if (password.length === 0) {
		strengthIndicator.className = 'password-strength';
		strengthIndicator.textContent = '';
		return;
	}

	if (SIGNUP_CONFIG.passwordStrengthRegex.strong.test(password)) {
		strengthClass = 'strong';
		strengthText = 'Strong password';
	} else if (SIGNUP_CONFIG.passwordStrengthRegex.medium.test(password)) {
		strengthClass = 'medium';
		strengthText = 'Medium password';
	} else {
		strengthClass = 'weak';
		strengthText = 'Weak password';
	}

	strengthIndicator.className = `password-strength ${strengthClass}`;
	strengthIndicator.textContent = strengthText;
}

/**
 * Register new user
 * @param {Object} formData - User registration data
 * @returns {Object} Registration result
 */
function registerUser(formData) {
	try {
		// Create user object
		const user = {
			email: formData.email,
			username: formData.username,
			password: formData.password, // In production, this would be hashed
			registrationDate: new Date().toISOString(),
			verified: false,
			loginAttempts: 0,
		};

		// Store user (in production, this would be sent to a backend API)
		registeredUsers[formData.username.toLowerCase()] = user;
		localStorage.setItem('cinefusion_users', JSON.stringify(registeredUsers));

		return { success: true, message: 'Registration successful' };
	} catch (error) {
		console.error('Registration error:', error);
		return {
			success: false,
			message: 'Registration failed. Please try again.',
		};
	}
}

/**
 * Handle successful registration
 * @param {string} username - Registered username
 */
function handleSuccessfulRegistration(username) {
	showAlert('Account created successfully! Redirecting to login...', 'success');

	// Redirect to login page after delay
	setTimeout(() => {
		window.location.href = 'login.html';
	}, 2000);
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
		formGroup.classList.remove('has-success');

		// Remove existing error message
		const existingError = formGroup.querySelector('.error-message');
		if (existingError) {
			existingError.remove();
		}

		// Add new error message
		const errorDiv = document.createElement('span');
		errorDiv.className = 'error-message';
		errorDiv.textContent = message;
		if (field && field.parentNode) {
			field.parentNode.appendChild(errorDiv);
		}
	}
}

/**
 * Show field success state
 * @param {string} fieldId - Field ID
 */
function showFieldSuccess(fieldId) {
	const field = document.getElementById(fieldId);
	const formGroup = field?.closest('.form-group');

	if (formGroup) {
		formGroup.classList.add('has-success');
		formGroup.classList.remove('has-error');

		// Remove any error messages
		const errorMessage = formGroup.querySelector('.error-message');
		if (errorMessage) {
			errorMessage.remove();
		}
	}
}

/**
 * Clear error for specific field
 * @param {string} fieldId - Field ID
 */
function clearFieldError(fieldId) {
	const field = document.getElementById(fieldId);
	const formGroup = field?.closest('.form-group');

	if (formGroup) {
		formGroup.classList.remove('has-error', 'has-success');
		const errorMessage = formGroup.querySelector('.error-message');
		if (errorMessage) {
			errorMessage.remove();
		}
	}
}

/**
 * Clear all form errors
 */
function clearAllErrors() {
	const formGroups = document.querySelectorAll('.form-group');
	formGroups.forEach((group) => {
		group.classList.remove('has-error', 'has-success');
		const errorMessage = group.querySelector('.error-message');
		if (errorMessage) {
			errorMessage.remove();
		}
	});

	// Clear alerts
	const alerts = document.querySelectorAll('.alert');
	alerts.forEach((alert) => alert.remove());
}

/**
 * Show/hide loading state
 * @param {boolean} show - Whether to show loading
 */
function showLoading(show) {
	const loadingDiv = document.getElementById('loading');
	const signupForm = document.getElementById('signup-form');

	if (loadingDiv && signupForm) {
		if (show) {
			loadingDiv.style.display = 'block';
			signupForm.style.display = 'none';
		} else {
			loadingDiv.style.display = 'none';
			signupForm.style.display = 'block';
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

		// Auto-remove after 5 seconds for non-success messages
		if (type !== 'success') {
			setTimeout(() => {
				if (alertDiv.parentNode) {
					alertDiv.remove();
				}
			}, 5000);
		}
	}
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', initializeSignup);
} else {
	initializeSignup();
}

// Export functions for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		validateEmail,
		validateUsername,
		validatePassword,
		validatePasswordMatch,
	};
}
