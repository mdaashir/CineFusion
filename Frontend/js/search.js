/**
 * Movie Search and Autocomplete Functionality
 * Handles search operations, autocomplete suggestions, and movie display
 */

// Mock movie data (In production, this would come from a backend API)
const SAMPLE_MOVIES = [
	{
		title: 'Avatar',
		year: 2009,
		genre: 'Action|Adventure|Fantasy|Sci-Fi',
		rating: 7.9,
		poster: '../img/pic1.jpeg',
	},
	{
		title: "Pirates of the Caribbean: At World's End",
		year: 2007,
		genre: 'Action|Adventure|Fantasy',
		rating: 7.1,
		poster: '../img/pic2.jpeg',
	},
	{
		title: 'Spectre',
		year: 2015,
		genre: 'Action|Adventure|Thriller',
		rating: 6.8,
		poster: '../img/pic1.jpeg',
	},
	{
		title: 'The Dark Knight Rises',
		year: 2012,
		genre: 'Action|Thriller',
		rating: 8.5,
		poster: '../img/pic2.jpeg',
	},
	{
		title: 'John Carter',
		year: 2012,
		genre: 'Action|Adventure|Sci-Fi',
		rating: 6.6,
		poster: '../img/pic1.jpeg',
	},
];

// Search configuration
const SEARCH_CONFIG = {
	minSearchLength: 2,
	maxSuggestions: 8,
	searchDelay: 300, // milliseconds
	apiTimeout: 5000, // milliseconds
};

let searchTimeout;
let currentSearchQuery = '';

/**
 * Initialize search functionality
 */
function initializeSearch() {
	const searchInput = document.getElementById('search');
	const suggestionsContainer = document.getElementById('suggestions');

	if (searchInput) {
		searchInput.addEventListener('input', handleSearchInput);
		searchInput.addEventListener('keydown', handleSearchKeydown);
		searchInput.addEventListener('focus', handleSearchFocus);
		searchInput.addEventListener('blur', handleSearchBlur);
	}

	// Load featured movies on page load
	loadFeaturedMovies();

	// Setup search button
	const searchBtn = document.querySelector('.search-btn');
	if (searchBtn) {
		searchBtn.addEventListener('click', performSearch);
	}
}

/**
 * Handle search input events
 * @param {Event} event - Input event
 */
function handleSearchInput(event) {
	const query = event.target.value.trim();
	currentSearchQuery = query;

	// Clear previous timeout
	if (searchTimeout) {
		clearTimeout(searchTimeout);
	}

	// Debounce search to avoid excessive API calls
	searchTimeout = setTimeout(() => {
		if (query.length >= SEARCH_CONFIG.minSearchLength) {
			showSuggestions(query);
		} else {
			hideSuggestions();
		}
	}, SEARCH_CONFIG.searchDelay);
}

/**
 * Handle keyboard navigation in search
 * @param {KeyboardEvent} event - Keydown event
 */
function handleSearchKeydown(event) {
	const suggestionsContainer = document.getElementById('suggestions');
	const suggestions =
		suggestionsContainer?.querySelectorAll('.suggestion-item');

	if (!suggestions || suggestions.length === 0) return;

	const currentActive = suggestionsContainer.querySelector(
		'.suggestion-item.active'
	);
	let activeIndex = currentActive
		? Array.from(suggestions).indexOf(currentActive)
		: -1;

	switch (event.key) {
		case 'ArrowDown':
			event.preventDefault();
			activeIndex = (activeIndex + 1) % suggestions.length;
			setActiveSuggestion(suggestions, activeIndex);
			break;

		case 'ArrowUp':
			event.preventDefault();
			activeIndex = activeIndex <= 0 ? suggestions.length - 1 : activeIndex - 1;
			setActiveSuggestion(suggestions, activeIndex);
			break;

		case 'Enter':
			event.preventDefault();
			if (currentActive) {
				selectSuggestion(currentActive.textContent);
			} else {
				performSearch();
			}
			break;

		case 'Escape':
			hideSuggestions();
			event.target.blur();
			break;
	}
}

/**
 * Handle search input focus
 */
function handleSearchFocus() {
	const query = document.getElementById('search')?.value.trim();
	if (query && query.length >= SEARCH_CONFIG.minSearchLength) {
		showSuggestions(query);
	}
}

/**
 * Handle search input blur (with delay to allow suggestion clicks)
 */
function handleSearchBlur() {
	setTimeout(() => {
		hideSuggestions();
	}, 200);
}

/**
 * Show search suggestions
 * @param {string} query - Search query
 */
async function showSuggestions(query) {
	try {
		const suggestions = await getSuggestions(query);
		displaySuggestions(suggestions);
	} catch (error) {
		console.error('Error getting suggestions:', error);
	}
}

