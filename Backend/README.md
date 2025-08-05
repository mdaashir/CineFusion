# 🎬 CineFusion Backend

> **A production-ready FastAPI backend for intelligent movie search and recommendations**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 📋 Table of Contents

- [🎬 CineFusion Backend](#-cinefusion-backend)
  - [📋 Table of Contents](#-table-of-contents)
  - [🌟 Features](#-features)
    - [Core Functionality](#core-functionality)
    - [Performance \& Scalability](#performance--scalability)
    - [Production-Ready Features](#production-ready-features)
  - [🛠️ Technology Stack](#️-technology-stack)
  - [📁 Project Structure](#-project-structure)
  - [🚀 Quick Start](#-quick-start)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Running the Server](#running-the-server)
  - [📖 Server Management](#-server-management)
    - [Server Commands](#server-commands)
    - [Configuration Validation](#configuration-validation)
    - [Testing](#testing)
    - [Production Deployment](#production-deployment)
  - [🔧 Configuration](#-configuration)
    - [Environment Variables](#environment-variables)
    - [JSON Configuration](#json-configuration)
  - [📊 API Documentation](#-api-documentation)
    - [Core Endpoints](#core-endpoints)
    - [Search \& Autocomplete](#search--autocomplete)
    - [Movie Data](#movie-data)
    - [Health \& Monitoring](#health--monitoring)
  - [📝 Logging System](#-logging-system)
    - [Log Types](#log-types)
    - [Log Structure](#log-structure)
    - [Log Files](#log-files)
  - [🚀 Performance Features](#-performance-features)
    - [Caching System](#caching-system)
    - [Rate Limiting](#rate-limiting)
    - [Data Structures](#data-structures)
  - [🔒 Security Features](#-security-features)
    - [Middleware](#middleware)
    - [Security Logging](#security-logging)
    - [Input Validation](#input-validation)
  - [🧪 Testing](#-testing)
    - [Test Suite Features](#test-suite-features)
    - [Running Tests](#running-tests)
    - [Test Categories](#test-categories)
  - [📈 Monitoring \& Health Checks](#-monitoring--health-checks)
    - [Health Check Endpoints](#health-check-endpoints)
    - [Monitoring Features](#monitoring-features)
    - [Alert System](#alert-system)
  - [🐳 Docker Support](#-docker-support)
    - [Quick Start with Docker](#quick-start-with-docker)
    - [Container Management](#container-management)
    - [Docker Environment Variables](#docker-environment-variables)
    - [Production Deployment](#production-deployment-1)
  - [🔄 Data Structures](#-data-structures)
    - [Trie Tree (Autocomplete)](#trie-tree-autocomplete)
    - [AVL Tree (Balanced Storage)](#avl-tree-balanced-storage)
    - [Pandas DataFrame (Data Processing)](#pandas-dataframe-data-processing)
  - [🚨 Error Handling](#-error-handling)
    - [Error Response Format](#error-response-format)
    - [Error Types](#error-types)
    - [Error Logging](#error-logging)
  - [⚡ Performance Optimization](#-performance-optimization)
    - [Response Time Targets](#response-time-targets)
    - [Memory Usage](#memory-usage)
    - [Optimization Techniques](#optimization-techniques)
  - [🛠️ Development](#️-development)
    - [Development Setup](#development-setup)
    - [Code Style](#code-style)
    - [Adding New Features](#adding-new-features)
  - [📚 API Reference](#-api-reference)
    - [Base URL](#base-url)
    - [Authentication](#authentication)
    - [Rate Limits](#rate-limits)
    - [Response Formats](#response-formats)
  - [🤝 Contributing](#-contributing)
    - [Getting Started](#getting-started)
    - [Code Standards](#code-standards)
    - [Testing Requirements](#testing-requirements)
  - [📄 License](#-license)
  - [🎯 Quick Commands Reference](#-quick-commands-reference)

## 🌟 Features

### Core Functionality

- **🔍 Intelligent Movie Search** - Advanced search with fuzzy matching and relevance scoring
- **⚡ Real-time Autocomplete** - Fast suggestions using optimized Trie data structure
- **🎯 Advanced Filtering** - Filter by genre, year, rating, director, and more
- **📊 Multi-criteria Sorting** - Sort by rating, year, popularity, and relevance
- **🎬 Rich Movie Data** - Comprehensive movie metadata with detailed information

### Performance & Scalability

- **💾 Advanced Caching** - LRU cache with TTL and intelligent eviction
- **⚖️ Rate Limiting** - Sliding window rate limiting with configurable limits
- **📈 Performance Monitoring** - Real-time metrics and performance tracking
- **🔄 Auto-balancing Data Structures** - AVL trees for efficient data storage

### Production-Ready Features

- **📝 Comprehensive Logging** - Structured JSON logging with file rotation
- **🔒 Security Middleware** - CORS, trusted hosts, and security headers
- **🏥 Health Checks** - Detailed health monitoring and status reporting
- **🚨 Error Handling** - Graceful error handling with detailed error responses
- **🧪 Comprehensive Testing** - 100% test coverage with automated test suite

## 🛠️ Technology Stack

| Component           | Technology             | Purpose                                       |
| ------------------- | ---------------------- | --------------------------------------------- |
| **Framework**       | FastAPI                | High-performance async web framework          |
| **Language**        | Python 3.8+            | Core backend language                         |
| **Data Processing** | Pandas                 | Movie data manipulation and analysis          |
| **Data Structures** | Custom Trie & AVL Tree | Optimized search and autocomplete             |
| **Validation**      | Pydantic               | Request/response validation and serialization |
| **Server**          | Uvicorn                | ASGI server for production deployment         |
| **Logging**         | Python Logging         | Structured logging with file rotation         |
| **Testing**         | Custom Test Suite      | Comprehensive API testing framework           |

## 📁 Project Structure

```
Backend/
├── 📄 server.py              # Server management script (replaces start_production.py)
├── 📄 main.py                # FastAPI application with all endpoints
├── 📄 config.py              # Configuration management
├── 📄 monitoring.py          # Performance monitoring and alerts
├── 📄 logger.py              # Comprehensive logging system (JSON-configured)
├── 📄 test.py                # Comprehensive test suite
├── 📄 README.md              # This documentation
├── � Dockerfile            # Docker container configuration
├── �📁 data/                  # Data files and configuration
│   ├── 🎬 movie_metadata.csv # Movie database (5000+ movies)
│   └── ⚙️ config.json        # Application configuration
├── 📁 process/               # Data structure implementations
│   ├── 🌳 trie.py            # Trie for autocomplete
│   └── 🌲 avl.py             # AVL tree for balanced storage
└── 📁 logs/                  # Log files (auto-created)
│   ├── 📊 cinefusion_api.log      # API request logs
│   ├── ⚡ cinefusion_performance.log # Performance metrics
│   ├── 🚨 cinefusion_errors.log     # Error logs
│   ├── 🔒 cinefusion_security.log   # Security events
│   └── 📅 cinefusion_daily.log      # Daily consolidated
└── 📁 static/                # Static files (Optional)
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **pip** package manager
- **10MB+ free disk space**
- **512MB+ available RAM**

### Installation

1. **Clone and navigate to the backend directory:**

   ```bash
   cd Backend/
   ```

2. **Install required packages:**

   ```bash
   pip install fastapi uvicorn pandas pydantic
   ```

3. **Verify installation:**
   ```bash
   python server.py validate
   ```

### Running the Server

**Quick start (development mode):**

```bash
python server.py all
```

**Step-by-step approach:**

```bash
# 1. Validate configuration
python server.py validate

# 2. Run tests
python server.py test

# 3. Start server
python server.py start
```

## 📖 Server Management

The `server.py` script provides comprehensive server management capabilities:

### Server Commands

| Command        | Description                              | Example                         |
| -------------- | ---------------------------------------- | ------------------------------- |
| `validate`     | Validate JSON configuration              | `python server.py validate`     |
| `test`         | Run comprehensive test suite             | `python server.py test`         |
| `test --quick` | Run quick tests only                     | `python server.py test --quick` |
| `start`        | Start development server                 | `python server.py start`        |
| `start --prod` | Start production server                  | `python server.py start --prod` |
| `health`       | Perform health check                     | `python server.py health`       |
| `status`       | Show server status                       | `python server.py status`       |
| `all`          | Run everything (validate + test + start) | `python server.py all`          |

### Configuration Validation

```bash
# Validate all configuration files
python server.py validate

# Expected output:
# ✓ Configuration validation passed
# ✓ Dependencies check passed
# ✓ Data files verified
```

### Testing

```bash
# Run full test suite (31 tests)
python server.py test

# Run quick tests only
python server.py test --quick

# Expected output:
# Total Tests: 31
# Passed: 31
# Failed: 0
# Success Rate: 100.0%
```

### Production Deployment

```bash
# Production mode with custom settings
python server.py start --prod --host 0.0.0.0 --port 8080 --workers 4

# Complete production deployment
python server.py all --prod
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description            | Default       | Example                |
| -------------- | ---------------------- | ------------- | ---------------------- |
| `ENVIRONMENT`  | Deployment environment | `development` | `production`           |
| `HOST`         | Server host address    | `127.0.0.1`   | `0.0.0.0`              |
| `PORT`         | Server port            | `8001`        | `8080`                 |
| `DEBUG`        | Enable debug mode      | `false`       | `true`                 |
| `LOG_LEVEL`    | Logging level          | `INFO`        | `DEBUG`                |
| `CORS_ORIGINS` | Allowed CORS origins   | `*`           | `https://mydomain.com` |

### JSON Configuration

The `data/app_config.json` file contains detailed configuration:

```json
{
	"application": {
		"name": "CineFusion",
		"version": "2.0.0",
		"description": "Intelligent Movie Search API"
	},
	"server": {
		"default_host": "127.0.0.1",
		"default_port": 8001,
		"worker_count": 1
	},
	"database": {
		"csv_filename": "movie_metadata.csv",
		"encoding": "utf-8"
	},
	"logging": {
		"default_level": "INFO",
		"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
	}
}
```

## 📊 API Documentation

### Core Endpoints

| Endpoint           | Method | Description                    | Response        |
| ------------------ | ------ | ------------------------------ | --------------- |
| `/`                | GET    | Root endpoint with API info    | Welcome message |
| `/health`          | GET    | Health check and system status | Health metrics  |
| `/api/search`      | GET    | Search movies by query         | Movie results   |
| `/api/suggestions` | GET    | Get autocomplete suggestions   | Suggestion list |

### Search & Autocomplete

**Search Movies:**

```http
GET /api/search?q=avatar&limit=10&genre=action&min_rating=7.0
```

**Response:**

```json
{
	"success": true,
	"results": [
		{
			"title": "Avatar",
			"year": 2009,
			"genre": "Action|Adventure|Fantasy",
			"rating": 7.9,
			"director": "James Cameron"
		}
	],
	"total": 1,
	"query": "avatar",
	"filters_applied": ["genre", "min_rating"]
}
```

**Autocomplete Suggestions:**

```http
GET /api/suggestions?q=av&limit=5
```

**Response:**

```json
{
	"success": true,
	"suggestions": ["Avatar", "Avengers", "Avatar: The Way of Water"],
	"query": "av",
	"count": 3
}
```

### Movie Data

**Get Movies List:**

```http
GET /api/movies?limit=5&offset=0
```

**Get Genres:**

```http
GET /api/genres
```

**Get Directors:**

```http
GET /api/directors?limit=10
```

### Health & Monitoring

**Health Check:**

```http
GET /health
```

**Response:**

```json
{
	"status": "healthy",
	"uptime": 3600,
	"version": "2.0.0",
	"database": {
		"status": "connected",
		"movies_count": 5043
	},
	"cache": {
		"status": "active",
		"hit_rate": 85.5,
		"size": 150
	}
}
```

## 📝 Logging System

### Log Types

| Logger          | Purpose                    | File                         | Level    |
| --------------- | -------------------------- | ---------------------------- | -------- |
| **App**         | General application events | `cinefusion_app.log`         | INFO+    |
| **API**         | Request/response logging   | `cinefusion_api.log`         | INFO+    |
| **Performance** | Performance metrics        | `cinefusion_performance.log` | INFO+    |
| **Error**       | Error tracking             | `cinefusion_errors.log`      | WARNING+ |
| **Security**    | Security events            | `cinefusion_security.log`    | INFO+    |

### Log Structure

**JSON Format (Production):**

```json
{
	"timestamp": "2025-08-06T10:30:15.123456",
	"level": "INFO",
	"logger": "CineFusion.api",
	"message": "API Request - GET /api/search",
	"request_id": "uuid-here",
	"user_ip": "127.0.0.1",
	"endpoint": "/api/search",
	"response_time": 45.67
}
```

**Colored Console (Development):**

```
2025-08-06 10:30:15 - CineFusion.api - INFO - API Request - GET /api/search
```

### Log Files

All logs are stored in the `logs/` directory with automatic rotation:

- **File Size Limit:** 10MB per file
- **Backup Count:** 5 backup files kept
- **Daily Rotation:** Daily logs kept for 30 days
- **Encoding:** UTF-8

## 🚀 Performance Features

### Caching System

- **LRU Cache** with configurable size and TTL
- **Hit Rate Monitoring** with real-time statistics
- **Automatic Cleanup** of expired entries
- **Memory Efficient** with intelligent eviction

### Rate Limiting

- **Sliding Window** algorithm for accurate limiting
- **Per-IP Tracking** with configurable limits
- **Graceful Degradation** with informative responses
- **Security Integration** with alert logging

### Data Structures

- **Trie Tree** for fast autocomplete (O(k) search time)
- **AVL Tree** for balanced data storage (O(log n) operations)
- **Pandas Integration** for efficient data processing
- **Memory Optimization** with lazy loading

## 🔒 Security Features

### Middleware

- **CORS Protection** with configurable origins
- **Trusted Host Validation** for production security
- **Rate Limiting** to prevent abuse
- **Request ID Tracking** for audit trails

### Security Logging

- **Intrusion Detection** with automated logging
- **Rate Limit Violations** tracked and reported
- **Error Pattern Analysis** for security monitoring
- **IP-based Tracking** with user agent logging

### Input Validation

- **Pydantic Models** for request validation
- **SQL Injection Prevention** with parameterized queries
- **XSS Protection** with output sanitization
- **Input Sanitization** with length limits

## 🧪 Testing

### Test Suite Features

- **31 Comprehensive Tests** covering all functionality
- **100% Success Rate** with detailed reporting
- **Performance Benchmarks** with response time validation
- **Error Handling Tests** with edge case coverage

### Running Tests

```bash
# Full test suite
python server.py test

# Quick tests only
python server.py test --quick

# Direct test execution
python test.py
```

### Test Categories

1. **Server Connectivity** - Basic server functionality
2. **Health & Monitoring** - System health validation
3. **Search Functionality** - Search engine testing
4. **Autocomplete** - Suggestion system validation
5. **Movie Endpoints** - Data retrieval testing
6. **Filtering & Sorting** - Advanced query testing
7. **Error Handling** - Error response validation
8. **Performance** - Response time benchmarks

## 📈 Monitoring & Health Checks

### Health Check Endpoints

```bash
# Detailed health check
curl http://localhost:8001/health

# Quick status check
python server.py health
```

### Monitoring Features

- **Real-time Metrics** collection and reporting
- **Performance Tracking** with response time analysis
- **Error Rate Monitoring** with threshold alerts
- **Resource Usage** tracking (memory, CPU)
- **Cache Performance** with hit rate analysis

### Alert System

- **Threshold-based Alerts** for performance degradation
- **Error Rate Monitoring** with automatic notifications
- **Resource Usage Alerts** for system health
- **Custom Metrics** with configurable thresholds

## 🐳 Docker Support

### Quick Start with Docker

The backend can be easily deployed using Docker with a simple, production-ready Dockerfile.

**Build the Docker image:**

```bash
docker build -t cinefusion-backend .
```

**Run the container:**

```bash
# Basic run
docker run -p 8001:8001 cinefusion-backend

# With log persistence
docker run -p 8001:8001 -v $(pwd)/logs:/app/logs cinefusion-backend

# With environment variables
docker run -p 8001:8001 -e ENVIRONMENT=development -e DEBUG=true cinefusion-backend
```

**Access the application:**

- API: http://localhost:8001
- Health Check: http://localhost:8001/health
- API Documentation: http://localhost:8001/docs

### Container Management

**View running containers:**

```bash
docker ps
```

**View logs:**

```bash
docker logs cinefusion-backend
```

**Execute commands in running container:**

```bash
# Run tests
docker exec -it cinefusion-backend python server.py test

# Check status
docker exec -it cinefusion-backend python server.py status

# Access container shell
docker exec -it cinefusion-backend bash
```

**Stop and remove:**

```bash
docker stop cinefusion-backend
docker rm cinefusion-backend
```

### Docker Environment Variables

Configure the container behavior using these environment variables:

| Variable       | Description            | Default      | Example               |
| -------------- | ---------------------- | ------------ | --------------------- |
| `ENVIRONMENT`  | Deployment environment | `production` | `development`         |
| `HOST`         | Server host            | `0.0.0.0`    | `127.0.0.1`           |
| `PORT`         | Server port            | `8001`       | `8080`                |
| `DEBUG`        | Debug mode             | `false`      | `true`                |
| `LOG_LEVEL`    | Logging level          | `INFO`       | `DEBUG`               |
| `CORS_ORIGINS` | Allowed origins        | `*`          | `https://example.com` |

### Production Deployment

For production deployment, the default Dockerfile includes:

- **Multi-stage build** for optimized image size
- **Non-root user** for security
- **Health checks** for container monitoring
- **Optimized Python** settings for performance
- **Log and data directories** with proper permissions

**Production run command:**

```bash
docker run -d \
  --name cinefusion-backend \
  --restart unless-stopped \
  -p 8001:8001 \
  -v $(pwd)/logs:/app/logs \
  -e ENVIRONMENT=production \
  cinefusion-backend
```

## 🔄 Data Structures

### Trie Tree (Autocomplete)

- **Purpose:** Fast prefix-based search for autocomplete
- **Complexity:** O(k) for search where k = query length
- **Features:** Memory-efficient with suggestion limiting
- **Implementation:** Custom optimized for movie titles

### AVL Tree (Balanced Storage)

- **Purpose:** Self-balancing binary search tree
- **Complexity:** O(log n) for all operations
- **Features:** Automatic balancing with height optimization
- **Implementation:** Clean backend-only implementation

### Pandas DataFrame (Data Processing)

- **Purpose:** Efficient data manipulation and filtering
- **Features:** Advanced filtering, sorting, and aggregation
- **Optimization:** Lazy loading with chunked processing
- **Memory:** Efficient memory usage with data types optimization

## 🚨 Error Handling

### Error Response Format

```json
{
	"success": false,
	"detail": "Error description",
	"error_code": "ERROR_TYPE",
	"error_id": "unique-error-id",
	"path": "/api/endpoint",
	"timestamp": "2025-08-06T10:30:15Z"
}
```

### Error Types

- **400 Bad Request** - Invalid input parameters
- **404 Not Found** - Endpoint or resource not found
- **422 Validation Error** - Pydantic validation failures
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Unexpected server errors

### Error Logging

All errors are automatically logged with:

- **Full Stack Traces** for debugging
- **Request Context** including IP and user agent
- **Error Classification** with severity levels
- **Recovery Suggestions** where applicable

## ⚡ Performance Optimization

### Response Time Targets

- **Search Endpoint:** < 1000ms (typically 10-50ms)
- **Autocomplete:** < 500ms (typically 1-5ms)
- **Health Check:** < 100ms (typically 1-2ms)
- **Static Endpoints:** < 50ms (typically 1ms)

### Memory Usage

- **Base Memory:** ~50MB for application
- **Data Structures:** ~20MB for 5000+ movies
- **Cache:** Configurable (default 100MB)
- **Total:** ~200MB typical usage

### Optimization Techniques

1. **Lazy Loading** of data structures
2. **Efficient Caching** with LRU eviction
3. **Optimized Search** algorithms
4. **Memory Pooling** for frequent operations
5. **Database Indexing** simulation with trees

## 🛠️ Development

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd Backend/

# Install dependencies
pip install fastapi uvicorn pandas pydantic

# Start development server
python server.py start

# Run tests
python server.py test
```

### Code Style

- **PEP 8** compliance with line length 88
- **Type Hints** for all function parameters and returns
- **Docstrings** for all public functions and classes
- **Error Handling** with try-catch blocks
- **Logging** for all significant operations

### Adding New Features

1. **Update Models** in appropriate files
2. **Add Endpoints** to main.py
3. **Write Tests** in test.py
4. **Update Documentation** in README.md
5. **Test Thoroughly** with full test suite

## 📚 API Reference

### Base URL

- **Development:** `http://localhost:8001`
- **Production:** `https://your-domain.com`

### Authentication

Currently, the API is open access. For production use, consider adding:

- API key authentication
- JWT token validation
- OAuth2 integration

### Rate Limits

- **Default:** 100 requests per minute per IP
- **Search:** Additional validation for complex queries
- **Autocomplete:** Optimized for high-frequency requests

### Response Formats

All responses follow a consistent format:

```json
{
  "success": true|false,
  "data": {...},
  "message": "Optional message",
  "meta": {
    "timestamp": "ISO timestamp",
    "request_id": "unique-id"
  }
}
```

## 🤝 Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- Follow existing code style
- Add comprehensive tests
- Update documentation
- Use meaningful commit messages
- Add type hints for new functions

### Testing Requirements

- All new features must have tests
- Tests must pass with 100% success rate
- Performance tests for optimization changes
- Error handling tests for edge cases

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Quick Commands Reference

| Action                 | Command                           |
| ---------------------- | --------------------------------- |
| **Start Everything**   | `python server.py all`            |
| **Development Server** | `python server.py start`          |
| **Production Server**  | `python server.py start --prod`   |
| **Run Tests**          | `python server.py test`           |
| **Validate Config**    | `python server.py validate`       |
| **Health Check**       | `python server.py health`         |
| **View Logs**          | `tail -f logs/cinefusion_api.log` |

---

**🎬 CineFusion Backend - Intelligent Movie Search Made Simple**

_Built with ❤️ using FastAPI, Python, and modern web technologies_
