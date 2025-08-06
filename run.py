#!/usr/bin/env python3
"""
CineFusion Development Server
A simple HTTP server for running the CineFusion web application locally
"""

import os
import sys
import webbrowser
import http.server
import socketserver
import threading
import time
from pathlib import Path

# Configuration
DEFAULT_PORT = 8000
FRONTEND_DIR = "Frontend"


def find_project_root():
    """Find the project root directory"""
    current_dir = Path(__file__).parent.absolute()

    # Look for package.json or Frontend directory
    if (current_dir / "package.json").exists() or (current_dir / FRONTEND_DIR).exists():
        return current_dir

    # Check parent directories
    for parent in current_dir.parents:
        if (parent / "package.json").exists() or (parent / FRONTEND_DIR).exists():
            return parent

    return current_dir


def check_frontend_directory(project_root):
    """Check if frontend directory exists and has required files"""
    frontend_path = project_root / FRONTEND_DIR

    if not frontend_path.exists():
        print(f"❌ Frontend directory not found: {frontend_path}")
        return False

    index_file = frontend_path / "index.html"
    if not index_file.exists():
        print(f"❌ index.html not found in: {frontend_path}")
        return False

    print(f"✅ Frontend directory found: {frontend_path}")
    return True


def start_server(port=DEFAULT_PORT):
    """Start the development server"""
    project_root = find_project_root()

    if not check_frontend_directory(project_root):
        print("❌ Cannot start server: Frontend files not found")
        return False

    frontend_path = project_root / FRONTEND_DIR

    try:
        # Change to frontend directory
        os.chdir(frontend_path)

        # Create server
        handler = http.server.SimpleHTTPRequestHandler

        # Try to start server on the specified port
        try:
            with socketserver.TCPServer(("", port), handler) as httpd:
                server_url = f"http://localhost:{port}"

                print("🚀 CineFusion Development Server")
                print("=" * 40)
                print(f"📁 Serving: {frontend_path}")
                print(f"🌐 URL: {server_url}")
                print(f"🔗 Direct link: {server_url}/index.html")
                print("-" * 40)
                print("💡 Tips:")
                print("   • Press Ctrl+C to stop the server")
                print("   • The browser will open automatically")
                print("   • Refresh the page to see changes")
                print("=" * 40)

                # Open browser after a short delay
                def open_browser():
                    time.sleep(1.5)
                    try:
                        webbrowser.open(server_url)
                        print(f"🌐 Opened {server_url} in your default browser")
                    except Exception as e:
                        print(f"⚠️  Could not open browser automatically: {e}")
                        print(f"   Please open {server_url} manually")

                browser_thread = threading.Thread(target=open_browser)
                browser_thread.daemon = True
                browser_thread.start()

                # Start server
                print(f"🟢 Server running on port {port}...")
                httpd.serve_forever()

        except OSError as e:
            if e.errno == 98 or "Address already in use" in str(e):
                print(f"❌ Port {port} is already in use")

                # Try to find an available port
                for alt_port in range(port + 1, port + 10):
                    try:
                        with socketserver.TCPServer(("", alt_port), handler) as httpd:
                            print(f"🔄 Trying alternative port {alt_port}...")
                            return start_server(alt_port)
                    except OSError:
                        continue

                print("❌ Could not find an available port")
                return False
            else:
                raise

    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False


def main():
    """Main function"""
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number. Using default port 8000.")
            port = DEFAULT_PORT
    else:
        port = DEFAULT_PORT

    print("🎬 CineFusion Development Server Starter")
    print("=" * 45)

    success = start_server(port)

    if success:
        print("✅ Server session completed successfully")
    else:
        print("❌ Server session ended with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