/**
 * Get search suggestions based on query
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of suggestions
 */
async function getSuggestions(query) {
	// Simulate API call
	return new Promise((resolve) => {
		setTimeout(() => {
			const suggestions = SAMPLE_MOVIES.filter(
				(movie) =>
					movie.title.toLowerCase().includes(query.toLowerCase()) ||
					movie.genre.toLowerCase().includes(query.toLowerCase())
			)
				.slice(0, SEARCH_CONFIG.maxSuggestions)
				.map((movie) => movie.title);

			resolve(suggestions);
		}, 100);
	});
}

/**
 * Display suggestions in dropdown
 * @param {Array} suggestions - Array of suggestion strings
 */
function displaySuggestions(suggestions) {
	const suggestionsContainer = document.getElementById('suggestions');
	if (!suggestionsContainer) return;

	// Clear existing suggestions
	suggestionsContainer.innerHTML = '';

	if (suggestions.length === 0) {
		const noResults = document.createElement('div');
		noResults.className = 'suggestion-item no-results';
		noResults.textContent = 'No movies found';
		suggestionsContainer.appendChild(noResults);
	} else {
		suggestions.forEach((suggestion, index) => {
			const suggestionElement = document.createElement('div');
			suggestionElement.className = 'suggestion-item';
			suggestionElement.textContent = suggestion;
			suggestionElement.addEventListener('click', () =>
				selectSuggestion(suggestion)
			);

			// Highlight search query in suggestion
			const regex = new RegExp(`(${currentSearchQuery})`, 'gi');
			suggestionElement.innerHTML = suggestion.replace(
				regex,
				'<strong>$1</strong>'
			);

			suggestionsContainer.appendChild(suggestionElement);
		});
	}

	// Show suggestions container
	suggestionsContainer.classList.add('show');
}

/**
 * Hide suggestions dropdown
 */
function hideSuggestions() {
	const suggestionsContainer = document.getElementById('suggestions');
	if (suggestionsContainer) {
		suggestionsContainer.classList.remove('show');
	}
}

/**
 * Set active suggestion for keyboard navigation
 * @param {NodeList} suggestions - List of suggestion elements
 * @param {number} activeIndex - Index of active suggestion
 */
function setActiveSuggestion(suggestions, activeIndex) {
	// Remove active class from all suggestions
	suggestions.forEach((suggestion) => suggestion.classList.remove('active'));

	// Add active class to current suggestion
	if (suggestions[activeIndex]) {
		suggestions[activeIndex].classList.add('active');
		suggestions[activeIndex].scrollIntoView({ block: 'nearest' });
	}
}

/**
 * Select a suggestion and perform search
 * @param {string} suggestion - Selected suggestion
 */
function selectSuggestion(suggestion) {
	const searchInput = document.getElementById('search');
	if (searchInput) {
		searchInput.value = suggestion;
		performSearch();
		hideSuggestions();
	}
}

/**
 * Perform main search
 */
async function performSearch() {
	const searchInput = document.getElementById('search');
	if (!searchInput) return;

	const query = searchInput.value.trim();
	if (!query) {
		showAlert('Please enter a search term', 'warning');
		return;
	}

	// Hide suggestions
	hideSuggestions();

	// Show loading state
	showSearchLoading(true);

	try {
		const results = await searchMovies(query);
		displaySearchResults(results, query);

		// Add to search history
		addToSearchHistory(query);
	} catch (error) {
		console.error('Search error:', error);
		showAlert('Search failed. Please try again.', 'error');
	} finally {
		showSearchLoading(false);
	}
}

/**
 * Search for movies
 * @param {string} query - Search query
 * @returns {Promise<Array>} Array of movie results
 */
async function searchMovies(query) {
	// Simulate API call
	return new Promise((resolve) => {
		setTimeout(() => {
			const results = SAMPLE_MOVIES.filter(
				(movie) =>
					movie.title.toLowerCase().includes(query.toLowerCase()) ||
					movie.genre.toLowerCase().includes(query.toLowerCase())
			);
			resolve(results);
		}, 500);
	});
}

/**
 * Display search results
 * @param {Array} results - Array of movie results
 * @param {string} query - Original search query
 */
