#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Suite for CineFusion API
Tests all endpoints, monitoring, and error handling
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Set console encoding for Windows compatibility
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class CineFusionAPITester:
    """Comprehensive API testing suite"""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_result(self, test_name: str, passed: bool, message: str = "", data: Any = None):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"{Colors.GREEN}[PASS] {test_name}{Colors.END}")
        else:
            print(f"{Colors.RED}[FAIL] {test_name}{Colors.END}")

        if message:
            print(f"  {message}")

        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    def test_server_connectivity(self) -> bool:
        """Test basic server connectivity"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Server Connectivity Tests ==={Colors.END}")

        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.log_result("Server Root Endpoint", True, f"Status: {response.status_code}")
                return True
            else:
                self.log_result("Server Root Endpoint", False, f"Unexpected status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_result("Server Root Endpoint", False, f"Connection failed: {e}")
            return False

    def test_health_endpoints(self):
        """Test health and monitoring endpoints"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Health & Monitoring Tests ==={Colors.END}")

        # Test main health endpoint
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Health Endpoint", True, f"Status: {data.get('status', 'unknown')}")

                # Check backend components
                if data.get('movies_loaded', 0) > 0:
                    self.log_result("Database Loaded", True, f"Movies: {data['movies_loaded']}")
                else:
                    self.log_result("Database Loaded", False, "No movies loaded")

                if data.get('database_status') == 'connected':
                    self.log_result("Database Connected", True)
                else:
                    self.log_result("Database Connected", False)

                # Check cache stats
                cache_stats = data.get('cache_stats', {})
                if cache_stats:
                    self.log_result("Cache System", True, f"Hit rate: {cache_stats.get('hit_rate', 0)}%")
                else:
                    self.log_result("Cache System", False, "Cache not available")
            else:
                self.log_result("Health Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Health Endpoint", False, f"Error: {e}")        # Test admin performance endpoint
        try:
            response = self.session.get(f"{self.api_url}/admin/performance", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Performance Monitoring", True, f"Status: {data.get('health', {}).get('status', 'unknown')}")
            else:
                self.log_result("Performance Monitoring", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Performance Monitoring", False, f"Error: {e}")

    def test_search_functionality(self):
        """Test search endpoints"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Search Functionality Tests ==={Colors.END}")

        search_tests = [
            ("avatar", "Popular movie search"),
            ("spider", "Partial title search"),
            ("action", "Genre search"),
            ("nonexistent123", "No results search"),
            ("a", "Single character search"),
        ]

        for query, description in search_tests:
            try:
                response = self.session.get(f"{self.api_url}/search?q={query}&limit=5", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    total_results = data.get('total_count', 0)
                    self.log_result(f"Search: {description}", True, f"Query: '{query}' -> {total_results} results")

                    # Validate response structure
                    if 'movies' in data and isinstance(data['movies'], list):
                        self.log_result(f"Search Response Structure: {description}", True)
                    else:
                        self.log_result(f"Search Response Structure: {description}", False, "Invalid response structure")
                else:
                    self.log_result(f"Search: {description}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Search: {description}", False, f"Error: {e}")

    def test_suggestions_functionality(self):
        """Test autocomplete suggestions"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Autocomplete Suggestions Tests ==={Colors.END}")

        suggestion_tests = [
            ("av", "Avatar prefix"),
            ("spi", "Spider prefix"),
            ("the", "Common prefix"),
            ("xyz", "No suggestions"),
        ]

        for query, description in suggestion_tests:
            try:
                response = self.session.get(f"{self.api_url}/suggestions?q={query}&limit=5", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    total_suggestions = data.get('total_available', 0)
                    self.log_result(f"Suggestions: {description}", True, f"Query: '{query}' -> {total_suggestions} suggestions")
                else:
                    self.log_result(f"Suggestions: {description}", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Suggestions: {description}", False, f"Error: {e}")

    def test_movie_endpoints(self):
        """Test movie listing endpoints"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Movie Endpoints Tests ==={Colors.END}")

        # Test movies list
        try:
            response = self.session.get(f"{self.api_url}/movies?limit=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    self.log_result("Movies List", True, f"Retrieved {len(data)} movies")
                else:
                    self.log_result("Movies List", False, "Empty or invalid response")
            else:
                self.log_result("Movies List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Movies List", False, f"Error: {e}")

        # Test genres endpoint
        try:
            response = self.session.get(f"{self.api_url}/genres", timeout=5)
            if response.status_code == 200:
                data = response.json()
                genres = data.get('genres', [])
                if isinstance(genres, list) and len(genres) > 0:
                    self.log_result("Genres List", True, f"Retrieved {len(genres)} genres")
                else:
                    self.log_result("Genres List", False, "Empty or invalid response")
            else:
                self.log_result("Genres List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Genres List", False, f"Error: {e}")

        # Test directors endpoint
        try:
            response = self.session.get(f"{self.api_url}/directors?limit=5", timeout=5)
            if response.status_code == 200:
                data = response.json()
                directors = data.get('directors', [])
                if isinstance(directors, list) and len(directors) > 0:
                    self.log_result("Directors List", True, f"Retrieved {len(directors)} directors")
                else:
                    self.log_result("Directors List", False, "Empty or invalid response")
            else:
                self.log_result("Directors List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Directors List", False, f"Error: {e}")

    def test_filtering_and_sorting(self):
        """Test advanced filtering and sorting"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Filtering & Sorting Tests ==={Colors.END}")

        # Test genre filtering
        try:
            response = self.session.get(f"{self.api_url}/search?q=a&genre=Action&limit=3", timeout=5)
            if response.status_code == 200:
                self.log_result("Genre Filtering", True, "Action genre filter works")
            else:
                self.log_result("Genre Filtering", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Genre Filtering", False, f"Error: {e}")

        # Test year filtering
        try:
            response = self.session.get(f"{self.api_url}/search?q=a&year=2020&limit=3", timeout=5)
            if response.status_code == 200:
                self.log_result("Year Filtering", True, "Year 2020 filter works")
            else:
                self.log_result("Year Filtering", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Year Filtering", False, f"Error: {e}")

        # Test rating filtering
        try:
            response = self.session.get(f"{self.api_url}/search?q=a&min_rating=8.0&limit=3", timeout=5)
            if response.status_code == 200:
                self.log_result("Rating Filtering", True, "Min rating 8.0 filter works")
            else:
                self.log_result("Rating Filtering", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Rating Filtering", False, f"Error: {e}")        # Test sorting
        try:
            response = self.session.get(f"{self.api_url}/movies?sort_by=rating&sort_order=desc&limit=3", timeout=5)
            if response.status_code == 200:
                self.log_result("Sorting by Rating", True, "Rating sort works")
            else:
                self.log_result("Sorting by Rating", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Sorting by Rating", False, f"Error: {e}")

    def test_error_handling(self):
        """Test error handling"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Error Handling Tests ==={Colors.END}")

        # Test invalid endpoint
        try:
            response = self.session.get(f"{self.api_url}/nonexistent", timeout=5)
            if response.status_code == 404:
                self.log_result("404 Error Handling", True, "Invalid endpoint returns 404")
            else:
                self.log_result("404 Error Handling", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result("404 Error Handling", False, f"Error: {e}")

        # Test invalid query parameters
        try:
            response = self.session.get(f"{self.api_url}/search?limit=-1", timeout=5)
            if response.status_code == 422:
                self.log_result("Validation Error Handling", True, "Invalid parameters return 422")
            else:
                self.log_result("Validation Error Handling", False, f"Expected 422, got {response.status_code}")
        except Exception as e:
            self.log_result("Validation Error Handling", False, f"Error: {e}")

    def test_performance_benchmarks(self):
        """Test response time performance"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Performance Benchmarks ==={Colors.END}")

        # Test search response time
        start_time = time.time()
        try:
            response = self.session.get(f"{self.api_url}/search?q=avatar&limit=10", timeout=5)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200 and response_time < 1000:
                self.log_result("Search Response Time", True, f"{response_time:.2f}ms (< 1000ms)")
            else:
                self.log_result("Search Response Time", False, f"{response_time:.2f}ms (too slow)")
        except Exception as e:
            self.log_result("Search Response Time", False, f"Error: {e}")

        # Test suggestions response time
        start_time = time.time()
        try:
            response = self.session.get(f"{self.api_url}/suggestions?q=av&limit=10", timeout=5)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200 and response_time < 500:
                self.log_result("Suggestions Response Time", True, f"{response_time:.2f}ms (< 500ms)")
            else:
                self.log_result("Suggestions Response Time", False, f"{response_time:.2f}ms (too slow)")
        except Exception as e:
            self.log_result("Suggestions Response Time", False, f"Error: {e}")

    def run_all_tests(self):
        """Run complete test suite"""
        print(f"{Colors.BOLD}{Colors.PURPLE}CineFusion API Test Suite{Colors.END}")
        print(f"{Colors.BOLD}Testing server: {self.base_url}{Colors.END}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Check server connectivity first
        if not self.test_server_connectivity():
            print(f"{Colors.RED}{Colors.BOLD}Server is not accessible. Aborting tests.{Colors.END}")
            return False

        # Run all test suites
        self.test_health_endpoints()
        self.test_search_functionality()
        self.test_suggestions_functionality()
        self.test_movie_endpoints()
        self.test_filtering_and_sorting()
        self.test_error_handling()
        self.test_performance_benchmarks()

        # Print summary
        self.print_summary()

        return self.passed_tests == self.total_tests

    def print_summary(self):
        """Print test results summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Test Results Summary ==={Colors.END}")
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {Colors.GREEN}{self.passed_tests}{Colors.END}")
        print(f"Failed: {Colors.RED}{self.total_tests - self.passed_tests}{Colors.END}")

        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        if success_rate == 100:
            print(f"Success Rate: {Colors.GREEN}{success_rate:.1f}%{Colors.END}")
        elif success_rate >= 80:
            print(f"Success Rate: {Colors.YELLOW}{success_rate:.1f}%{Colors.END}")
        else:
            print(f"Success Rate: {Colors.RED}{success_rate:.1f}%{Colors.END}")

        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def export_results(self, filename: str = "test_results.json"):
        """Export test results to JSON file"""
        results = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
            },
            "test_results": self.test_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"Test results exported to: {filename}")

def main():
    """Main test runner"""
    import argparse
    import subprocess
    import threading
    import time

    parser = argparse.ArgumentParser(description="CineFusion API Test Suite")
    parser.add_argument("--url", default="http://localhost:8001", help="Base URL for API testing")
    parser.add_argument("--export", help="Export results to JSON file")
    parser.add_argument("--standalone", action="store_true", help="Start server automatically for testing")

    args = parser.parse_args()

    server_process = None

    if args.standalone:
        print("Starting server for testing...")
        try:
            # Start the server in background
            server_process = subprocess.Popen([
                sys.executable, "-c",
                "import main; import uvicorn; uvicorn.run(main.app, host='127.0.0.1', port=8001, log_level='warning')"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait for server to start
            print("Waiting for server to start...")

            # Check if server is running with more patience
            for attempt in range(20):  # Try for 20 seconds
                try:
                    response = requests.get(args.url, timeout=2)
                    if response.status_code == 200:
                        print(f"Server started successfully! (attempt {attempt + 1})")
                        break
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    if attempt < 19:  # Don't print on last attempt
                        print(f"  Waiting... (attempt {attempt + 1}/20)")
            else:
                print("Failed to connect to server after 20 attempts")
                if server_process:
                    server_process.terminate()
                sys.exit(1)

        except Exception as e:
            print(f"Failed to start server: {e}")
            if server_process:
                server_process.terminate()
            sys.exit(1)

    try:
        tester = CineFusionAPITester(args.url)
        success = tester.run_all_tests()

        if args.export:
            tester.export_results(args.export)

        return_code = 0 if success else 1

    finally:
        # Clean up server if we started it
        if server_process:
            print("Stopping test server...")
            server_process.terminate()
            server_process.wait()

    sys.exit(return_code)

if __name__ == "__main__":
    main()
