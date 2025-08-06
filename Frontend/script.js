/**
 * CineFusion Advanced Frontend Application
 * Complete movie discovery platform with dynamic features
 */

// Application Configuration - Loaded from config.json
let CONFIG = {
	API_BASE: 'http://localhost:8001/api',
	STORAGE_PREFIX: 'cinefusion_',
	ITEMS_PER_PAGE: 24,
	CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
	DEBOUNCE_DELAY: 300,
	THEMES: ['dark', 'light'],
	DEFAULT_THEME: 'dark',
	// Fallback admin credentials
	ADMIN_USERNAME: 'admin',
	ADMIN_PASSWORD: 'admin123',
	ADMIN_ENABLED: true,
	ADMIN_SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes
};

// Load configuration from external config.json
async function loadConfig() {
	try {
		const response = await fetch('../config.json');
		if (response.ok) {
			const config = await response.json();
			// Map external config to internal CONFIG object
			CONFIG = {
				API_BASE: config.frontend.api.base_url,
				STORAGE_PREFIX: config.frontend.ui.storage_prefix,
				ITEMS_PER_PAGE: config.frontend.ui.items_per_page,
				CACHE_DURATION: config.frontend.ui.cache_duration_ms,
				DEBOUNCE_DELAY: config.frontend.ui.debounce_delay,
				THEMES: config.frontend.ui.themes,
				DEFAULT_THEME: config.frontend.ui.default_theme,
				// Additional config properties
				API_TIMEOUT: config.frontend.api.timeout_ms,
				API_RETRY_ATTEMPTS: config.frontend.api.retry_attempts,
				MIN_QUERY_LENGTH: config.frontend.search.min_query_length,
				SUGGESTION_LIMIT: config.frontend.search.suggestion_limit,
				SEARCH_DELAY: config.frontend.search.search_delay_ms,
				ADMIN_ENABLED: config.admin.enabled,
				ADMIN_SESSION_TIMEOUT: config.admin.session_timeout_minutes * 60 * 1000, // Convert to milliseconds
				ADMIN_USERNAME: config.admin.default_credentials.username,
				ADMIN_PASSWORD: config.admin.default_credentials.password,
			};
			console.log('Configuration loaded from config.json');
		} else {
			console.warn('Could not load config.json, using default configuration');
		}
	} catch (error) {
		console.warn(
			'Error loading config.json, using default configuration:',
			error
		);
	}
}

// Application State Management
class AppState {
	constructor() {
		this.currentPage = 'movies';
		this.currentPageNum = 1;
		this.totalPages = 1;
		this.currentQuery = '';
		this.currentFilters = {};
		this.currentSort = { by: 'rating', order: 'desc' };
		this.viewMode = 'grid';
		this.user = null;
		this.watchlist = this.loadWatchlist();
		this.theme = this.loadTheme();
		this.genres = [];
		this.isLoading = false;
		this.cache = new Map();
	}

	loadWatchlist() {
		try {
			const saved = localStorage.getItem(CONFIG.STORAGE_PREFIX + 'watchlist');
			return saved ? JSON.parse(saved) : [];
		} catch (e) {
			console.warn('Failed to load watchlist:', e);
			return [];
		}
	}

	saveWatchlist() {
		try {
			localStorage.setItem(
				CONFIG.STORAGE_PREFIX + 'watchlist',
				JSON.stringify(this.watchlist)
			);
		} catch (e) {
			console.warn('Failed to save watchlist:', e);
		}
	}

	loadTheme() {
		try {
			const saved = localStorage.getItem(CONFIG.STORAGE_PREFIX + 'theme');
			return saved || CONFIG.DEFAULT_THEME;
		} catch (e) {
			return CONFIG.DEFAULT_THEME;
		}
	}

	saveTheme() {
		try {
			localStorage.setItem(CONFIG.STORAGE_PREFIX + 'theme', this.theme);
		} catch (e) {
			console.warn('Failed to save theme:', e);
		}
	}

	addToWatchlist(movie) {
		if (!this.isInWatchlist(movie.title)) {
			this.watchlist.push({
				title: movie.title,
				year: movie.year,
				rating: movie.rating,
				genre: movie.genre,
				director: movie.director,
				duration: movie.duration,
				actors: movie.actors,
				addedAt: new Date().toISOString(),
			});
			this.saveWatchlist();
			return true;
		}
		return false;
	}

	removeFromWatchlist(title) {
		const index = this.watchlist.findIndex((movie) => movie.title === title);
		if (index > -1) {
			this.watchlist.splice(index, 1);
			this.saveWatchlist();
			return true;
		}
		return false;
	}

	isInWatchlist(title) {
		return this.watchlist.some((movie) => movie.title === title);
	}

	clearWatchlist() {
		this.watchlist = [];
		this.saveWatchlist();
	}
}

// API Service
class APIService {
	constructor() {
		this.cache = new Map();
	}

	async request(endpoint, params = {}) {
		const cacheKey = this.generateCacheKey(endpoint, params);
		const cached = this.cache.get(cacheKey);

		if (cached && Date.now() - cached.timestamp < CONFIG.CACHE_DURATION) {
			return cached.data;
		}

		try {
			const url = new URL(CONFIG.API_BASE + endpoint);
			Object.keys(params).forEach((key) => {
				if (
					params[key] !== null &&
					params[key] !== undefined &&
					params[key] !== ''
				) {
					url.searchParams.append(key, params[key]);
				}
			});

			const controller = new AbortController();
			const timeoutId = setTimeout(() => controller.abort(), 10000);

			const response = await fetch(url, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					Accept: 'application/json',
				},
				signal: controller.signal,
			});

			clearTimeout(timeoutId);

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const data = await response.json();

			// Cache successful responses
			this.cache.set(cacheKey, {
				data,
				timestamp: Date.now(),
			});

