// An array of background image URLs
var backgrounds = [
	'D:/ads_package/website/images/pic1.jpeg',
	'D:/ads_package/website/images/pic2.jpeg',
	'D:/ads_package/website/images/logo-color.png',
	// Add more background image URLs as needed
];

function getRandomBackground() {
	return backgrounds[Math.floor(Math.random() * backgrounds.length)];
}

function changeBackground() {
	document.body.style.backgroundImage = 'url(' + getRandomBackground() + ')';
}

// Refresh the background every 5 seconds (5000 milliseconds)
setInterval(changeBackground, 5000);
