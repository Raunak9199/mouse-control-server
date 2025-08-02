#!/usr/bin/env python3
"""
Desktop Mouse Server with GUI
Easy-to-use desktop application for end users
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import json
import threading
import sys
import time
import logging
import platform
import webbrowser
from typing import Dict, Any
import qrcode
from PIL import Image, ImageTk
import io

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
except ImportError:
    print("❌ pyautogui not found. Install with: pip install pyautogui")
    sys.exit(1)

class MouseServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Phone Mouse Controller Server")
        self.root.geometry("500x700")
        self.root.resizable(True, True)
        
        # Server settings
        self.server = None
        self.is_running = False
        self.port = 8888
        self.connected_clients = 0
        
        # Setup GUI
        self.setup_gui()
        self.setup_logging()
        
        # Get initial IP
        self.local_ip = self.get_local_ip()
        self.ip_var.set(self.local_ip)
        
        # Protocol for window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="📱 Phone Mouse Controller", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Status indicator
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_var = tk.StringVar(value="⭕ Stopped")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Client count
        ttk.Label(status_frame, text="Connected:").grid(row=1, column=0, sticky=tk.W)
        self.clients_var = tk.StringVar(value="0 devices")
        ttk.Label(status_frame, textvariable=self.clients_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Connection Info", padding="10")
        conn_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        conn_frame.columnconfigure(1, weight=1)
        
        # IP Address
        ttk.Label(conn_frame, text="Your IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_var = tk.StringVar()
        ip_frame = ttk.Frame(conn_frame)
        ip_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        ip_frame.columnconfigure(0, weight=1)
        
        self.ip_entry = ttk.Entry(ip_frame, textvariable=self.ip_var, state="readonly", 
                                 font=("Courier", 10))
        self.ip_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(ip_frame, text="📋", command=self.copy_ip, width=3).grid(row=0, column=1)
        
        # Port
        ttk.Label(conn_frame, text="Port:").grid(row=1, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(self.port))
        port_frame = ttk.Frame(conn_frame)
        port_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        self.port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        self.port_entry.grid(row=0, column=0, sticky=tk.W)
        self.port_entry.bind('<KeyRelease>', self.on_port_change)
        
        # Full address
        ttk.Label(conn_frame, text="Full Address:").grid(row=2, column=0, sticky=tk.W)
        self.full_address_var = tk.StringVar()
        self.update_full_address()
        full_addr_frame = ttk.Frame(conn_frame)
        full_addr_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        full_addr_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(full_addr_frame, textvariable=self.full_address_var, state="readonly",
                 font=("Courier", 10, "bold")).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(full_addr_frame, text="📋", command=self.copy_full_address, width=3).grid(row=0, column=1)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="🚀 Start Server", 
                                      command=self.start_server, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ Stop Server", 
                                     command=self.stop_server, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="🔄 Refresh IP", 
                  command=self.refresh_ip).pack(side=tk.LEFT)
        
        # QR Code section
        qr_frame = ttk.LabelFrame(main_frame, text="Quick Connect", padding="10")
        qr_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.qr_label = ttk.Label(qr_frame, text="Start server to generate QR code")
        self.qr_label.pack()
        
        # Instructions
        instr_frame = ttk.LabelFrame(main_frame, text="Instructions", padding="10")
        instr_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        instructions = """1. Click 'Start Server' to begin
2. Install the 'Phone Mouse Controller' app on your phone
3. Enter the IP address shown above in the app
4. Tap 'Connect' in the app
5. Use your phone as a wireless mouse!