			return data;
		} catch (error) {
			if (error.name === 'AbortError') {
				throw new Error('Request timeout');
			}
			throw error;
		}
	}

	generateCacheKey(endpoint, params) {
		return `${endpoint}_${JSON.stringify(params)}`;
	}

	async getMovies(page = 1, filters = {}, sort = {}) {
		const params = {
			limit: CONFIG.ITEMS_PER_PAGE,
			offset: (page - 1) * CONFIG.ITEMS_PER_PAGE,
			sort_by: sort.by || 'rating',
			sort_order: sort.order || 'desc',
		};

		// Add filters
		Object.keys(filters).forEach((key) => {
			if (filters[key]) {
				switch (key) {
					case 'genre':
						params.genre = filters[key];
						break;
					case 'yearFrom':
						params.year_from = filters[key];
						break;
					case 'yearTo':
						params.year_to = filters[key];
						break;
					case 'minRating':
						params.min_rating = filters[key];
						break;
					case 'maxRating':
						params.max_rating = filters[key];
						break;
					case 'durationFrom':
						params.duration_from = filters[key];
						break;
					case 'durationTo':
						params.duration_to = filters[key];
						break;
					case 'director':
						params.director = filters[key];
						break;
					case 'actor':
						params.actor = filters[key];
						break;
				}
			}
		});

		const response = await this.request('/movies', params);
		return Array.isArray(response) ? response : response.movies || [];
	}

	async searchMovies(query, page = 1, filters = {}) {
		const params = {
			q: query,
			limit: CONFIG.ITEMS_PER_PAGE,
			offset: (page - 1) * CONFIG.ITEMS_PER_PAGE,
		};

		// Add filters
		Object.keys(filters).forEach((key) => {
			if (filters[key]) {
				params[key] = filters[key];
			}
		});

		const response = await this.request('/search', params);
		return {
			movies: response.movies || [],
			totalCount: response.total_count || 0,
			executionTime: response.execution_time_ms || 0,
		};
	}

	async getSuggestions(query) {
		if (!query || query.length < 2) return [];

		const response = await this.request('/suggestions', {
			q: query,
			limit: 10,
		});
		return response.suggestions || [];
	}

	async getGenres() {
		const response = await this.request('/genres');
		return response.genres || [];
	}

	async getStatistics() {
		return await this.request('/stats');
	}

	async getHealth() {
		return await this.request('/health');
	}
}

// UI Manager
class UIManager {
	constructor(appState, apiService) {
		this.state = appState;
		this.api = apiService;
		this.searchDebounceTimer = null;
	}

	init() {
		this.setupEventListeners();
		this.applyTheme();
		this.loadInitialData();
		this.showPage(this.state.currentPage);
		this.initAdminEvents(); // Initialize admin functionality
	}

	setupEventListeners() {
		// Navigation
		document.querySelectorAll('.nav-link').forEach((link) => {
			link.addEventListener('click', (e) => {
				e.preventDefault();
				const page = e.currentTarget.dataset.page;
				this.showPage(page);
			});
		});

		// Theme toggle
		const themeToggle = document.getElementById('themeToggle');
		themeToggle?.addEventListener('click', () => this.toggleTheme());

		// Search
		const searchInputs = document.querySelectorAll('.search-input');
		searchInputs.forEach((input) => {
			input.addEventListener('input', (e) => this.handleSearchInput(e));
			input.addEventListener('keydown', (e) => {
				if (e.key === 'Enter') {
					this.performSearch(e.target.value);
				}
			});
		});

		// Search button
		document.querySelectorAll('.search-btn').forEach((btn) => {
			btn.addEventListener('click', () => {
				const input = btn
					.closest('.search-container')
					.querySelector('.search-input');
				this.performSearch(input.value);
			});
		});

		// Quick filters
		document.querySelectorAll('.filter-btn').forEach((btn) => {
			btn.addEventListener('click', (e) => this.handleQuickFilter(e));
		});

		// View controls
		document.querySelectorAll('.view-btn').forEach((btn) => {
			btn.addEventListener('click', (e) => this.handleViewChange(e));
		});

		// Sort
		const sortSelect = document.getElementById('sortSelect');
		sortSelect?.addEventListener('change', (e) => this.handleSortChange(e));

		// Filters
		const filtersToggle = document.getElementById('filtersToggle');
		filtersToggle?.addEventListener('click', () => this.toggleFilters());

		const applyFilters = document.getElementById('applyFilters');
		applyFilters?.addEventListener('click', () => this.applyFilters());

		const clearFilters = document.getElementById('clearFilters');
		clearFilters?.addEventListener('click', () => this.clearFilters());

		// Rating range
		const ratingRange = document.getElementById('ratingRange');
		ratingRange?.addEventListener('input', (e) => {
			const value = e.target.value;
			const display = document.getElementById('ratingValue');
			if (display) display.textContent = `${value}+`;
		});

		// Auth
		this.setupAuthEventListeners();

		// Modal
		this.setupModalEventListeners();

		// Watchlist
		const clearWatchlist = document.getElementById('clearWatchlist');
		clearWatchlist?.addEventListener('click', () => this.clearWatchlist());

		// Mobile menu
		const mobileToggle = document.getElementById('mobileToggle');
		mobileToggle?.addEventListener('click', () => this.toggleMobileMenu());

		// User menu
		const userBtn = document.getElementById('userBtn');
		userBtn?.addEventListener('click', (e) => {
			e.stopPropagation();
			document.getElementById('userDropdown')?.classList.toggle('show');
		});

		// Close dropdowns on outside click
		document.addEventListener('click', () => {
			document.querySelectorAll('.user-dropdown').forEach((dropdown) => {
				dropdown.classList.remove('show');
			});
			this.hideSuggestions();
		});
	}

	setupAuthEventListeners() {
		// User menu actions
		document.querySelectorAll('[data-action]').forEach((item) => {
			item.addEventListener('click', (e) => {
				e.preventDefault();
				const action = e.currentTarget.dataset.action;
				this.handleAuthAction(action);
			});
		});

		// Modal switches
		const switchToSignup = document.getElementById('switchToSignup');
		switchToSignup?.addEventListener('click', (e) => {
			e.preventDefault();
			this.hideModal('loginModal');
			this.showModal('signupModal');
		});

		const switchToLogin = document.getElementById('switchToLogin');
		switchToLogin?.addEventListener('click', (e) => {
			e.preventDefault();
			this.hideModal('signupModal');
			this.showModal('loginModal');
		});

		// Forms
		const loginForm = document.getElementById('loginForm');
		loginForm?.addEventListener('submit', (e) => this.handleLogin(e));

		const signupForm = document.getElementById('signupForm');
		signupForm?.addEventListener('submit', (e) => this.handleSignup(e));
	}

