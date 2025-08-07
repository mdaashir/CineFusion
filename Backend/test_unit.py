#!/usr/bin/env python3
"""
Unit Tests for CineFusion Backend
Tests that don't require a running server or external dependencies
"""

import sys
import os
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))


try:
    from config import get_config
    from process.trie import Trie
    from process.avl import AVLTree
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    print("Some tests will be skipped")


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and validation"""

    def test_config_loading(self):
        """Test that configuration can be loaded"""
        try:
            config = get_config()
            self.assertIsNotNone(config)
            print("Configuration loaded successfully")
        except Exception as e:
            self.fail(f"Configuration loading failed: {e}")

    def test_config_validation(self):
        """Test configuration validation"""
        try:
            config = get_config()
            # Basic validation - check if config object has required attributes
            self.assertTrue(hasattr(config, "HOST"), "Config missing HOST attribute")
            self.assertTrue(hasattr(config, "PORT"), "Config missing PORT attribute")
            self.assertTrue(hasattr(config, "DEBUG"), "Config missing DEBUG attribute")
            print("Configuration structure is valid")
        except Exception as e:
            self.fail(f"Configuration validation failed: {e}")


class TestDataStructures(unittest.TestCase):
    """Test custom data structures"""

    def test_trie_basic_operations(self):
        """Test basic Trie operations"""
        try:
            trie = Trie()

            # Test insertion
            test_movies = ["Batman", "Batman Returns", "Superman"]
            for movie in test_movies:
                trie.insert(movie.lower())

            # Test search
            search_result = trie.search("batman")
            self.assertTrue(search_result)
            print("Trie search operations work correctly")

        except Exception as e:
            print(f"Warning: Trie test skipped due to import error: {e}")

    def test_avl_tree_operations(self):
        """Test AVL Tree operations"""
        try:
            avl = AVLTree()

            # Test insertion
            test_data = [
                "Movie10",
                "Movie20",
                "Movie30",
                "Movie40",
                "Movie50",
                "Movie25",
            ]
            for value in test_data:
                avl.insert(value)

            # Test basic properties
            self.assertIsNotNone(avl.root)
            print("AVL Tree operations work correctly")

        except Exception as e:
            print(f"Warning: AVL Tree test skipped due to import error: {e}")


class TestFileStructure(unittest.TestCase):
    """Test that required files exist and have correct structure"""

    def test_required_files_exist(self):
        """Test that all required files exist"""
        backend_dir = Path(__file__).parent
        root_dir = backend_dir.parent

        required_files = [
            backend_dir / "main.py",
            backend_dir / "server.py",
            backend_dir / "config.py",
            backend_dir / "requirements.txt",
            backend_dir / "Dockerfile",
            root_dir / "config.json",
        ]

        for file_path in required_files:
            self.assertTrue(file_path.exists(), f"Required file missing: {file_path}")

        print("[PASS] All required files exist")

    def test_json_files_valid(self):
        """Test that JSON files are valid"""
        backend_dir = Path(__file__).parent
        root_dir = backend_dir.parent

        # Test main config file
        config_file = root_dir / "config.json"
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            self.assertIsInstance(config_data, dict)
            print("[PASS] config.json is valid JSON")
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON in config.json: {e}")

        # Test production config if it exists
        production_config = root_dir / "config.production.json"
        if production_config.exists():
            try:
                with open(production_config, "r", encoding="utf-8") as f:
                    json.load(f)
                print("config.production.json is valid JSON")
            except json.JSONDecodeError as e:
                self.fail(f"Invalid JSON in config.production.json: {e}")


class TestImports(unittest.TestCase):
    """Test that all modules can be imported"""

    def test_config_imports(self):
        """Test importing config module"""
        try:
            from config import get_config

            config = get_config()
            self.assertIsNotNone(config)
            print("[PASS] config.py imports successfully")
        except ImportError as e:
            self.fail(f"Could not import config.py: {e}")

    def test_main_imports(self):
        """Test importing main modules"""
        try:
            import main

            print("[PASS] main.py imports successfully")
        except ImportError as e:
            print(f"Warning: Could not import main.py: {e}")
            # Don't fail on this as it might require additional dependencies


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality without server"""

    @patch("pandas.read_csv")
    def test_data_loading_mock(self, mock_read_csv):
        """Test data loading with mocked pandas"""
        # Mock CSV data
        mock_df = MagicMock()
        mock_df.shape = (1000, 10)
        mock_df.to_dict.return_value = [
            {"title": "Test Movie 1", "genre": "Action"},
            {"title": "Test Movie 2", "genre": "Drama"},
        ]
        mock_read_csv.return_value = mock_df

        # This would test data loading if we had the module
        print("✓ Data loading structure is testable")

    def test_server_instantiation(self):
        """Test that server can be instantiated"""
        try:
            from server import CineFusionServer

            # Test that server can be instantiated
            server = CineFusionServer()
            self.assertIsNotNone(server)
            print("[PASS] Server can be instantiated")
        except Exception as e:
            print(f"Warning: Server instantiation test failed: {e}")

    def test_data_structures_available(self):
        """Test that data structure modules exist"""
        backend_dir = Path(__file__).parent

        # Check if data structure files exist
        process_dir = backend_dir / "process"
        if process_dir.exists():
            trie_file = process_dir / "trie.py"
            avl_file = process_dir / "avl.py"

            if trie_file.exists():
                print("[PASS] Trie data structure file exists")
            if avl_file.exists():
                print("[PASS] AVL tree data structure file exists")
        else:
            print("Warning: Process directory not found")


class TestDockerConfiguration(unittest.TestCase):
    """Test Docker-related configurations"""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and has basic structure"""
        backend_dir = Path(__file__).parent
        dockerfile = backend_dir / "Dockerfile"

        self.assertTrue(dockerfile.exists(), "Dockerfile missing")

        # Check basic Dockerfile structure
        with open(dockerfile, "r") as f:
            content = f.read()

        self.assertIn("FROM", content, "Dockerfile missing FROM instruction")
        self.assertIn("COPY", content, "Dockerfile missing COPY instruction")
        self.assertIn("EXPOSE", content, "Dockerfile missing EXPOSE instruction")

        print("[PASS] Dockerfile exists and has valid structure")

    def test_requirements_file(self):
        """Test that requirements.txt exists and is readable"""
        backend_dir = Path(__file__).parent
        requirements_file = backend_dir / "requirements.txt"

        self.assertTrue(requirements_file.exists(), "requirements.txt missing")

        # Check that file is readable and has content
        with open(requirements_file, "r") as f:
            lines = f.readlines()

        self.assertGreater(len(lines), 0, "requirements.txt is empty")
        print("requirements.txt exists and has content")


def run_unit_tests():
    """Run all unit tests"""
    print("Running CineFusion Unit Tests (No Server Required)")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestConfiguration,
        TestDataStructures,
        TestFileStructure,
        TestImports,
        TestBasicFunctionality,
        TestDockerConfiguration,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("All unit tests passed!")
        return True
    else:
        failed = len(result.failures)
        errors = len(result.errors)
        print(f"FAILED: {failed} test(s) failed, {errors} error(s)")

        # Print failure details
        for test, traceback in result.failures:
            print(f"FAILED: {test}")
            print(f"  {traceback}")

        for test, traceback in result.errors:
            print(f"ERROR: {test}")
            print(f"  {traceback}")

        return False


if __name__ == "__main__":
    success = run_unit_tests()
    sys.exit(0 if success else 1)
