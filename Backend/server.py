#!/usr/bin/env python3
"""
CineFusion Server Manager
Comprehensive server management script for CineFusion backend
Features: JSON validation, testing, logging, and production deployment
"""

import os
import sys
import json
import time
import signal
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import custom logging
from logger import setup_logging, get_request_logger
from config import get_config, APP_CONFIG

# Initialize logging
environment = "development"  # Server management always uses development logging
loggers = setup_logging(environment=environment)
logger = loggers["app"]


class CineFusionServer:
    """Comprehensive server manager for CineFusion"""

    def __init__(self):
        self.config = get_config()
        self.processes = []
        self.shutdown_requested = False
        self.start_time = datetime.now()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("CineFusion Server Manager initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
        self.stop_server()
        sys.exit(0)

    def validate_json_config(self) -> bool:
        """Validate JSON configuration files"""
        logger.info("Validating JSON configuration...")

        # First try to load from root directory (new location)
        config_file = Path(__file__).parent.parent / "config.json"

        # Fallback to old location for compatibility
        if not config_file.exists():
            config_file = Path(__file__).parent / "data" / "config.json"

        try:
            # Check if config file exists
            if not config_file.exists():
                logger.error(f"Configuration file not found: {config_file}")
                return False

            # Load and validate JSON
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Check if it's the new unified config format
            if "backend" in config_data:
                # Validate unified config structure
                required_sections = ["application", "frontend", "backend", "admin"]
                backend_config = config_data.get("backend", {})
                backend_required = [
                    "server",
                    "api",
                    "database",
                    "logging",
                    "monitoring",
                    "cache",
                    "search",
                    "suggestions",
                    "security",
                ]
            else:
                # Legacy config format
                required_sections = [
                    "application",
                    "server",
                    "api",
                    "database",
                    "logging",
                    "monitoring",
                    "cache",
                    "search",
                    "suggestions",
                    "security",
                ]
                backend_config = config_data
                backend_required = required_sections

            missing_sections = []
            for section in required_sections:
                if section not in config_data:
                    missing_sections.append(section)

            # Check backend-specific sections if unified config
            if "backend" in config_data:
                for section in backend_required:
                    if section not in backend_config:
                        missing_sections.append(f"backend.{section}")

            if missing_sections:
                logger.error(f"Missing configuration sections: {missing_sections}")
                return False

            # Validate specific required fields
            validations = [
                ("application.name", str),
                ("application.version", str),
                ("server.default_host", str),
                ("server.default_port", int),
                ("database.csv_filename", str),
                ("api.prefix", str),
                ("logging.levels.default", str),
            ]

            for field_path, expected_type in validations:
                try:
                    keys = field_path.split(".")
                    value = config_data
                    for key in keys:
                        value = value[key]

                    if not isinstance(value, expected_type):
                        logger.error(
                            f"Invalid type for {field_path}: expected {expected_type.__name__}, got {type(value).__name__}"
                        )
                        return False

                except KeyError:
                    logger.error(f"Missing required configuration field: {field_path}")
                    return False

            # Validate file paths
            data_dir = Path(__file__).parent / "data"
            csv_file = data_dir / config_data["database"]["csv_filename"]

            if not csv_file.exists():
                logger.error(f"Movie data file not found: {csv_file}")
                return False

            logger.info("✓ JSON configuration validation passed")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return False
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def check_dependencies(self) -> bool:
        """Check system dependencies and requirements"""
        logger.info("Checking system dependencies...")

        try:
            # Check Python version
            if sys.version_info < (3, 8):
                logger.error(f"Python 3.8+ required, found {sys.version}")
                return False

            # Check required packages
            required_packages = ["fastapi", "uvicorn", "pandas", "pydantic"]

            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)

            if missing_packages:
                logger.error(f"Missing required packages: {missing_packages}")
                logger.info(
                    "Install missing packages with: pip install fastapi uvicorn pandas pydantic"
                )
                return False

            # Check data files
            data_dir = Path(__file__).parent / "data"
            required_files = ["config.json", self.config.MOVIE_CSV_PATH.name]

            for file_name in required_files:
                file_path = data_dir / file_name
                if not file_path.exists():
                    logger.error(f"Required file not found: {file_path}")
                    return False

            # Check log directory
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)

            # Check disk space
            try:
                import shutil

                disk_usage = shutil.disk_usage(".")
                free_gb = disk_usage.free / (1024**3)
                if free_gb < 1:
                    logger.warning(f"Low disk space: {free_gb:.1f}GB free")
                else:
                    logger.info(f"Disk space: {free_gb:.1f}GB free")
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")

            logger.info("✓ Dependencies check passed")
            return True

        except Exception as e:
            logger.error(f"Dependencies check failed: {e}")
            return False

    def run_tests(self, quick: bool = False) -> bool:
        """Run the test suite"""
        logger.info(f"Running {'quick' if quick else 'full'} test suite...")

        try:
            test_file = Path(__file__).parent / "test.py"
            if not test_file.exists():
                logger.error("Test file not found: test.py")
                return False

            # Run tests with standalone mode to start server automatically
            cmd = [sys.executable, str(test_file), "--standalone"]
            if quick:
                # Could add quick mode flag in future
                pass

            logger.info("Executing test suite...")
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300  # 5 minute timeout
                )

                # Log test output
                if result.stdout:
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            logger.info(f"TEST: {line}")

                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"TEST ERROR: {line}")

                if result.returncode == 0:
                    # If return code is 0, tests passed successfully
                    logger.info("✓ All tests passed successfully")
                    return True
                else:
                    logger.error(f"Tests failed with return code: {result.returncode}")
                    return False

            except subprocess.TimeoutExpired:
                logger.error("Test execution timed out")
                return False
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return False

    def start_server(
        self,
        environment: str = "development",
        host: Optional[str] = None,
        port: Optional[int] = None,
        workers: Optional[int] = None,
        daemon: bool = False,
    ) -> bool:
        """Start the FastAPI server"""

        logger.info(f"Starting CineFusion server in {environment} mode...")

        # Set environment
        os.environ["ENVIRONMENT"] = environment

        # Use provided values or defaults from config
        host = host or self.config.HOST
        port = port or self.config.PORT
        workers = workers or self.config.WORKER_COUNT

        try:
            # Build uvicorn command
            cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                str(host),
                "--port",
                str(port),
            ]

            # Add environment-specific options
            if environment == "development":
                cmd.extend(["--reload", "--log-level", "debug"])
            elif environment == "production":
                cmd.extend(
                    [
                        "--workers",
                        str(workers),
                        "--log-level",
                        "warning",
                        "--access-log",
                        "--no-access-log" if not self.config.DEBUG else "",
                    ]
                )
                # Remove empty strings
                cmd = [c for c in cmd if c]

            logger.info(f"Server command: {' '.join(cmd)}")
            logger.info(f"Server will be available at: http://{host}:{port}")
            logger.info(f"API documentation: http://{host}:{port}/docs")

            if daemon:
                # Run as daemon process
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=Path(__file__).parent,
                )
                self.processes.append(process)
                logger.info(f"Server started as daemon process (PID: {process.pid})")
                return True
            else:
                # Run in foreground
                logger.info("Starting server in foreground mode...")
                logger.info("Press Ctrl+C to stop the server")

                # Execute the server
                subprocess.run(cmd, cwd=Path(__file__).parent)
                return True

        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop all running server processes"""
        logger.info("Stopping server processes...")

        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"Process {process.pid} terminated successfully")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {process.pid} did not terminate, killing...")
                process.kill()
            except Exception as e:
                logger.error(f"Error stopping process {process.pid}: {e}")

        self.processes.clear()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        logger.info("Performing health check...")

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Check configuration
        health_status["checks"]["config"] = self.validate_json_config()

        # Check dependencies
        health_status["checks"]["dependencies"] = self.check_dependencies()

        # Check data files
        try:
            csv_path = self.config.MOVIE_CSV_PATH
            health_status["checks"]["data_file"] = csv_path.exists()
            if csv_path.exists():
                health_status["data_file_size"] = csv_path.stat().st_size
        except Exception:
            health_status["checks"]["data_file"] = False

        # Check log directory
        log_dir = Path(__file__).parent / "logs"
        health_status["checks"]["log_directory"] = log_dir.exists()

        # Overall status
        if all(health_status["checks"].values()):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "unhealthy"

        logger.info(f"Health check completed: {health_status['status']}")
        return health_status

    def show_status(self) -> Dict[str, Any]:
        """Show server status"""
        status = {
            "server_name": "CineFusion Backend",
            "version": self.config.APP_VERSION,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime": str(datetime.now() - self.start_time),
            "config": {
                "host": self.config.HOST,
                "port": self.config.PORT,
                "debug": self.config.DEBUG,
                "log_level": self.config.data.get("logging", {})
                .get("levels", {})
                .get("default", "INFO"),
            },
            "health": self.health_check(),
        }

        return status


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CineFusion Server Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
                %(prog)s validate          # Validate configuration
                %(prog)s test             # Run full test suite
                %(prog)s test --quick     # Run quick tests
                %(prog)s start            # Start development server
                %(prog)s start --prod     # Start production server
                %(prog)s start --host 0.0.0.0 --port 8080
                %(prog)s health           # Health check
                %(prog)s status           # Show status
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate JSON configuration"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument(
        "--quick", action="store_true", help="Run quick tests only"
    )

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the server")
    start_parser.add_argument("--prod", action="store_true", help="Production mode")
    start_parser.add_argument("--host", help="Host address")
    start_parser.add_argument("--port", type=int, help="Port number")
    start_parser.add_argument("--workers", type=int, help="Number of workers")
    start_parser.add_argument("--daemon", action="store_true", help="Run as daemon")

    # Health command
    health_parser = subparsers.add_parser("health", help="Health check")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show server status")

    # All command (run everything)
    all_parser = subparsers.add_parser("all", help="Validate, test, and start server")
    all_parser.add_argument("--prod", action="store_true", help="Production mode")
    all_parser.add_argument("--skip-tests", action="store_true", help="Skip tests")
    all_parser.add_argument("--host", help="Host address")
    all_parser.add_argument("--port", type=int, help="Port number")

    args = parser.parse_args()

    # Create server instance
    server = CineFusionServer()

    try:
        if args.command == "validate":
            success = server.validate_json_config()
            if success:
                print("✓ Configuration validation passed")
                sys.exit(0)
            else:
                print("✗ Configuration validation failed")
                sys.exit(1)

        elif args.command == "test":
            success = server.run_tests(quick=getattr(args, "quick", False))
            if success:
                print("✓ All tests passed")
                sys.exit(0)
            else:
                print("✗ Some tests failed")
                sys.exit(1)

        elif args.command == "start":
            environment = (
                "production" if getattr(args, "prod", False) else "development"
            )
            success = server.start_server(
                environment=environment,
                host=getattr(args, "host", None),
                port=getattr(args, "port", None),
                workers=getattr(args, "workers", None),
                daemon=getattr(args, "daemon", False),
            )
            sys.exit(0 if success else 1)

        elif args.command == "health":
            health = server.health_check()
            print(json.dumps(health, indent=2))
            sys.exit(0 if health["status"] == "healthy" else 1)

        elif args.command == "status":
            status = server.show_status()
            print(json.dumps(status, indent=2, default=str))
            sys.exit(0)

        elif args.command == "all":
            print("🚀 Starting CineFusion deployment...")

            # Step 1: Validate configuration
            print("\n1. Validating configuration...")
            if not server.validate_json_config():
                print("✗ Configuration validation failed")
                sys.exit(1)
            print("✓ Configuration valid")

            # Step 2: Check dependencies
            print("\n2. Checking dependencies...")
            if not server.check_dependencies():
                print("✗ Dependencies check failed")
                sys.exit(1)
            print("✓ Dependencies satisfied")

            # Step 3: Run tests (unless skipped)
            if not getattr(args, "skip_tests", False):
                print("\n3. Running tests...")
                if not server.run_tests():
                    print("⚠ Some tests failed, but continuing with server startup...")
                    print("  Use 'python server.py test' to see detailed test results")
                else:
                    print("✓ All tests passed")
            else:
                print("\n3. Skipping tests...")

            # Step 4: Start server
            print("\n4. Starting server...")
            environment = (
                "production" if getattr(args, "prod", False) else "development"
            )
            server.start_server(
                environment=environment,
                host=getattr(args, "host", None),
                port=getattr(args, "port", None),
            )

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