	setupModalEventListeners() {
		// Close buttons
		document.querySelectorAll('.modal-close').forEach((btn) => {
			btn.addEventListener('click', (e) => {
				const modal = e.target.closest('.modal');
				this.hideModal(modal.id);
			});
		});

		// Click outside to close
		document.querySelectorAll('.modal').forEach((modal) => {
			modal.addEventListener('click', (e) => {
				if (e.target === modal) {
					this.hideModal(modal.id);
				}
			});
		});

		// Escape key
		document.addEventListener('keydown', (e) => {
			if (e.key === 'Escape') {
				document.querySelectorAll('.modal.show').forEach((modal) => {
					this.hideModal(modal.id);
				});
			}
		});
	}

	async loadInitialData() {
		try {
			// Load stats to get total movies count
			const stats = await this.api.getStatistics();
			this.state.totalMovies = stats.database?.total_movies || 5043;

			// Load genres for filters
			this.state.genres = await this.api.getGenres();
			this.populateGenreFilter();

			// Load initial movies
			await this.loadMovies();
		} catch (error) {
			console.error('Failed to load initial data:', error);
			this.showToast('Failed to load data. Please refresh the page.', 'error');
		}
	}

	populateGenreFilter() {
		const genreFilter = document.getElementById('genreFilter');
		if (genreFilter && this.state.genres.length > 0) {
			genreFilter.innerHTML = '<option value="">All Genres</option>';
			this.state.genres.forEach((genre) => {
				const option = document.createElement('option');
				option.value = genre;
				option.textContent = genre;
				genreFilter.appendChild(option);
			});
		}
	}

	async loadMovies(page = 1) {
		if (this.state.isLoading) return;

		this.state.isLoading = true;
		this.showLoading('moviesLoading');

		try {
			const movies = await this.api.getMovies(
				page,
				this.state.currentFilters,
				this.state.currentSort
			);

			// Update totalMovies based on response
			if (Array.isArray(movies)) {
				// Estimate total based on response size
				if (movies.length === CONFIG.ITEMS_PER_PAGE) {
					// If we got a full page, there might be more
					this.state.totalMovies = page * CONFIG.ITEMS_PER_PAGE + 1;
				} else {
					// Last page or exact count
					this.state.totalMovies =
						(page - 1) * CONFIG.ITEMS_PER_PAGE + movies.length;
				}
			}

			this.state.currentPageNum = page;
			this.displayMovies(movies, 'moviesGrid');
			this.updateMoviesCount(this.state.totalMovies); // Use total count, not current page count
			this.updatePagination('moviesPagination', page);
		} catch (error) {
			console.error('Failed to load movies:', error);
			this.showToast('Failed to load movies. Please try again.', 'error');
		} finally {
			this.state.isLoading = false;
			this.hideLoading('moviesLoading');
		}
	}

	async loadGenres() {
		try {
			const stats = await this.api.getStatistics();
			const genres = this.state.genres;

			const genresGrid = document.getElementById('genresGrid');
			if (genresGrid) {
				genresGrid.innerHTML = genres
					.map((genre) => {
						const count = Math.floor(Math.random() * 500) + 50; // Placeholder count
						return `
                        <div class="genre-card" data-genre="${genre}">
                            <div class="genre-icon">
                                <i class="fas ${this.getGenreIcon(genre)}"></i>
                            </div>
                            <h3 class="genre-name">${genre}</h3>
                            <p class="genre-count">${count} movies</p>
                        </div>
                    `;
					})
					.join('');

				// Add click handlers
				genresGrid.querySelectorAll('.genre-card').forEach((card) => {
					card.addEventListener('click', (e) => {
						const genre = e.currentTarget.dataset.genre;
						this.filterByGenre(genre);
					});
				});
			}
		} catch (error) {
			console.error('Failed to load genres:', error);
		}
	}

	getGenreIcon(genre) {
		const icons = {
			Action: 'fa-rocket',
			Adventure: 'fa-mountain',
			Comedy: 'fa-laugh',
			Drama: 'fa-theater-masks',
			Horror: 'fa-ghost',
			Thriller: 'fa-eye',
			'Sci-Fi': 'fa-robot',
			Fantasy: 'fa-magic',
			Romance: 'fa-heart',
			Crime: 'fa-user-secret',
			Mystery: 'fa-search',
			Animation: 'fa-palette',
			Family: 'fa-home',
			Musical: 'fa-music',
			War: 'fa-shield-alt',
			Western: 'fa-hat-cowboy',
			Documentary: 'fa-camera',
			Biography: 'fa-user',
			History: 'fa-landmark',
			Sport: 'fa-running',
		};
		return icons[genre] || 'fa-film';
	}

	async handleSearchInput(e) {
		const query = e.target.value.trim();

		// Clear previous timer
		if (this.searchDebounceTimer) {
			clearTimeout(this.searchDebounceTimer);
		}

		// Hide suggestions if query is too short
		if (query.length < 2) {
			this.hideSuggestions();
			return;
		}

		// Debounce suggestions
		this.searchDebounceTimer = setTimeout(async () => {
			try {
				const suggestions = await this.api.getSuggestions(query);
				this.showSuggestions(suggestions, e.target);
			} catch (error) {
				console.error('Failed to get suggestions:', error);
				this.hideSuggestions();
			}
		}, CONFIG.DEBOUNCE_DELAY);
	}

	showSuggestions(suggestions, inputElement) {
		const container = inputElement.closest('.search-container');
		const dropdown = container?.querySelector('.search-dropdown');

		if (!dropdown || suggestions.length === 0) {
			this.hideSuggestions();
			return;
		}

		dropdown.innerHTML = suggestions
			.map(
				(suggestion) => `
            <div class="dropdown-suggestion" data-suggestion="${suggestion}">
                <i class="fas fa-search"></i> ${suggestion}
            </div>
        `
			)
			.join('');

		// Add click handlers
		dropdown.querySelectorAll('.dropdown-suggestion').forEach((item) => {
			item.addEventListener('click', (e) => {
				const suggestion = e.currentTarget.dataset.suggestion;
				inputElement.value = suggestion;
				this.performSearch(suggestion);
				this.hideSuggestions();
			});
		});

		dropdown.classList.add('show');
	}

