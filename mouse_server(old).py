#!/usr/bin/env python3
"""
Desktop Mouse Server
Receives mouse commands from Flutter app and controls the computer mouse
"""

import socket
import json
import threading
import sys
import time
import logging
from typing import Dict, Any

# Cross-platform mouse control
try:
    import pyautogui
    print("✓ Using pyautogui for mouse control")
    pyautogui.FAILSAFE = False  # Disable failsafe for smooth operation
    pyautogui.PAUSE = 0  # Remove default pause between actions
except ImportError:
    print("❌ pyautogui not found. Install with: pip install pyautogui")
    sys.exit(1)

# Additional dependencies for different platforms
import platform
system = platform.system()

if system == "Linux":
    try:
        import Xlib.display
        print("✓ Linux X11 support available")
    except ImportError:
        print("⚠️  For better Linux support, install: pip install python-xlib")

class MouseServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.connected_clients = []
        self.server_thread = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        self.logger.info(f"Screen resolution: {self.screen_width}x{self.screen_height}")

    def start_server(self):
        """Start the mouse server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            local_ip = self.get_local_ip()
            self.logger.info(f"🖱️  Mouse server started on {self.host}:{self.port}")
            self.logger.info(f"📱 Connect your Flutter app to: {local_ip}:{self.port}")
            print(f"📍 Your desktop IP address is: {local_ip}")
            print(f"🔗 Use this IP in your Flutter app: {local_ip}")
            
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)  # Add timeout to make it interruptible
                    try:
                        client_socket, client_address = self.server_socket.accept()
                        self.logger.info(f"📲 Client connected from {client_address}")
                        
                        # Handle client in a separate thread
                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(client_socket, client_address)
                        )
                        client_thread.daemon = True
                        client_thread.start()
                        
                        self.connected_clients.append(client_socket)
                        
                    except socket.timeout:
                        # Timeout is expected, continue loop
                        continue
                        
                except socket.error as e:
                    if self.is_running:
                        self.logger.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket, client_address):
        """Handle individual client connections"""
        buffer = ""
        
        try:
            while self.is_running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Process complete JSON messages (separated by newlines)
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            command = json.loads(line.strip())
                            self.process_mouse_command(command)
                        except json.JSONDecodeError as e:
                            self.logger.warning(f"Invalid JSON from {client_address}: {e}")
                        except Exception as e:
                            self.logger.error(f"Error processing command: {e}")
                            
        except socket.error as e:
            self.logger.info(f"Client {client_address} disconnected: {e}")
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
            if client_socket in self.connected_clients:
                self.connected_clients.remove(client_socket)
            self.logger.info(f"🔌 Client {client_address} disconnected")

    def process_mouse_command(self, command: Dict[str, Any]):
        """Process mouse commands from the Flutter app"""
        try:
            command_type = command.get('type')
            
            if command_type == 'move':
                # Move mouse cursor
                delta_x = float(command.get('deltaX', 0))
                delta_y = float(command.get('deltaY', 0))
                
                # Get current mouse position
                current_x, current_y = pyautogui.position()
                
                # Calculate new position
                new_x = max(0, min(self.screen_width - 1, current_x + delta_x))
                new_y = max(0, min(self.screen_height - 1, current_y + delta_y))
                
                # Move mouse
                pyautogui.moveTo(new_x, new_y)
                
            elif command_type == 'click':
                # Mouse click
                button = command.get('button', 'left')
                
                if button == 'left':
                    pyautogui.click()
                elif button == 'right':
                    pyautogui.rightClick()
                elif button == 'middle':
                    pyautogui.middleClick()
                    
                self.logger.debug(f"Mouse {button} click")
                
            elif command_type == 'scroll':
                # Mouse scroll
                delta_x = float(command.get('deltaX', 0))
                delta_y = float(command.get('deltaY', 0))
                
                # Vertical scroll
                if abs(delta_y) > 1:
                    scroll_amount = int(delta_y / 10)  # Adjust sensitivity
                    pyautogui.vscroll(scroll_amount)
                
                # Horizontal scroll (if supported)
                if abs(delta_x) > 1:
                    scroll_amount = int(delta_x / 10)
                    pyautogui.hscroll(scroll_amount)
                    
                self.logger.debug(f"Mouse scroll: x={delta_x}, y={delta_y}")
                
            elif command_type == 'double_click':
                # Double click
                pyautogui.doubleClick()
                self.logger.debug("Mouse double click")
                
            else:
                self.logger.warning(f"Unknown command type: {command_type}")
                
        except Exception as e:
            self.logger.error(f"Error executing mouse command: {e}")

    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            return local_ip
        except Exception:
            return "localhost"

    def cleanup(self):
        """Clean up server resources"""
        self.is_running = False
        
        # Close all client connections
        for client in self.connected_clients:
            try:
                client.close()
            except:
                pass
        self.connected_clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            
        self.logger.info("🛑 Mouse server stopped")

    def stop(self):
        """Stop the server"""
        self.cleanup()


def main():
    """Main function"""
    print("=" * 50)
    print("🖱️  PHONE MOUSE CONTROLLER SERVER")
    print("=" * 50)
    print(f"🖥️  System: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("=" * 50)
    
    # Check dependencies
    print("📦 Checking dependencies...")
    try:
        import pyautogui
        print("   ✓ pyautogui - OK")
    except ImportError:
        print("   ❌ pyautogui - Missing! Install with: pip install pyautogui")
        return
    
    print("=" * 50)
    
    server = MouseServer()
    
    try:
        print("🚀 Starting server...")
        print("📍 Getting IP address...")
        
        # Show IP address before starting
        local_ip = server.get_local_ip()
        print(f"🌐 Your computer's IP address: {local_ip}")
        print(f"🔌 Server will listen on port: {server.port}")
        print("=" * 50)
        
        print("🎯 Server is starting...")
        print("📱 Open your Flutter app and connect to this server")
        print("⚠️  Make sure both devices are on the same WiFi network")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start server (this will block)
        server.start_server()
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.stop()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("🔍 Try running as administrator or check if port 8888 is available")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()