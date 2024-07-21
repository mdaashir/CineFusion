const signupForm = document.getElementById('signup-form');
signupForm.addEventListener('submit', function (event) {
	event.preventDefault();

	const mail = document.getElementById('mail').value;
	const username = document.getElementById('username').value;
	const password = document.getElementById('password').value;
	const reenteredpass = document.getElementById('reenteredpass').value;

	if (password !== reenteredpass) {
		alert('Passwords do not match!');
		return;
	}
	window.location.href = 'login.html';
});

const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', function (event) {
	event.preventDefault();

	const enteredUsername = document.getElementById('username').value;
	const enteredPassword = document.getElementById('password').value;

	const your_username = enteredUsername;
	const your_password = enteredPassword;

	if (your_username === enteredUsername && your_password === enteredPassword) {
		alert('Login successful!');

		window.location.href = 'homepage.html';
		return;
	} else {
		alert('Invalid username or password!');
	}
});