	hideSuggestions() {
		document.querySelectorAll('.search-dropdown').forEach((dropdown) => {
			dropdown.classList.remove('show');
		});
	}

	async performSearch(query, page = 1) {
		if (!query.trim()) return;

		this.state.currentQuery = query.trim();
		if (page === 1) {
			this.showPage('search');
		}

		this.state.isLoading = true;
		this.showLoading('searchResults');

		try {
			const result = await this.api.searchMovies(
				query,
				page,
				this.state.currentFilters
			);

			// Handle both API response formats
			const movies = result.movies || result || [];
			const totalCount =
				result.totalCount || result.total_count || movies.length;

			this.displayMovies(movies, 'searchResults');
			this.updateSearchCount(totalCount, query);

			// Calculate total pages from totalCount
			const totalPages = Math.ceil(totalCount / CONFIG.ITEMS_PER_PAGE);
			this.updatePagination('searchPagination', page, totalPages);
		} catch (error) {
			console.error('Search failed:', error);
			this.showToast('Search failed. Please try again.', 'error');
		} finally {
			this.state.isLoading = false;
			this.hideLoading('searchResults');
		}
	}

	displayMovies(movies, containerId) {
		const container = document.getElementById(containerId);
		if (!container) return;

		if (movies.length === 0) {
			container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-film fa-3x"></i>
                    <h3>No movies found</h3>
                    <p>Try adjusting your search or filters</p>
                </div>
            `;
			return;
		}

		container.className = `movies-grid ${
			this.state.viewMode === 'list' ? 'list-view' : ''
		}`;
		container.innerHTML = movies
			.map((movie) => this.createMovieCard(movie))
			.join('');

		// Add animation
		container.classList.add('fade-in');
	}

	createMovieCard(movie) {
		const isInWatchlist = this.state.isInWatchlist(movie.title);
		const posterUrl = movie.poster_url || 'img/images.png';

		return `
            <div class="movie-card" data-movie='${JSON.stringify(movie)}'>
                <div class="movie-poster">
                    <img src="${posterUrl}" alt="${movie.title}"
                         onerror="this.src='img/images.png'">
                </div>
                <div class="movie-info">
                    <h3 class="movie-title">${movie.title}</h3>
                    <div class="movie-meta">
                        <span class="movie-year">${movie.year || 'N/A'}</span>
                        <span class="movie-rating">
                            <i class="fas fa-star"></i>
                            ${movie.rating || 'N/A'}
                        </span>
                    </div>
                    <p class="movie-genre">${(movie.genre || '')
											.split('|')
											.slice(0, 2)
											.join(', ')}</p>
                    <div class="movie-actions">
                        <button class="action-btn watchlist-btn ${
													isInWatchlist ? 'watchlist-added' : ''
												}"
                                data-action="watchlist">
                            <i class="fas ${
															isInWatchlist ? 'fa-check' : 'fa-bookmark'
														}"></i>
                            ${isInWatchlist ? 'Added' : 'Watchlist'}
                        </button>
                        <button class="action-btn" data-action="details">
                            <i class="fas fa-info-circle"></i>
                            Details
                        </button>
                    </div>
                </div>
            </div>
        `;
	}

	showPage(pageId) {
		// Update navigation
		document.querySelectorAll('.nav-link').forEach((link) => {
			link.classList.toggle('active', link.dataset.page === pageId);
		});

		// Hide all pages
		document.querySelectorAll('.page-content').forEach((page) => {
			page.classList.add('hidden');
		});

		// Show selected page
		const targetPage = document.getElementById(pageId + 'Page');
		if (targetPage) {
			targetPage.classList.remove('hidden');
			this.state.currentPage = pageId;
		}

		// Show/hide search section
		const searchSection = document.getElementById('searchSection');
		if (searchSection) {
			searchSection.style.display = pageId === 'movies' ? 'block' : 'none';
		}

		// Load page-specific content
		switch (pageId) {
			case 'movies':
				this.loadMovies();
				break;
			case 'genres':
				this.loadGenres();
				break;
			case 'watchlist':
				this.loadWatchlist();
				break;
			case 'search':
				// Search results loaded by performSearch
				break;
		}
	}

	loadWatchlist() {
		const watchlistGrid = document.getElementById('watchlistGrid');
		const watchlistEmpty = document.getElementById('watchlistEmpty');
		const watchlistCount = document.getElementById('watchlistCount');

		if (this.state.watchlist.length === 0) {
			watchlistGrid.style.display = 'none';
			watchlistEmpty.style.display = 'block';
			if (watchlistCount) watchlistCount.textContent = '0 movies';
		} else {
			watchlistGrid.style.display = 'grid';
			watchlistEmpty.style.display = 'none';
			if (watchlistCount)
				watchlistCount.textContent = `${this.state.watchlist.length} movies`;

			watchlistGrid.className = `movies-grid ${
				this.state.viewMode === 'list' ? 'list-view' : ''
			}`;
			watchlistGrid.innerHTML = this.state.watchlist
				.map((movie) => this.createMovieCard(movie))
				.join('');
		}
	}

	handleQuickFilter(e) {
		// Update active filter
		document.querySelectorAll('.filter-btn').forEach((btn) => {
			btn.classList.remove('active');
		});
		e.target.classList.add('active');

		const filter = e.target.dataset.filter;

		// Reset current filters and sort
		this.state.currentFilters = {};

		// Apply filter logic
		switch (filter) {
			case 'all':
				// Show all movies with default sorting
				this.state.currentSort = { by: 'rating', order: 'desc' };
				break;
			case 'popular':
				// Sort by rating descending to show most popular first
				this.state.currentSort = { by: 'rating', order: 'desc' };
				break;
			case 'recent':
				// Sort by year descending to show newest first
				this.state.currentSort = { by: 'year', order: 'desc' };
				break;
			case 'top-rated':
				// Filter movies with rating >= 8.0 and sort by rating
				this.state.currentFilters = { minRating: 8.0 };
				this.state.currentSort = { by: 'rating', order: 'desc' };
				break;
		}

		// Load movies with new filters/sort
		this.loadMovies(1);
		this.showToast(
			`Showing ${filter === 'all' ? 'all' : filter.replace('-', ' ')} movies`,
			'info'
		);
	}

	handleViewChange(e) {
		document.querySelectorAll('.view-btn').forEach((btn) => {
			btn.classList.remove('active');
		});
		e.target.classList.add('active');

		this.state.viewMode = e.target.dataset.view;

		// Re-render current view
		if (this.state.currentPage === 'movies') {
			// Re-apply view class to existing grid
			const grid = document.getElementById('moviesGrid');
			if (grid) {
				grid.className = `movies-grid ${
					this.state.viewMode === 'list' ? 'list-view' : ''
				}`;
			}
		}
	}

	handleSortChange(e) {
		const [by, order] = e.target.value.split('-');
		this.state.currentSort = { by, order };
		this.loadMovies(1);
	}

	toggleFilters() {
		const panel = document.getElementById('filtersPanel');
		if (panel) {
			panel.classList.toggle('show');
		}
	}

	applyFilters() {
		const filters = {};

		// Collect filter values
		const genre = document.getElementById('genreFilter')?.value;
		const yearFrom = document.getElementById('yearFrom')?.value;
		const yearTo = document.getElementById('yearTo')?.value;
		const minRating = document.getElementById('ratingRange')?.value;
		const durationFrom = document.getElementById('durationFrom')?.value;
		const durationTo = document.getElementById('durationTo')?.value;

		if (genre) filters.genre = genre;
		if (yearFrom) filters.yearFrom = yearFrom;
		if (yearTo) filters.yearTo = yearTo;
		if (minRating && minRating > 0) filters.minRating = minRating;
		if (durationFrom) filters.durationFrom = durationFrom;
		if (durationTo) filters.durationTo = durationTo;

		this.state.currentFilters = filters;
		this.loadMovies(1);
		this.showToast('Filters applied successfully', 'success');
	}

	clearFilters() {
		this.state.currentFilters = {};

		// Clear form inputs
		document.getElementById('genreFilter').value = '';
		document.getElementById('yearFrom').value = '';
		document.getElementById('yearTo').value = '';
		document.getElementById('ratingRange').value = 0;
		document.getElementById('ratingValue').textContent = '0+';
		document.getElementById('durationFrom').value = '';
		document.getElementById('durationTo').value = '';

		this.loadMovies(1);
		this.showToast('Filters cleared', 'info');
	}

	filterByGenre(genre) {
		this.state.currentFilters = { genre };
		this.showPage('movies');
		this.showToast(`Showing ${genre} movies`, 'info');
	}

	toggleTheme() {
		this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
		this.applyTheme();
		this.state.saveTheme();
	}

	applyTheme() {
		document.body.className = `theme-${this.state.theme}`;

		const themeIcon = document.querySelector('#themeToggle i');
		if (themeIcon) {
			themeIcon.className =
				this.state.theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
		}
	}

	handleAuthAction(action) {
		switch (action) {
			case 'login':
				this.showModal('loginModal');
				break;
			case 'signup':
				this.showModal('signupModal');
				break;
			case 'logout':
				this.handleLogout();
				break;
		}
	}

	async handleLogin(e) {
		e.preventDefault();
		const username = document.getElementById('loginUsername')?.value;
		const password = document.getElementById('loginPassword')?.value;

		if (!username || !password) {
			this.showToast('Please fill in all fields', 'error');
			return;
		}

		// Simulate login (replace with actual API call)
		try {
			// Check for admin credentials from config
			const isAdmin =
				username.toLowerCase() === CONFIG.ADMIN_USERNAME.toLowerCase() &&
				password === CONFIG.ADMIN_PASSWORD;

			// Mock successful login
			this.state.user = {
				username,
				name: isAdmin ? 'Administrator' : username,
				role: isAdmin ? 'admin' : 'user',
			};

			this.updateUserUI();
			this.hideModal('loginModal');
			this.showToast(
				`Welcome ${isAdmin ? 'Administrator' : 'back'}!`,
				'success'
			);

			// Show admin panel if admin user
			if (isAdmin) {
				this.showAdminControls();
			}
		} catch (error) {
			this.showToast('Login failed. Please try again.', 'error');
		}
	}

	async handleSignup(e) {
		e.preventDefault();
		const name = document.getElementById('signupName')?.value;
		const email = document.getElementById('signupEmail')?.value;
		const password = document.getElementById('signupPassword')?.value;
		const confirmPassword = document.getElementById('confirmPassword')?.value;

		if (!name || !email || !password || !confirmPassword) {
			this.showToast('Please fill in all fields', 'error');
			return;
		}

		if (password !== confirmPassword) {
			this.showToast('Passwords do not match', 'error');
			return;
		}

		// Simulate signup (replace with actual API call)
		try {
			// Mock successful signup
			this.state.user = { email, name };
			this.updateUserUI();
			this.hideModal('signupModal');
			this.showToast('Account created successfully!', 'success');
		} catch (error) {
			this.showToast('Signup failed. Please try again.', 'error');
		}
	}

	handleLogout() {
		this.state.user = null;
		this.updateUserUI();
		this.hideAdminControls(); // Hide admin controls on logout
		this.showToast('Logged out successfully', 'info');
	}

	updateUserUI() {
		const userNameElement = document.querySelector('.user-name');
		const loginItem = document.querySelector('[data-action="login"]');
		const signupItem = document.querySelector('[data-action="signup"]');
		const logoutItem = document.querySelector('[data-action="logout"]');

		if (this.state.user) {
			if (userNameElement) userNameElement.textContent = this.state.user.name;
			if (loginItem) loginItem.style.display = 'none';
			if (signupItem) signupItem.style.display = 'none';
			if (logoutItem) logoutItem.style.display = 'block';
		} else {
			if (userNameElement) userNameElement.textContent = 'Guest';
			if (loginItem) loginItem.style.display = 'block';
			if (signupItem) signupItem.style.display = 'block';
			if (logoutItem) logoutItem.style.display = 'none';
		}
	}

	showModal(modalId) {
		const modal = document.getElementById(modalId);
		if (modal) {
			modal.classList.add('show');
			document.body.style.overflow = 'hidden';
		}
	}

	hideModal(modalId) {
		const modal = document.getElementById(modalId);
		if (modal) {
			modal.classList.remove('show');
			document.body.style.overflow = '';
		}
	}

	clearWatchlist() {
		if (confirm('Are you sure you want to clear your entire watchlist?')) {
			this.state.clearWatchlist();
			this.loadWatchlist();
			this.showToast('Watchlist cleared', 'info');
		}
	}

	toggleMobileMenu() {
		const navLinks = document.getElementById('navLinks');
		const mobileSearch = document.getElementById('mobileSearch');

		if (navLinks) {
			navLinks.classList.toggle('show');
		}
	}

	updateMoviesCount(count) {
		const countElement = document.getElementById('moviesCount');
		if (countElement) {
			countElement.textContent = `${count} movies`;
		}
	}

	updateSearchCount(count, query) {
		const countElement = document.getElementById('searchCount');
		if (countElement) {
			countElement.textContent = `${count} results for "${query}"`;
		}
	}

	updatePagination(containerId, currentPage, totalPages) {
		const container = document.getElementById(containerId);
		if (!container) return;

		// Calculate total pages if not provided
		if (!totalPages) {
			totalPages = Math.ceil(this.state.totalMovies / CONFIG.ITEMS_PER_PAGE);
		}

		if (totalPages <= 1) {
			container.style.display = 'none';
			return;
		}

		container.style.display = 'flex';
		container.innerHTML = this.createPaginationHTML(currentPage, totalPages);

		// Add event listeners
		container.querySelectorAll('.page-btn').forEach((btn) => {
			btn.addEventListener('click', (e) => {
				const page = parseInt(e.target.dataset.page);
				if (page && page !== currentPage) {
					if (this.state.currentPage === 'search') {
						this.performSearch(this.state.currentQuery, page);
					} else {
						this.loadMovies(page);
					}
				}
			});
		});
	}

	createPaginationHTML(currentPage, totalPages) {
		let html = '';

		// Previous button
		html += `
            <button class="page-btn" data-page="${currentPage - 1}" ${
			currentPage === 1 ? 'disabled' : ''
		}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

