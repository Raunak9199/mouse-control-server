#!/usr/bin/env python3
"""
Desktop Mouse Server with Modern Dark Theme GUI
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

class ModernStyle:
    """Modern dark theme styling"""
    # Color palette
    COLORS = {
        'bg_primary': '#1e1e2e',      # Main background
        'bg_secondary': '#313244',     # Secondary background
        'bg_tertiary': '#45475a',      # Tertiary background
        'accent': '#89b4fa',           # Primary accent (blue)
        'accent_hover': '#74c7ec',     # Accent hover (sky)
        'success': '#a6e3a1',          # Success green
        'warning': '#fab387',          # Warning orange
        'error': '#f38ba8',            # Error red
        'text_primary': '#cdd6f4',     # Primary text
        'text_secondary': '#bac2de',   # Secondary text
        'text_muted': '#6c7086',       # Muted text
        'border': '#585b70',           # Border color
        'surface': '#181825',          # Surface color
    }

class MouseServerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📱 Phone Mouse Controller Server")
        self.root.geometry("550x750")
        self.root.resizable(True, True)
        
        # Center the main window
        self.center_window(self.root, 550, 750)
        
        # Apply modern dark theme
        self.setup_modern_theme()
        
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

    def center_window(self, window, width, height):
        """Center a window on the screen"""
        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Set window position
        window.geometry(f"{width}x{height}+{x}+{y}")

    def setup_modern_theme(self):
        """Setup modern dark theme"""
        colors = ModernStyle.COLORS
        
        # Configure root window
        self.root.configure(bg=colors['bg_primary'])
        
        # Create custom style
        self.style = ttk.Style()
        
        # Configure ttk styles for dark theme
        self.style.theme_use('clam')
        
        # Main frame style
        self.style.configure('Main.TFrame', 
                           background=colors['bg_primary'],
                           relief='flat')
        
        # Card frame style
        self.style.configure('Card.TFrame',
                           background=colors['bg_secondary'],
                           relief='solid',
                           borderwidth=1)
        
        # Label styles
        self.style.configure('Title.TLabel',
                           background=colors['bg_primary'],
                           foreground=colors['text_primary'],
                           font=('Segoe UI', 18, 'bold'))
        
        self.style.configure('Heading.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['text_primary'],
                           font=('Segoe UI', 11, 'bold'))
        
        self.style.configure('Body.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['text_secondary'],
                           font=('Segoe UI', 10))
        
        self.style.configure('Muted.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['text_muted'],
                           font=('Segoe UI', 9))
        
        # Status label styles
        self.style.configure('Success.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['success'],
                           font=('Segoe UI', 10, 'bold'))
        
        self.style.configure('Warning.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['warning'],
                           font=('Segoe UI', 10, 'bold'))
        
        self.style.configure('Error.TLabel',
                           background=colors['bg_secondary'],
                           foreground=colors['error'],
                           font=('Segoe UI', 10, 'bold'))
        
        # Button styles
        self.style.configure('Accent.TButton',
                           background=colors['accent'],
                           foreground='white',
                           font=('Segoe UI', 10, 'bold'),
                           relief='flat',
                           padding=(20, 10))
        
        self.style.map('Accent.TButton',
                      background=[('active', colors['accent_hover']),
                                ('pressed', colors['accent'])])
        
        self.style.configure('Secondary.TButton',
                           background=colors['bg_tertiary'],
                           foreground=colors['text_primary'],
                           font=('Segoe UI', 10),
                           relief='flat',
                           padding=(15, 8))
        
        self.style.map('Secondary.TButton',
                      background=[('active', colors['border']),
                                ('pressed', colors['bg_tertiary'])])
        
        self.style.configure('Success.TButton',
                           background=colors['success'],
                           foreground=colors['bg_primary'],
                           font=('Segoe UI', 10, 'bold'),
                           relief='flat',
                           padding=(20, 10))
        
        self.style.configure('Error.TButton',
                           background=colors['error'],
                           foreground='white',
                           font=('Segoe UI', 10, 'bold'),
                           relief='flat',
                           padding=(20, 10))
        
        # Entry styles
        self.style.configure('Modern.TEntry',
                           fieldbackground=colors['bg_tertiary'],
                           foreground=colors['text_primary'],
                           bordercolor=colors['border'],
                           lightcolor=colors['border'],
                           darkcolor=colors['border'],
                           font=('Consolas', 10))
        
        # LabelFrame styles
        self.style.configure('Card.TLabelframe',
                           background=colors['bg_secondary'],
                           foreground=colors['text_primary'],
                           bordercolor=colors['border'],
                           lightcolor=colors['border'],
                           darkcolor=colors['border'],
                           font=('Segoe UI', 10, 'bold'))
        
        self.style.configure('Card.TLabelframe.Label',
                           background=colors['bg_secondary'],
                           foreground=colors['text_primary'],
                           font=('Segoe UI', 10, 'bold'))

    def setup_gui(self):
        """Setup the modern GUI components"""
        colors = ModernStyle.COLORS
        
        # Main container with padding
        main_container = tk.Frame(self.root, bg=colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section
        self.create_header(main_container)
        
        # Status card
        self.create_status_card(main_container)
        
        # Connection card
        self.create_connection_card(main_container)
        
        # Control buttons
        self.create_control_buttons(main_container)
        
        # QR Code card
        self.create_qr_card(main_container)
        
        # Instructions card
        self.create_instructions_card(main_container)
        
        # Log card
        self.create_log_card(main_container)
        
        # Footer buttons
        self.create_footer_buttons(main_container)

    def create_header(self, parent):
        """Create modern header"""
        header_frame = tk.Frame(parent, bg=ModernStyle.COLORS['bg_primary'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        # Title with gradient effect simulation
        title_frame = tk.Frame(header_frame, bg=ModernStyle.COLORS['bg_primary'])
        title_frame.pack()
        
        title_label = tk.Label(title_frame, 
                              text="📱 Phone Mouse Controller",
                              font=('Segoe UI', 24, 'bold'),
                              fg=ModernStyle.COLORS['accent'],
                              bg=ModernStyle.COLORS['bg_primary'])
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Turn your phone into a wireless mouse",
                                 font=('Segoe UI', 11),
                                 fg=ModernStyle.COLORS['text_muted'],
                                 bg=ModernStyle.COLORS['bg_primary'])
        subtitle_label.pack(pady=(5, 0))

    def create_status_card(self, parent):
        """Create modern status card"""
        colors = ModernStyle.COLORS
        
        card = self.create_card(parent, "🔋 Server Status")
        
        # Status grid
        status_grid = tk.Frame(card, bg=colors['bg_secondary'])
        status_grid.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Server status
        status_row = tk.Frame(status_grid, bg=colors['bg_secondary'])
        status_row.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(status_row, text="Status:", 
                font=('Segoe UI', 10), 
                fg=colors['text_secondary'], 
                bg=colors['bg_secondary']).pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="⭕ Stopped")
        self.status_label = tk.Label(status_row, textvariable=self.status_var,
                                    font=('Segoe UI', 10, 'bold'),
                                    fg=colors['error'],
                                    bg=colors['bg_secondary'])
        self.status_label.pack(side=tk.RIGHT)
        
        # Connected clients
        clients_row = tk.Frame(status_grid, bg=colors['bg_secondary'])
        clients_row.pack(fill=tk.X)
        
        tk.Label(clients_row, text="Connected Devices:",
                font=('Segoe UI', 10),
                fg=colors['text_secondary'],
                bg=colors['bg_secondary']).pack(side=tk.LEFT)
        
        self.clients_var = tk.StringVar(value="0")
        tk.Label(clients_row, textvariable=self.clients_var,
                font=('Segoe UI', 10, 'bold'),
                fg=colors['text_primary'],
                bg=colors['bg_secondary']).pack(side=tk.RIGHT)

    def create_connection_card(self, parent):
        """Create modern connection card"""
        colors = ModernStyle.COLORS
        
        card = self.create_card(parent, "🌐 Connection Info")
        
        conn_grid = tk.Frame(card, bg=colors['bg_secondary'])
        conn_grid.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # IP Address row
        ip_row = tk.Frame(conn_grid, bg=colors['bg_secondary'])
        ip_row.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(ip_row, text="Your IP Address:",
                font=('Segoe UI', 10),
                fg=colors['text_secondary'],
                bg=colors['bg_secondary']).pack(anchor=tk.W)
        
        ip_entry_frame = tk.Frame(ip_row, bg=colors['bg_secondary'])
        ip_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.ip_var = tk.StringVar()
        ip_entry = tk.Entry(ip_entry_frame,
                           textvariable=self.ip_var,
                           font=('Consolas', 12, 'bold'),
                           bg=colors['bg_tertiary'],
                           fg=colors['accent'],
                           relief='flat',
                           state='readonly',
                           justify='center')
        ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        copy_ip_btn = tk.Button(ip_entry_frame, text="📋",
                               command=self.copy_ip,
                               bg=colors['accent'],
                               fg='white',
                               activebackground=colors['accent_hover'],
                               activeforeground='white',
                               relief='flat',
                               font=('Segoe UI', 10, 'bold'),
                               width=3,
                               cursor='hand2')
        copy_ip_btn.pack(side=tk.RIGHT)
        
        # Port row
        port_row = tk.Frame(conn_grid, bg=colors['bg_secondary'])
        port_row.pack(fill=tk.X, pady=(0, 12))
        
        tk.Label(port_row, text="Port:",
                font=('Segoe UI', 10),
                fg=colors['text_secondary'],
                bg=colors['bg_secondary']).pack(anchor=tk.W)
        
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = tk.Entry(port_row,
                             textvariable=self.port_var,
                             font=('Consolas', 11),
                             bg=colors['bg_tertiary'],
                             fg=colors['text_primary'],
                             relief='flat',
                             width=10)
        port_entry.pack(anchor=tk.W, pady=(5, 0))
        port_entry.bind('<KeyRelease>', self.on_port_change)
        
        # Full address row
        addr_row = tk.Frame(conn_grid, bg=colors['bg_secondary'])
        addr_row.pack(fill=tk.X)
        
        tk.Label(addr_row, text="Full Address:",
                font=('Segoe UI', 10),
                fg=colors['text_secondary'],
                bg=colors['bg_secondary']).pack(anchor=tk.W)
        
        addr_entry_frame = tk.Frame(addr_row, bg=colors['bg_secondary'])
        addr_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.full_address_var = tk.StringVar()
        self.update_full_address()
        
        addr_entry = tk.Entry(addr_entry_frame,
                             textvariable=self.full_address_var,
                             font=('Consolas', 12, 'bold'),
                             bg=colors['surface'],
                             fg=colors['success'],
                             relief='flat',
                             state='readonly',
                             justify='center')
        addr_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        copy_addr_btn = tk.Button(addr_entry_frame, text="📋",
                                 command=self.copy_full_address,
                                 bg=colors['success'],
                                 fg='white',
                                 activebackground='#8bc34a',
                                 activeforeground='white',
                                 relief='flat',
                                 font=('Segoe UI', 10, 'bold'),
                                 width=3,
                                 cursor='hand2')
        copy_addr_btn.pack(side=tk.RIGHT)

    def create_control_buttons(self, parent):
        """Create modern control buttons"""
        colors = ModernStyle.COLORS
        
        btn_frame = tk.Frame(parent, bg=colors['bg_primary'])
        btn_frame.pack(pady=20)
        
        # Start button
        self.start_button = tk.Button(btn_frame,
                                     text="🚀 Start Server",
                                     command=self.start_server,
                                     bg=colors['success'],
                                     fg='white',
                                     activebackground='#8bc34a',
                                     activeforeground='white',
                                     font=('Segoe UI', 12, 'bold'),
                                     relief='flat',
                                     padx=25,
                                     pady=12,
                                     cursor='hand2')
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Stop button
        self.stop_button = tk.Button(btn_frame,
                                    text="⏹️ Stop Server",
                                    command=self.stop_server,
                                    bg=colors['error'],
                                    fg='white',
                                    activebackground='#e57373',
                                    activeforeground='white',
                                    font=('Segoe UI', 12, 'bold'),
                                    relief='flat',
                                    padx=25,
                                    pady=12,
                                    state='disabled',
                                    cursor='hand2')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Refresh IP button
        refresh_btn = tk.Button(btn_frame,
                               text="🔄 Refresh IP",
                               command=self.refresh_ip,
                               bg=colors['bg_tertiary'],
                               fg=colors['text_primary'],
                               activebackground=colors['border'],
                               activeforeground='white',
                               font=('Segoe UI', 11, 'bold'),
                               relief='flat',
                               padx=20,
                               pady=12,
                               cursor='hand2')
        refresh_btn.pack(side=tk.LEFT)

    def create_qr_card(self, parent):
        """Create modern QR code card"""
        colors = ModernStyle.COLORS
        
        self.qr_card = self.create_card(parent, "📷 Quick Connect QR Code")
        
        qr_container = tk.Frame(self.qr_card, bg=colors['bg_secondary'])
        qr_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.qr_label = tk.Label(qr_container,
                                text="Start server to generate QR code",
                                font=('Segoe UI', 11),
                                fg=colors['text_muted'],
                                bg=colors['bg_secondary'])
        self.qr_label.pack(pady=10)

    def create_instructions_card(self, parent):
        """Create modern instructions card"""
        colors = ModernStyle.COLORS
        
        card = self.create_card(parent, "📖 Quick Setup Guide")
        
        instr_frame = tk.Frame(card, bg=colors['bg_secondary'])
        instr_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        instructions = [
            "1. Click 'Start Server' to begin",
            "2. Install 'Phone Mouse Controller' app on your phone",
            "3. Scan QR code or enter the IP address in the app",
            "4. Tap 'Connect' in the mobile app",
            "5. Use your phone as a wireless mouse!"
        ]
        
        for i, instruction in enumerate(instructions):
            instr_label = tk.Label(instr_frame,
                                  text=instruction,
                                  font=('Segoe UI', 10),
                                  fg=colors['text_secondary'],
                                  bg=colors['bg_secondary'],
                                  anchor='w')
            instr_label.pack(fill=tk.X, pady=2)
        
        # Network note
        note_frame = tk.Frame(instr_frame, bg=colors['bg_tertiary'])
        note_frame.pack(fill=tk.X, pady=(10, 0))
        
        note_label = tk.Label(note_frame,
                             text="💡 Ensure both devices are on the same WiFi network",
                             font=('Segoe UI', 10, 'italic'),
                             fg=colors['warning'],
                             bg=colors['bg_tertiary'])
        note_label.pack(pady=8)

    def create_log_card(self, parent):
        """Create modern log card"""
        colors = ModernStyle.COLORS
        
        card = self.create_card(parent, "📝 Server Log")
        
        log_frame = tk.Frame(card, bg=colors['bg_secondary'])
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 height=8,
                                                 bg=colors['surface'],
                                                 fg=colors['text_secondary'],
                                                 font=('Consolas', 9),
                                                 relief='flat',
                                                 wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_footer_buttons(self, parent):
        """Create modern footer buttons"""
        colors = ModernStyle.COLORS
        
        footer_frame = tk.Frame(parent, bg=colors['bg_primary'])
        footer_frame.pack(pady=(15, 0))
        
        buttons = [
            ("📱 Download App", self.open_app_download, colors['accent']),
            ("❓ Help", self.show_help, colors['bg_tertiary']),
            ("ℹ️ About", self.show_about, colors['bg_tertiary'])
        ]
        
        for text, command, bg_color in buttons:
            fg_color = 'white'
            active_bg = colors['accent_hover'] if bg_color == colors['accent'] else colors['border']
            btn = tk.Button(footer_frame,
                           text=text,
                           command=command,
                           bg=bg_color,
                           fg=fg_color,
                           activebackground=active_bg,
                           activeforeground='white',
                           font=('Segoe UI', 10, 'bold'),
                           relief='flat',
                           padx=15,
                           pady=8,
                           cursor='hand2')
            btn.pack(side=tk.LEFT, padx=(0, 10))

    def create_card(self, parent, title):
        """Create a modern card container"""
        colors = ModernStyle.COLORS
        
        # Card container with shadow effect
        card_container = tk.Frame(parent, bg=colors['bg_primary'])
        card_container.pack(fill=tk.X, pady=(0, 15))
        
        # Card with border
        card = tk.Frame(card_container,
                       bg=colors['bg_secondary'],
                       relief='solid',
                       bd=1,
                       highlightbackground=colors['border'],
                       highlightthickness=1)
        card.pack(fill=tk.X)
        
        # Card header
        header = tk.Frame(card, bg=colors['bg_secondary'])
        header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        title_label = tk.Label(header,
                              text=title,
                              font=('Segoe UI', 12, 'bold'),
                              fg=colors['text_primary'],
                              bg=colors['bg_secondary'])
        title_label.pack(anchor=tk.W)
        
        return card

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
        if self.is_running:
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
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image with dark theme colors
            qr_image = qr.make_image(fill_color=ModernStyle.COLORS['text_primary'], 
                                   back_color=ModernStyle.COLORS['surface'])
            qr_image = qr_image.resize((160, 160))
            
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
            self.status_label.configure(fg=ModernStyle.COLORS['success'])
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            
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
        self.status_label.configure(fg=ModernStyle.COLORS['error'])
        self.clients_var.set("0")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        self.qr_label.configure(image="", text="Start server to generate QR code")
        self.logger.info("Server stopped")

    def update_client_count(self, count):
        """Update connected client count"""
        self.connected_clients = count
        self.clients_var.set(str(count))

    def show_message(self, message):
        """Show info message with dark theme"""
        msg_box = tk.Toplevel(self.root)
        msg_box.title("Info")
        msg_box.configure(bg=ModernStyle.COLORS['bg_secondary'])
        msg_box.geometry("350x180")
        msg_box.resizable(False, False)
        
        # Center the dialog
        self.center_window(msg_box, 350, 180)
        
        # Make modal
        msg_box.transient(self.root)
        msg_box.grab_set()
        
        # Content frame
        content_frame = tk.Frame(msg_box, bg=ModernStyle.COLORS['bg_secondary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Icon
        icon_label = tk.Label(content_frame, text="ℹ️",
                             font=('Segoe UI', 32),
                             bg=ModernStyle.COLORS['bg_secondary'],
                             fg=ModernStyle.COLORS['accent'])
        icon_label.pack(pady=(0, 10))
        
        # Message
        label = tk.Label(content_frame, text=message,
                        bg=ModernStyle.COLORS['bg_secondary'],
                        fg=ModernStyle.COLORS['text_primary'],
                        font=('Segoe UI', 11),
                        wraplength=300,
                        justify=tk.CENTER)
        label.pack(pady=(0, 20))
        
        # OK button
        ok_btn = tk.Button(content_frame, text="OK",
                          command=msg_box.destroy,
                          bg=ModernStyle.COLORS['accent'],
                          fg='white',
                          activebackground=ModernStyle.COLORS['accent_hover'],
                          activeforeground='white',
                          font=('Segoe UI', 10, 'bold'),
                          relief='flat',
                          padx=30,
                          pady=10,
                          cursor='hand2')
        ok_btn.pack()
        
        # Focus on OK button
        ok_btn.focus_set()
        msg_box.bind('<Return>', lambda e: msg_box.destroy())
        msg_box.bind('<Escape>', lambda e: msg_box.destroy())

    def show_error(self, message):
        """Show error message with dark theme"""
        msg_box = tk.Toplevel(self.root)
        msg_box.title("Error")
        msg_box.configure(bg=ModernStyle.COLORS['bg_secondary'])
        msg_box.geometry("400x200")
        msg_box.resizable(False, False)
        
        # Center the dialog
        self.center_window(msg_box, 400, 200)
        
        # Make modal
        msg_box.transient(self.root)
        msg_box.grab_set()
        
        # Content frame
        content_frame = tk.Frame(msg_box, bg=ModernStyle.COLORS['bg_secondary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Error icon
        icon_label = tk.Label(content_frame, text="❌",
                             font=('Segoe UI', 32),
                             bg=ModernStyle.COLORS['bg_secondary'],
                             fg=ModernStyle.COLORS['error'])
        icon_label.pack(pady=(0, 10))
        
        # Error message
        label = tk.Label(content_frame, text=message,
                        bg=ModernStyle.COLORS['bg_secondary'],
                        fg=ModernStyle.COLORS['text_primary'],
                        font=('Segoe UI', 11),
                        wraplength=350,
                        justify=tk.CENTER)
        label.pack(pady=(0, 20))
        
        # OK button
        ok_btn = tk.Button(content_frame, text="OK",
                          command=msg_box.destroy,
                          bg=ModernStyle.COLORS['error'],
                          fg='white',
                          activebackground='#e57373',
                          activeforeground='white',
                          font=('Segoe UI', 10, 'bold'),
                          relief='flat',
                          padx=30,
                          pady=10,
                          cursor='hand2')
        ok_btn.pack()
        
        # Focus on OK button
        ok_btn.focus_set()
        msg_box.bind('<Return>', lambda e: msg_box.destroy())
        msg_box.bind('<Escape>', lambda e: msg_box.destroy())

    def open_app_download(self):
        """Open app download page"""
        webbrowser.open("https://github.com/yourusername/phone-mouse-controller")

    def show_help(self):
        """Show help dialog with dark theme"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Help - Phone Mouse Controller")
        help_window.configure(bg=ModernStyle.COLORS['bg_primary'])
        help_window.geometry("600x700")
        
        # Center the window
        self.center_window(help_window, 600, 700)
        help_window.transient(self.root)
        
        # Create scrollable content
        canvas = tk.Canvas(help_window, bg=ModernStyle.COLORS['bg_primary'])
        scrollbar = ttk.Scrollbar(help_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernStyle.COLORS['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Help content
        help_content = """Phone Mouse Controller Help

SETUP INSTRUCTIONS:
1. Click 'Start Server' to begin
2. Note the IP address displayed
3. Install the mobile app on your phone
4. Enter the IP address in the app or scan QR code
5. Tap 'Connect' in the mobile app

TROUBLESHOOTING:
• Both devices must be on same WiFi network
• Try 'Refresh IP' if connection fails
• Check Windows Firewall settings
• Some routers block device communication
• Make sure port 8888 is not blocked

MOBILE APP CONTROLS:
• Move finger on trackpad = move cursor
• Tap trackpad = left click
• Left Click button = left click
• Right Click button = right click
• Scroll area = scroll up/down

TECHNICAL INFO:
• Default port: 8888
• Protocol: TCP Socket
• Data format: JSON

For more help and source code:
github.com/yourusername/phone-mouse-controller"""
        
        help_label = tk.Label(scrollable_frame,
                             text=help_content,
                             font=('Segoe UI', 10),
                             fg=ModernStyle.COLORS['text_secondary'],
                             bg=ModernStyle.COLORS['bg_primary'],
                             justify=tk.LEFT,
                             anchor='nw')
        help_label.pack(padx=20, pady=20, fill=tk.BOTH)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def show_about(self):
        """Show about dialog with dark theme"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About - Phone Mouse Controller")
        about_window.configure(bg=ModernStyle.COLORS['bg_secondary'])
        about_window.geometry("450x350")
        about_window.resizable(False, False)
        
        # Center the window
        self.center_window(about_window, 450, 350)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Content frame
        content_frame = tk.Frame(about_window, bg=ModernStyle.COLORS['bg_secondary'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # App icon/title
        title_label = tk.Label(content_frame,
                              text="📱 Phone Mouse Controller",
                              font=('Segoe UI', 16, 'bold'),
                              fg=ModernStyle.COLORS['accent'],
                              bg=ModernStyle.COLORS['bg_secondary'])
        title_label.pack(pady=(0, 10))
        
        version_label = tk.Label(content_frame,
                                text="Server v1.0",
                                font=('Segoe UI', 12),
                                fg=ModernStyle.COLORS['text_primary'],
                                bg=ModernStyle.COLORS['bg_secondary'])
        version_label.pack(pady=(0, 20))
        
        desc_label = tk.Label(content_frame,
                             text="Turn your phone into a wireless mouse!\n\nFeatures:\n• Wireless mouse control\n• Left & right click\n• Scroll functionality\n• QR code connection\n• Modern dark theme",
                             font=('Segoe UI', 10),
                             fg=ModernStyle.COLORS['text_secondary'],
                             bg=ModernStyle.COLORS['bg_secondary'],
                             justify=tk.CENTER)
        desc_label.pack(pady=(0, 20))
        
        system_info = f"System: {platform.system()} {platform.release()}\nPython: {sys.version.split()[0]}"
        sys_label = tk.Label(content_frame,
                            text=system_info,
                            font=('Consolas', 9),
                            fg=ModernStyle.COLORS['text_muted'],
                            bg=ModernStyle.COLORS['bg_secondary'])
        sys_label.pack(pady=(0, 20))
        
        # Close button
        close_btn = tk.Button(content_frame,
                             text="Close",
                             command=about_window.destroy,
                             bg=ModernStyle.COLORS['accent'],
                             fg='white',
                             activebackground=ModernStyle.COLORS['accent_hover'],
                             activeforeground='white',
                             font=('Segoe UI', 10, 'bold'),
                             relief='flat',
                             padx=30,
                             pady=10,
                             cursor='hand2')
        close_btn.pack()
        
        # Focus and keyboard bindings
        close_btn.focus_set()
        about_window.bind('<Return>', lambda e: about_window.destroy())
        about_window.bind('<Escape>', lambda e: about_window.destroy())

    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            result = messagebox.askyesno("Quit", 
                                       "Server is running. Stop server and quit?",
                                       icon='question')
            if result:
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
        def append():
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.update()
        
        # Make sure we're in the main thread
        try:
            append()
        except:
            pass


class MouseServer:
    """Mouse server for handling phone connections"""
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
            self.logger.info(f"Server listening on port {self.port}")
            
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
                            self.logger.error(f"Accept error: {e}")
                        break
                        
                except Exception as e:
                    if self.is_running:
                        self.logger.error(f"Server error: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket, client_address):
        """Handle client connection"""
        buffer = ""
        try:
            while self.is_running:
                try:
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
                            except json.JSONDecodeError as e:
                                self.logger.error(f"JSON decode error: {e}")
                            except Exception as e:
                                self.logger.error(f"Command processing error: {e}")
                                
                except socket.timeout:
                    continue
                except socket.error:
                    break
                except Exception as e:
                    self.logger.error(f"Client handling error: {e}")
                    break
                    
        except Exception as e:
            self.logger.info(f"Client {client_address[0]} disconnected")
        finally:
            try:
                client_socket.close()
            except:
                pass
            
            if client_socket in self.connected_clients:
                self.connected_clients.remove(client_socket)
                if self.gui:
                    self.gui.update_client_count(len(self.connected_clients))

    def process_mouse_command(self, command):
        """Process mouse commands from phone"""
        try:
            command_type = command.get('type')
            
            if command_type == 'move':
                delta_x = float(command.get('deltaX', 0))
                delta_y = float(command.get('deltaY', 0))
                
                # Get current position and calculate new position
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
                    # Convert scroll delta to scroll amount
                    scroll_amount = max(-10, min(10, int(delta_y / 5)))
                    if scroll_amount != 0:
                        pyautogui.scroll(scroll_amount)
                        
        except Exception as e:
            self.logger.error(f"Mouse command error: {e}")

    def stop(self):
        """Stop the server"""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
    def cleanup(self):
        """Cleanup resources"""
        for client in self.connected_clients[:]:  # Copy list to avoid modification during iteration
            try:
                client.close()
            except:
                pass
        self.connected_clients.clear()
        
        if self.gui:
            self.gui.update_client_count(0)


if __name__ == "__main__":
    # Check if required packages are available
    missing_packages = []
    
    try:
        import tkinter
    except ImportError:
        missing_packages.append("tkinter (should be included with Python)")
    
    try:
        import PIL
    except ImportError:
        missing_packages.append("pillow")
    
    try:
        import qrcode
    except ImportError:
        missing_packages.append("qrcode[pil]")
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install pillow qrcode[pil]")
        sys.exit(1)
    
    print("🚀 Starting Phone Mouse Controller Server...")
    app = MouseServerGUI()
    app.run()