💡 Make sure both devices are on the same WiFi network"""
        
        ttk.Label(instr_frame, text=instructions, justify=tk.LEFT).pack(anchor=tk.W)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Server Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=60)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=7, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(bottom_frame, text="📱 Download App", 
                  command=self.open_app_download).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="❓ Help", 
                  command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(bottom_frame, text="ℹ️ About", 
                  command=self.show_about).pack(side=tk.LEFT)

    def setup_logging(self):
        """Setup logging to display in GUI"""
        self.log_handler = GUILogHandler(self.log_text)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%H:%M:%S',
            handlers=[self.log_handler]
        )
        self.logger = logging.getLogger(__name__)

    def get_local_ip(self):
        """Get the local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    def update_full_address(self):
        """Update the full address display"""
        self.full_address_var.set(f"{self.ip_var.get()}:{self.port_var.get()}")

    def on_port_change(self, event):
        """Handle port change"""
        try:
            self.port = int(self.port_var.get())
            self.update_full_address()
        except ValueError:
            pass

    def copy_ip(self):
        """Copy IP to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.ip_var.get())
        self.show_message("IP address copied to clipboard!")

    def copy_full_address(self):
        """Copy full address to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.full_address_var.get())
        self.show_message("Full address copied to clipboard!")

    def refresh_ip(self):
        """Refresh IP address"""
        self.local_ip = self.get_local_ip()
        self.ip_var.set(self.local_ip)
        self.update_full_address()
        self.generate_qr_code()
        self.show_message("IP address refreshed!")

    def generate_qr_code(self):
        """Generate QR code for easy connection"""
        if not self.is_running:
            return
            
        try:
            # Create connection info for QR code
            connection_info = {
                "ip": self.ip_var.get(),
                "port": int(self.port_var.get()),
                "name": platform.node()
            }
            
            qr_data = json.dumps(connection_info)
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=3, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_image = qr_image.resize((150, 150))
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(qr_image)
            self.qr_label.configure(image=photo, text="")
            self.qr_label.image = photo  # Keep a reference
            
        except Exception as e:
            self.qr_label.configure(text=f"QR generation failed: {e}", image="")

    def start_server(self):
        """Start the mouse server"""
        try:
            self.port = int(self.port_var.get())
            self.server = MouseServer(port=self.port, gui=self)
            
            # Start server in thread
            self.server_thread = threading.Thread(target=self.server.start_server)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.is_running = True
            self.status_var.set("🟢 Running")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.port_entry.configure(state="disabled")
            
            self.generate_qr_code()
            self.logger.info(f"Server started on {self.local_ip}:{self.port}")
            
        except Exception as e:
            self.show_error(f"Failed to start server: {e}")

    def stop_server(self):
        """Stop the mouse server"""
        if self.server:
            self.server.stop()
            
        self.is_running = False
        self.connected_clients = 0
        self.status_var.set("⭕ Stopped")
        self.clients_var.set("0 devices")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.port_entry.configure(state="normal")
        
        self.qr_label.configure(image="", text="Start server to generate QR code")
        self.logger.info("Server stopped")

    def update_client_count(self, count):
        """Update connected client count"""
        self.connected_clients = count
        self.clients_var.set(f"{count} device{'s' if count != 1 else ''}")

    def show_message(self, message):
        """Show info message"""
        messagebox.showinfo("Info", message)

    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)

    def open_app_download(self):
        """Open app download page"""
        # This would link to your app store page
        webbrowser.open("https://github.com/yourusername/phone-mouse-controller")

    def show_help(self):
        """Show help dialog"""
        help_text = """Phone Mouse Controller Help

SETUP:
1. Click 'Start Server' to begin
2. Note the IP address displayed
3. Install the mobile app on your phone
4. Enter the IP address in the app
5. Tap 'Connect'

TROUBLESHOOTING:
• Both devices must be on same WiFi network
• Try 'Refresh IP' if connection fails
• Check Windows Firewall settings
• Some routers block device communication

CONTROLS:
• Move finger on phone = move cursor
• Tap phone screen = left click
• Use app buttons for right click
• Scroll area for page scrolling

For more help, visit: github.com/yourusername/phone-mouse-controller"""
        
        messagebox.showinfo("Help", help_text)

    def show_about(self):
        """Show about dialog"""
        about_text = f"""Phone Mouse Controller Server v1.0

Turn your phone into a wireless mouse!

System: {platform.system()} {platform.release()}
Python: {sys.version.split()[0]}

© 2024 Your Name
Open Source Project"""
        
        messagebox.showinfo("About", about_text)

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Server is running. Stop and quit?"):
                self.stop_server()
                time.sleep(0.5)  # Give time to cleanup
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        """Run the GUI"""
        self.root.mainloop()


class GUILogHandler(logging.Handler):
    """Custom log handler for GUI"""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.see(tk.END)
        self.text_widget.update()


class MouseServer:
    """Simplified mouse server for GUI"""
    def __init__(self, port=8888, gui=None):
        self.port = port
        self.gui = gui
        self.server_socket = None
        self.is_running = False
        self.connected_clients = []
        
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        self.logger = logging.getLogger(__name__)

    def start_server(self):
        """Start the server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)
                    try:
                        client_socket, client_address = self.server_socket.accept()
                        self.logger.info(f"Client connected: {client_address[0]}")
                        
                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(client_socket, client_address)
                        )
                        client_thread.daemon = True
                        client_thread.start()
                        
                        self.connected_clients.append(client_socket)
                        if self.gui:
                            self.gui.update_client_count(len(self.connected_clients))
                            
                    except socket.timeout:
                        continue
                        
                except socket.error as e:
                    if self.is_running:
                        self.logger.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        buffer = ""
        try:
            while self.is_running:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            command = json.loads(line.strip())
                            self.process_mouse_command(command)
                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            self.logger.error(f"Command error: {e}")
                            
        except Exception as e:
            self.logger.info(f"Client disconnected: {client_address[0]}")
        finally:
            client_socket.close()
            if client_socket in self.connected_clients:
                self.connected_clients.remove(client_socket)
                if self.gui:
                    self.gui.update_client_count(len(self.connected_clients))

    def process_mouse_command(self, command):
        """Process mouse commands"""
        try:
            command_type = command.get('type')
            
            if command_type == 'move':
                delta_x = float(command.get('deltaX', 0))
                delta_y = float(command.get('deltaY', 0))
                
                current_x, current_y = pyautogui.position()
                new_x = max(0, min(self.screen_width - 1, current_x + delta_x))
                new_y = max(0, min(self.screen_height - 1, current_y + delta_y))
                
                pyautogui.moveTo(new_x, new_y)
                
            elif command_type == 'click':
                button = command.get('button', 'left')
                if button == 'left':
                    pyautogui.click()
                elif button == 'right':
                    pyautogui.rightClick()
                    
            elif command_type == 'scroll':
                delta_y = float(command.get('deltaY', 0))
                if abs(delta_y) > 1:
                    # scroll_amount = int(delta_y / 10)
                    scroll_amount = max(-15, min(15, int(delta_y / 3))) 
                    pyautogui.vscroll(scroll_amount)
                    
        except Exception as e:
            self.logger.error(f"Mouse command error: {e}")

    def stop(self):
        """Stop the server"""
        self.is_running = False
        
    def cleanup(self):
        """Cleanup resources"""
        for client in self.connected_clients:
            try:
                client.close()
            except:
                pass
        self.connected_clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass


if __name__ == "__main__":
    # Check if required packages are available
    try:
        import tkinter
        import PIL
        import qrcode
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Install with: pip install pillow qrcode[pil]")
        sys.exit(1)
    
    app = MouseServerGUI()
    app.run()