		// Page numbers
		const maxVisible = 5;
		let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
		let endPage = Math.min(totalPages, startPage + maxVisible - 1);

		if (endPage - startPage + 1 < maxVisible) {
			startPage = Math.max(1, endPage - maxVisible + 1);
		}

		if (startPage > 1) {
			html += `<button class="page-btn" data-page="1">1</button>`;
			if (startPage > 2) {
				html += `<span class="page-ellipsis">...</span>`;
			}
		}

		for (let i = startPage; i <= endPage; i++) {
			html += `
                <button class="page-btn ${
									i === currentPage ? 'active' : ''
								}" data-page="${i}">
                    ${i}
                </button>
            `;
		}

		if (endPage < totalPages) {
			if (endPage < totalPages - 1) {
				html += `<span class="page-ellipsis">...</span>`;
			}
			html += `<button class="page-btn" data-page="${totalPages}">${totalPages}</button>`;
		}

		// Next button
		html += `
            <button class="page-btn" data-page="${currentPage + 1}" ${
			currentPage === totalPages ? 'disabled' : ''
		}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

		// Page info
		html += `
            <span class="page-info">
                Page ${currentPage} of ${totalPages}
            </span>
        `;

		return html;
	}

	showLoading(containerId) {
		const container = document.getElementById(containerId);
		if (container) {
			container.style.display = 'flex';
		}
	}

	hideLoading(containerId) {
		const container = document.getElementById(containerId);
		if (container) {
			container.style.display = 'none';
		}
	}

	showToast(message, type = 'info', duration = 3000) {
		const container = document.getElementById('toastContainer');
		if (!container) return;

		const toast = document.createElement('div');
		toast.className = `toast ${type}`;
		toast.innerHTML = `
            <i class="fas ${this.getToastIcon(type)}"></i>
            <span>${message}</span>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