function displaySearchResults(results, query) {
	const movieGrid = document.getElementById('movieGrid');
	const featuredSection = document.querySelector('.featured-movies h2');

	if (!movieGrid) return;

	// Update section title
	if (featuredSection) {
		featuredSection.textContent =
			results.length > 0
				? `Search Results for "${query}" (${results.length} found)`
				: `No results found for "${query}"`;
	}

	// Clear existing content
	movieGrid.innerHTML = '';

	if (results.length === 0) {
		const noResults = document.createElement('div');
		noResults.className = 'no-results';
		noResults.innerHTML = `
            <h3>No movies found</h3>
            <p>Try searching with different keywords or check your spelling.</p>
            <button onclick="loadFeaturedMovies()">Show All Movies</button>
        `;
		movieGrid.appendChild(noResults);
		return;
	}

	// Display results
	results.forEach((movie) => {
		const movieCard = createMovieCard(movie);
		movieGrid.appendChild(movieCard);
	});
}

/**
 * Load and display featured movies
 */
async function loadFeaturedMovies() {
	const movieGrid = document.getElementById('movieGrid');
	const featuredSection = document.querySelector('.featured-movies h2');

	if (!movieGrid) return;

	// Update section title
	if (featuredSection) {
		featuredSection.textContent = 'Featured Movies';
	}

	// Show loading
	movieGrid.innerHTML = '<div class="loading-movies">Loading movies...</div>';

	try {
		// Simulate API call
		await new Promise((resolve) => setTimeout(resolve, 500));

		// Clear loading
		movieGrid.innerHTML = '';

		// Display featured movies
		SAMPLE_MOVIES.forEach((movie) => {
			const movieCard = createMovieCard(movie);
			movieGrid.appendChild(movieCard);
		});
	} catch (error) {
		console.error('Error loading featured movies:', error);
		movieGrid.innerHTML =
			'<div class="error-message">Failed to load movies</div>';
	}
}

/**
 * Create movie card element
 * @param {Object} movie - Movie data
 * @returns {HTMLElement} Movie card element
 */
function createMovieCard(movie) {
	const card = document.createElement('div');
	card.className = 'movie-card';
	card.innerHTML = `
        <img src="${movie.poster}" alt="${
		movie.title
	}" class="movie-poster" onerror="this.src='../img/placeholder.png'">
        <div class="movie-info">
            <h3 class="movie-title">${movie.title}</h3>
            <p class="movie-year">${movie.year}</p>
            <div class="movie-rating">
                <span class="rating-star">★</span>
                <span>${movie.rating}/10</span>
            </div>
            <p class="movie-genre">${movie.genre.replace(/\|/g, ', ')}</p>
        </div>
    `;

	// Add click event for movie details
	card.addEventListener('click', () => showMovieDetails(movie));

	return card;
}

/**
 * Show movie details (placeholder for future implementation)
 * @param {Object} movie - Movie data
 */
function showMovieDetails(movie) {
	alert(
		`Movie: ${movie.title}\nYear: ${movie.year}\nRating: ${
			movie.rating
		}/10\nGenres: ${movie.genre.replace(/\|/g, ', ')}`
	);
}

/**
 * Add search query to history
 * @param {string} query - Search query
 */
function addToSearchHistory(query) {
	try {
		let searchHistory = JSON.parse(
			localStorage.getItem('cinefusion_search_history') || '[]'
		);

		// Remove duplicate if exists
		searchHistory = searchHistory.filter((item) => item.query !== query);

		// Add new search to beginning
		searchHistory.unshift({
			query: query,
			timestamp: new Date().toISOString(),
		});

		// Keep only last 20 searches
		searchHistory = searchHistory.slice(0, 20);

		localStorage.setItem(
			'cinefusion_search_history',
			JSON.stringify(searchHistory)
		);
	} catch (error) {
		console.error('Error saving search history:', error);
	}
}

/**
 * Show/hide search loading state
 * @param {boolean} show - Whether to show loading
 */
function showSearchLoading(show) {
	const searchBtn = document.querySelector('.search-btn');

	if (searchBtn) {
		if (show) {
			searchBtn.innerHTML = '<div class="spinner-small"></div>';
			searchBtn.disabled = true;
		} else {
			searchBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                </svg>
            `;
			searchBtn.disabled = false;
		}
	}
}

/**
 * Show alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type
 */
function showAlert(message, type = 'info') {
	// Create alert element
	const alert = document.createElement('div');
	alert.className = `search-alert ${type}`;
	alert.textContent = message;

	// Add to page
	const searchContainer = document.querySelector('.search-container');
	if (searchContainer) {
		searchContainer.appendChild(alert);

		// Auto-remove after 3 seconds
		setTimeout(() => {
			if (alert.parentNode) {
				alert.remove();
			}
		}, 3000);
	}
}

// Initialize search when DOM is ready
if (document.readyState === 'loading') {
	document.addEventListener('DOMContentLoaded', initializeSearch);
} else {
	initializeSearch();
}

// Export functions for potential use in other scripts
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		performSearch,
		searchMovies,
		addToSearchHistory,
	};
}
