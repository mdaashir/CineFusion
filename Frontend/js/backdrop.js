// Background images array with relative paths
const backgrounds = [
	'../img/pic1.jpeg',
	'../img/pic2.jpeg',
	'../img/logo-color.png',
	'../img/background.png',
];

// Current background index
let currentBackgroundIndex = 0;

/**
 * Get a random background image from the array
 * @returns {string} Random background image path
 */
function getRandomBackground() {
	return backgrounds[Math.floor(Math.random() * backgrounds.length)];
}

/**
 * Get the next background image in sequence
 * @returns {string} Next background image path
 */
function getNextBackground() {
	currentBackgroundIndex = (currentBackgroundIndex + 1) % backgrounds.length;
	return backgrounds[currentBackgroundIndex];
}

/**
 * Change the background image
 * @param {boolean} random - Whether to use random or sequential background
 */
function changeBackground(random = true) {
	try {
		const backgroundUrl = random ? getRandomBackground() : getNextBackground();

		// Create a new image to preload
		const img = new Image();
		img.onload = function () {
			// Apply the background once the image is loaded
			document.body.style.backgroundImage = `url('${backgroundUrl}')`;
		};
		img.onerror = function () {
			console.warn(`Failed to load background image: ${backgroundUrl}`);
		};
		img.src = backgroundUrl;
	} catch (error) {
		console.error('Error changing background:', error);
	}
}

/**
 * Initialize the background changer
 */
function initializeBackgroundChanger() {
	// Set initial background
	changeBackground();

	// Change background every 5 seconds (5000 milliseconds)
	setInterval(() => changeBackground(), 5000);

	// Add smooth transition for better UX
	document.body.style.transition = 'background-image 1s ease-in-out';
	document.body.style.backgroundSize = 'cover';
	document.body.style.backgroundPosition = 'center';
	document.body.style.backgroundRepeat = 'no-repeat';
	document.body.style.backgroundAttachment = 'fixed';
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', initializeBackgroundChanger);
} else {
	initializeBackgroundChanger();
}

// Optional: Allow manual background change on click
document.addEventListener('keydown', function (event) {
	// Press 'B' key to manually change background
	if (event.key.toLowerCase() === 'b') {
		changeBackground();
	}
});

// Export functions for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		changeBackground,
		getRandomBackground,
		getNextBackground,
	};
}