		container.appendChild(toast);

		// Show animation
		setTimeout(() => toast.classList.add('show'), 100);

		// Close button
		const closeBtn = toast.querySelector('.toast-close');
		closeBtn.addEventListener('click', () => this.removeToast(toast));

		// Auto remove
		setTimeout(() => this.removeToast(toast), duration);
	}

	getToastIcon(type) {
		const icons = {
			success: 'fa-check-circle',
			error: 'fa-exclamation-circle',
			warning: 'fa-exclamation-triangle',
			info: 'fa-info-circle',
		};
		return icons[type] || 'fa-info-circle';
	}

	removeToast(toast) {
		toast.classList.remove('show');
		setTimeout(() => {
			if (toast.parentNode) {
				toast.parentNode.removeChild(toast);
			}
		}, 300);
	}

	// Admin functionality methods
	showAdminControls() {
		const adminLink = document.querySelector('.admin-only');
		if (adminLink) {
			adminLink.style.display = 'flex';
		}
	}

	hideAdminControls() {
		const adminLink = document.querySelector('.admin-only');
		if (adminLink) {
			adminLink.style.display = 'none';
		}
	}

	initAdminEvents() {
		// Admin tab switching
		document.querySelectorAll('.admin-tab-btn').forEach((btn) => {
			btn.addEventListener('click', (e) => {
				const tab = e.target.dataset.tab;
				this.switchAdminTab(tab);
			});
		});
	}

	switchAdminTab(tab) {
		// Update tab buttons
		document.querySelectorAll('.admin-tab-btn').forEach((btn) => {
			btn.classList.remove('active');
		});
		document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

		// Update tab content
		document.querySelectorAll('.admin-tab-content').forEach((content) => {
			content.classList.remove('active');
		});
		document.getElementById(`${tab}Tab`).classList.add('active');
	}
}

