"""
Rust Auto-Connect Plugin
Launches Rust and connects to a server when raid alert is received
"""

import subprocess
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                                QLineEdit, QLabel, QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from plugin_base import PluginBase

class Plugin(PluginBase):
    """Plugin to launch Rust and auto-connect to server"""
    
    def __init__(self, telegram_service, config: dict):
        super().__init__(telegram_service, config)
        self.enabled = False
        
        # Default settings
        self.server_ip = self.config.get("rust_server_ip", "192.168.1.50")
        self.server_port = self.config.get("rust_server_port", "28015")
        
        # Create widget
        self._widget = None
    
    def get_name(self) -> str:
        """Return plugin name"""
        return "Rust Auto-Connect"
    
    def get_icon(self) -> str:
        """Return plugin icon"""
        return "🎮"
    
    def get_widget(self) -> QWidget:
        """Return plugin widget"""
        if self._widget is None:
            self._widget = self._build_ui()
        return self._widget
    
    def get_description(self) -> str:
        """Return plugin description"""
        return "Automatically launch Rust and connect to your server on raid alerts"
    
    def _build_ui(self):
        """Build the UI"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Header
        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        # Title row with help button
        title_row = QHBoxLayout()
        
        title = QLabel("🎮 Rust Auto-Connect")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        title_row.addWidget(title)
        
        help_btn = QPushButton("❓")
        help_btn.setFont(QFont("Segoe UI", 14))
        help_btn.setMaximumWidth(35)
        help_btn.setMaximumHeight(35)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 17px;
                color: #d4d4d4;
            }
            QPushButton:hover {
                background-color: #3e3e42;
            }
        """)
        help_btn.clicked.connect(self.show_help)
        title_row.addWidget(help_btn)
        title_row.addStretch()
        
        header_layout.addLayout(title_row)
        
        subtitle = QLabel("Launch Rust and auto-connect to your server on raid alerts")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Server Configuration Group
        server_group = QGroupBox("Server Configuration")
        server_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        server_group.setStyleSheet(self.get_groupbox_style())
        server_layout = QVBoxLayout(server_group)
        
        # Server IP
        ip_row = QHBoxLayout()
        ip_label = QLabel("Server IP:")
        ip_label.setMinimumWidth(120)
        ip_label.setFont(QFont("Segoe UI", 10))
        ip_row.addWidget(ip_label)
        
        self.ip_input = QLineEdit()
        self.ip_input.setText(self.server_ip)
        self.ip_input.setPlaceholderText("192.168.1.50 or play.example.com")
        self.ip_input.setMinimumHeight(32)
        self.ip_input.textChanged.connect(self.on_ip_changed)
        ip_row.addWidget(self.ip_input)
        
        server_layout.addLayout(ip_row)
        
        # Server Port
        port_row = QHBoxLayout()
        port_label = QLabel("Server Port:")
        port_label.setMinimumWidth(120)
        port_label.setFont(QFont("Segoe UI", 10))
        port_row.addWidget(port_label)
        
        self.port_input = QLineEdit()
        self.port_input.setText(self.server_port)
        self.port_input.setPlaceholderText("28015")
        self.port_input.setMinimumHeight(32)
        self.port_input.textChanged.connect(self.on_port_changed)
        port_row.addWidget(self.port_input)
        
        server_layout.addLayout(port_row)
        
        layout.addWidget(server_group)
        
        # Test Button
        test_frame = QFrame()
        test_frame.setObjectName("card")
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(16, 16, 16, 16)
        
        test_btn = QPushButton("🎮 Test Connection")
        test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        test_btn.setMinimumHeight(48)
        test_btn.setStyleSheet(self.get_button_style("#ce422b"))  # Rust red color
        test_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(test_btn)
        
        self.status_label = QLabel("Ready to launch Rust on raid alerts")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888888; padding: 10px;")
        test_layout.addWidget(self.status_label)
        
        layout.addWidget(test_frame)
        layout.addStretch()
        
        return widget
    
    def on_ip_changed(self, text):
        """Update server IP"""
        self.server_ip = text
        self.config["rust_server_ip"] = text
    
    def on_port_changed(self, text):
        """Update server port"""
        self.server_port = text
        self.config["rust_server_port"] = text
    
    def test_connection(self):
        """Test launching Rust with current settings"""
        if not self.validate_settings():
            return
        
        self.status_label.setText("🚀 Launching Rust...")
        self.status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        
        try:
            self.launch_rust()
            self.status_label.setText("✅ Rust launched successfully!")
            self.status_label.setStyleSheet("color: #44ff44; padding: 10px;")
            
            QMessageBox.information(
                self._widget,
                "Success",
                f"Rust is launching and connecting to:\n{self.server_ip}:{self.server_port}\n\nCheck your game!"
            )
        except Exception as e:
            self.status_label.setText(f"❌ Launch failed")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            
            QMessageBox.critical(
                self._widget,
                "Error",
                f"Failed to launch Rust:\n{str(e)}\n\nCheck your Steam path and try again."
            )
    
    def validate_settings(self):
        """Validate settings before launch"""
        if not self.server_ip:
            QMessageBox.warning(self._widget, "Missing Settings", "Please enter a server IP address")
            return False
        
        if not self.server_port:
            QMessageBox.warning(self._widget, "Missing Settings", "Please enter a server port")
            return False
        
        return True
    
    def launch_rust(self):
        """Launch Rust and connect to server using steam://run protocol"""
        # Use steam://run/APPID//+connect%20IP:PORT
        # 252490 is Rust's Steam App ID
        # URL encode the +connect command
        rust_app_id = "252490"
        connect_command = f"+connect%20{self.server_ip}:{self.server_port}"
        
        # Format: steam://run/252490//+connect%20IP:PORT
        steam_url = f"steam://run/{rust_app_id}//{connect_command}"
        
        print(f"[Rust Auto-Connect] Opening Steam URL: {steam_url}")
        
        # Use os.startfile to open the steam:// URL
        os.startfile(steam_url)
        
        print(f"[Rust Auto-Connect] Launched Rust connecting to {self.server_ip}:{self.server_port}")
    
    def on_telegram_message(self, message: str):
        """Called when Telegram message received - launch Rust"""
        print(f"[Rust Auto-Connect] on_telegram_message called. Enabled: {self.enabled}, Message: {message}")
        
        if not self.enabled:
            print("[Rust Auto-Connect] Plugin is disabled, skipping")
            return
        
        print(f"[Rust Auto-Connect] Raid alert received! Launching Rust...")
        
        if not self.validate_settings():
            print("[Rust Auto-Connect] Invalid settings, skipping launch")
            return
        
        try:
            self.launch_rust()
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"🚀 Launched Rust at {self.server_ip}:{self.server_port}")
                self.status_label.setStyleSheet("color: #44ff44; padding: 10px;")
        except Exception as e:
            print(f"[Rust Auto-Connect] Error launching Rust: {e}")
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"❌ Launch failed")
                self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
    
    def on_enable(self):
        """Called when plugin is enabled"""
        self.enabled = True
        print("[Rust Auto-Connect] Plugin enabled")
    
    def on_disable(self):
        """Called when plugin is disabled"""
        self.enabled = False
        print("[Rust Auto-Connect] Plugin disabled")
    
    def cleanup(self):
        """Called when plugin is being unloaded"""
        pass
    
    def show_help(self):
        """Show setup guide"""
        help_text = """<b>Rust Auto-Connect Setup Guide</b><br><br>

<b>What This Does:</b><br>
Automatically launches Rust and connects to your server when a raid alert is received.<br><br>

<b>Step 1: Find Your Server Info</b><br>
1. Open Rust console (F1)<br>
2. Type <code>client.connect</code> to see connection format<br>
3. Or check server list/Discord for IP:Port<br><br>

<b>Step 2: Configure Plugin</b><br>
• <b>Server IP:</b> Can be IP address (192.168.1.50) or domain (play.myserver.com)<br>
• <b>Server Port:</b> Usually 28015 (default Rust port)<br><br>

<b>How It Works:</b><br>
Uses the <code>steam://connect/</code> protocol to launch Rust directly.<br>
Steam must be installed and logged in for this to work.<br><br>

<b>Step 3: Test</b><br>
1. Click "🎮 Test Connection"<br>
2. Rust should launch and auto-connect<br>
3. If it works, enable the plugin!<br><br>

<b>Tips:</b><br>
• Make sure Steam is running<br>
• Rust will minimize if already open<br>
• Works even if you're AFK - instant notification<br>
• Perfect for defending against offline raids!<br><br>

<b>Troubleshooting:</b><br>
• Nothing happens → Make sure Steam is installed and logged in<br>
• Wrong server → Double-check IP:Port<br>
• Already in server → Plugin still works, just switches servers"""
        
        msg = QMessageBox()
        msg.setWindowTitle("Rust Auto-Connect Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                min-width: 500px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        msg.exec()
    
    def get_groupbox_style(self):
        return """
            QGroupBox {
                background-color: #131418;
                border: 1px solid #2a2c33;
                border-radius: 14px;
                padding: 18px 12px 12px 12px;
                margin-top: 12px;
                color: #d4d4d4;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 6px 10px;
                color: #d4d4d4;
                font-weight: 600;
            }
        """
    
    def get_button_style(self, bg_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {bg_color}dd;
            }}
            QPushButton:pressed {{
                background-color: {bg_color}aa;
            }}
        """