// Event delegation for dynamic content
document.addEventListener('click', (e) => {
	// Movie card actions
	if (e.target.matches('.action-btn') || e.target.closest('.action-btn')) {
		const btn = e.target.closest('.action-btn');
		const action = btn.dataset.action;
		const movieCard = btn.closest('.movie-card');
		const movieData = JSON.parse(movieCard.dataset.movie);

		if (action === 'watchlist') {
			toggleWatchlist(movieData, btn);
		} else if (action === 'details') {
			showMovieDetails(movieData);
		}
	}

	// Movie card click (for details)
	if (e.target.closest('.movie-card') && !e.target.closest('.action-btn')) {
		const movieCard = e.target.closest('.movie-card');
		const movieData = JSON.parse(movieCard.dataset.movie);
		showMovieDetails(movieData);
	}
});

// Watchlist functions
function toggleWatchlist(movie, btn) {
	const isAdded = app.state.isInWatchlist(movie.title);

	if (isAdded) {
		app.state.removeFromWatchlist(movie.title);
		btn.classList.remove('watchlist-added');
		btn.innerHTML = '<i class="fas fa-bookmark"></i> Watchlist';
		app.showToast('Removed from watchlist', 'info');
	} else {
		app.state.addToWatchlist(movie);
		btn.classList.add('watchlist-added');
		btn.innerHTML = '<i class="fas fa-check"></i> Added';
		app.showToast('Added to watchlist', 'success');
	}

	// Update watchlist page if currently viewing
	if (app.state.currentPage === 'watchlist') {
		app.loadWatchlist();
	}
}

// Movie details modal
function showMovieDetails(movie) {
	const modalBody = document.getElementById('modalBody');
	if (!modalBody) return;

	modalBody.innerHTML = `
        <div class="movie-detail">
            <div class="movie-detail-poster">
                <img src="${movie.poster_url || 'img/images.png'}" alt="${
		movie.title
	}"
                     onerror="this.src='img/images.png'">
            </div>
            <div class="movie-detail-info">
                <h2>${movie.title}</h2>
                <div class="movie-detail-meta">
                    <div class="detail-item">
                        <span class="detail-label">Year</span>
                        <span class="detail-value">${movie.year || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Rating</span>
                        <span class="detail-value">
                            <i class="fas fa-star" style="color: #ffc107;"></i>
                            ${movie.rating || 'N/A'}/10
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Duration</span>
                        <span class="detail-value">${
													movie.duration || 'N/A'
												} min</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Genre</span>
                        <span class="detail-value">${(
													movie.genre || ''
												).replace(/\|/g, ', ')}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Director</span>
                        <span class="detail-value">${
													movie.director || 'N/A'
												}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Actors</span>
                        <span class="detail-value">${
													movie.actors || 'N/A'
												}</span>
                    </div>
                </div>
                ${movie.plot ? `<p class="movie-plot">${movie.plot}</p>` : ''}
                <div class="movie-actions">
                    <button class="btn btn-primary" onclick="toggleWatchlist(${JSON.stringify(
											movie
										).replace(/"/g, '&quot;')}, this)">
                        <i class="fas ${
													app.state.isInWatchlist(movie.title)
														? 'fa-check'
														: 'fa-bookmark'
												}"></i>
                        ${
													app.state.isInWatchlist(movie.title)
														? 'Remove from Watchlist'
														: 'Add to Watchlist'
												}
                    </button>
                </div>
            </div>
        </div>
    `;

	app.showModal('movieModal');
}

// Initialize application
let app;

document.addEventListener('DOMContentLoaded', async () => {
	// Load configuration first
	await loadConfig();

	const appState = new AppState();
	const apiService = new APIService();
	app = new UIManager(appState, apiService);

	// Make app globally available
	window.app = app;

	app.init();
});

// Handle window resize for responsive design
window.addEventListener('resize', () => {
	// Debounce resize events
	clearTimeout(window.resizeTimer);
	window.resizeTimer = setTimeout(() => {
		// Trigger any resize-dependent updates
		if (app && app.state.currentPage) {
			// Re-render current page if needed
		}
	}, 250);
});

// Global Admin Functions
window.testBackendConnection = async function () {
	const result = document.getElementById('backend-debug-result');
	try {
		const response = await fetch(`${CONFIG.API_BASE}/health`);
		const data = await response.json();
		result.innerHTML = `<strong style="color: #28a745;">✅ Backend Connected</strong><br>
			Status: ${data.status}<br>
			Movies: ${data.movies_loaded}<br>
			Version: ${data.version}<br>
			Uptime: ${Math.floor(data.uptime_seconds / 3600)}h ${Math.floor(
			(data.uptime_seconds % 3600) / 60
		)}m`;
	} catch (error) {
		result.innerHTML = `<strong style="color: #dc3545;">❌ Backend Error:</strong> ${error.message}`;
	}
};

window.testSearchFunction = async function () {
	const query = document.getElementById('debug-search-input').value;
	const result = document.getElementById('search-debug-result');
	try {
		const response = await fetch(
			`${CONFIG.API_BASE}/search?q=${encodeURIComponent(query)}&limit=5`
		);
		const data = await response.json();
		result.innerHTML = `<strong style="color: #28a745;">✅ Search Results</strong><br>
			Query: "${query}"<br>
			Total: ${data.total_count}<br>
			Movies: ${data.movies.length}<br>
			Titles: ${data.movies.map((m) => m.title).join(', ')}`;
	} catch (error) {
		result.innerHTML = `<strong style="color: #dc3545;">❌ Search Error:</strong> ${error.message}`;
	}
};

window.testMoviesPagination = async function (page = 1) {
	const result = document.getElementById('movies-debug-result');
	try {
		const response = await fetch(
			`${CONFIG.API_BASE}/movies?limit=24&offset=${
				(page - 1) * 24
			}&sort_by=rating&sort_order=desc`
		);
		const data = await response.json();
		result.innerHTML = `<strong style="color: #28a745;">✅ Movies (Page ${page})</strong><br>
			Count: ${data.length}<br>
			First 3: ${data
				.slice(0, 3)
				.map((m) => `${m.title} (${m.year})`)
				.join(', ')}`;
	} catch (error) {
		result.innerHTML = `<strong style="color: #dc3545;">❌ Movies Error:</strong> ${error.message}`;
	}
};

window.testFilter = async function (type) {
	const result = document.getElementById('filter-debug-result');
	let url = `${CONFIG.API_BASE}/movies?limit=5&sort_by=rating&sort_order=desc`;

	switch (type) {
		case 'popular':
			url += '&sort_by=rating&sort_order=desc';
			break;
		case 'recent':
			url += '&sort_by=year&sort_order=desc';
			break;
		case 'top-rated':
			url += '&min_rating=8.0';
			break;
	}

	try {
		const response = await fetch(url);
		const data = await response.json();
		result.innerHTML = `<strong style="color: #28a745;">✅ ${type.toUpperCase()} Filter</strong><br>
			Count: ${data.length}<br>
			Movies: ${data
				.slice(0, 3)
				.map((m) => `${m.title} (${m.rating}⭐)`)
				.join('<br>')}`;
	} catch (error) {
		result.innerHTML = `<strong style="color: #dc3545;">❌ Filter Error:</strong> ${error.message}`;
	}
};

window.refreshSystemStatus = async function () {
	const container = document.getElementById('system-status-container');
	container.innerHTML =
		'<div style="text-align: center;">Loading system status...</div>';

	try {
		const [healthResponse, statsResponse] = await Promise.all([
			fetch(`${CONFIG.API_BASE}/health`),
			fetch(`${CONFIG.API_BASE}/stats`),
		]);

		const health = await healthResponse.json();
		const stats = await statsResponse.json();

		container.innerHTML = `
			<div class="status-grid">
				<div class="status-item success">
					<h4>System Health</h4>
					<p>Status: ${health.status}</p>
					<p>Uptime: ${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor(
			(health.uptime_seconds % 3600) / 60
		)}m</p>
					<p>Version: ${health.version}</p>
				</div>

				<div class="status-item info">
					<h4>Database</h4>
					<p>Total Movies: ${stats.database.total_movies}</p>
					<p>Directors: ${stats.database.unique_directors}</p>
					<p>Actors: ${stats.database.unique_actors}</p>
					<p>Genres: ${stats.database.unique_genres}</p>
				</div>

				<div class="status-item ${
					stats.performance.current_status === 'healthy' ? 'success' : 'warning'
				}">
					<h4>Performance</h4>
					<p>Status: ${stats.performance.current_status}</p>
					<p>Avg Response: ${stats.performance.avg_response_time_ms.toFixed(2)}ms</p>
					<p>Requests: ${stats.performance.total_requests}</p>
					<p>Error Rate: ${stats.performance.error_rate.toFixed(2)}%</p>
				</div>

				<div class="status-item info">
					<h4>Cache</h4>
					<p>Size: ${stats.cache.size}/${stats.cache.max_size}</p>
					<p>Hit Rate: ${stats.cache.hit_rate.toFixed(2)}%</p>
					<p>Hits: ${stats.cache.hits}</p>
					<p>Misses: ${stats.cache.misses}</p>
				</div>
			</div>
		`;
	} catch (error) {
		container.innerHTML = `<div class="status-item error">
			<h4>Error Loading System Status</h4>
			<p>${error.message}</p>
		</div>`;
	}
};

window.runAllTests = async function () {
	const result = document.getElementById('api-test-results');
	result.innerHTML = '<div>Running comprehensive API tests...</div>';

	const tests = [
		{ name: 'Health Check', fn: () => fetch(`${CONFIG.API_BASE}/health`) },
		{
			name: 'Movies Endpoint',
			fn: () => fetch(`${CONFIG.API_BASE}/movies?limit=1`),
		},
		{
			name: 'Search Endpoint',
			fn: () => fetch(`${CONFIG.API_BASE}/search?q=spider&limit=1`),
		},
		{ name: 'Genres Endpoint', fn: () => fetch(`${CONFIG.API_BASE}/genres`) },
		{ name: 'Stats Endpoint', fn: () => fetch(`${CONFIG.API_BASE}/stats`) },
		{
			name: 'Suggestions Endpoint',
			fn: () => fetch(`${CONFIG.API_BASE}/suggestions?q=sp&limit=3`),
		},
	];

	const results = [];

	for (const test of tests) {
		try {
			const start = Date.now();
			const response = await test.fn();
			const time = Date.now() - start;
			const data = await response.json();

			results.push(
				`<div style="color: #28a745;">✅ ${test.name}: ${response.status} (${time}ms)</div>`
			);
		} catch (error) {
			results.push(
				`<div style="color: #dc3545;">❌ ${test.name}: ${error.message}</div>`
			);
		}
	}

	result.innerHTML = results.join('');
};

window.runHealthTest = () => window.testBackendConnection();
window.runMoviesTest = () => window.testMoviesPagination(1);
window.runSearchTest = () => window.testSearchFunction();

window.runGenresTest = async function () {
	const result = document.getElementById('api-test-results');
	try {
		const response = await fetch(`${CONFIG.API_BASE}/genres`);
		const data = await response.json();
		result.innerHTML = `<div style="color: #28a745;">✅ Genres Test: ${data.genres.length} genres found</div>`;
	} catch (error) {
		result.innerHTML = `<div style="color: #dc3545;">❌ Genres Test: ${error.message}</div>`;
	}
};

window.runStatsTest = async function () {
	const result = document.getElementById('api-test-results');
	try {
		const response = await fetch(`${CONFIG.API_BASE}/stats`);
		const data = await response.json();
		result.innerHTML = `<div style="color: #28a745;">✅ Stats Test: ${data.database.total_movies} total movies</div>`;
	} catch (error) {
		result.innerHTML = `<div style="color: #dc3545;">❌ Stats Test: ${error.message}</div>`;
	}
};

// Handle online/offline status
window.addEventListener('online', () => {
	app.showToast('Connection restored', 'success');
});

window.addEventListener('offline', () => {
	app.showToast(
		'Connection lost. Some features may be unavailable.',
		'warning'
	);
});
