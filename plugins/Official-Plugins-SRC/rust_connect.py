"""
Rust Auto-Connect Plugin
Launches Rust and connects to a server when raid alert is received
"""

import subprocess
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                                QLineEdit, QLabel, QPushButton, QMessageBox, QFrame,
                                QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from plugin_base import PluginBase

class Plugin(PluginBase):
    """Plugin to launch Rust and auto-connect to server"""
    
    def __init__(self, telegram_service, config: dict):
        super().__init__(telegram_service, config)
        self.enabled = False
        
        # Server list - list of dicts with name, ip, port
        self.servers = self.config.get("rust_servers", [])
        self.selected_server_index = self.config.get("rust_selected_server", -1)
        
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

    def get_version(self) -> str:
        return "1.0.0"

    def get_author(self) -> str:
        return "RustPlusRaidAlarms Team"

    def get_homepage(self) -> str:
        return "https://github.com/eman225511/RustPlusRaidAlarms"
    
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
        
        # Server List Group
        server_group = QGroupBox("Server List")
        server_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        server_group.setStyleSheet(self.get_groupbox_style())
        server_layout = QVBoxLayout(server_group)
        
        # Server list widget
        self.server_list = QListWidget()
        self.server_list.setMinimumHeight(150)
        self.server_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 4px;
                color: #d4d4d4;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """)
        self.server_list.itemSelectionChanged.connect(self.on_server_selected)
        server_layout.addWidget(self.server_list)
        
        # Add/Remove buttons
        button_row = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Server")
        add_btn.setFont(QFont("Segoe UI", 10))
        add_btn.setMinimumHeight(36)
        add_btn.setStyleSheet(self.get_button_style("#28a745"))
        add_btn.clicked.connect(self.add_server)
        button_row.addWidget(add_btn)
        
        remove_btn = QPushButton("➖ Remove Server")
        remove_btn.setFont(QFont("Segoe UI", 10))
        remove_btn.setMinimumHeight(36)
        remove_btn.setStyleSheet(self.get_button_style("#dc3545"))
        remove_btn.clicked.connect(self.remove_server)
        button_row.addWidget(remove_btn)
        
        server_layout.addLayout(button_row)
        
        # Info label
        info_label = QLabel("Select one server from the list - it will be used when raid alerts are received")
        info_label.setFont(QFont("Segoe UI", 9))
        info_label.setStyleSheet("color: #888888; padding: 4px;")
        info_label.setWordWrap(True)
        server_layout.addWidget(info_label)
        
        layout.addWidget(server_group)
        
        # Load servers into list
        self.refresh_server_list()
        
        # Selected Server Display
        selected_frame = QFrame()
        selected_frame.setObjectName("card")
        selected_layout = QVBoxLayout(selected_frame)
        selected_layout.setContentsMargins(16, 12, 16, 12)
        
        selected_header = QLabel("Currently Selected Server:")
        selected_header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        selected_header.setStyleSheet("color: #b8b8b8;")
        selected_layout.addWidget(selected_header)
        
        self.selected_label = QLabel("No server selected")
        self.selected_label.setFont(QFont("Segoe UI", 12))
        self.selected_label.setStyleSheet("color: #ffa500; padding: 8px;")
        self.selected_label.setWordWrap(True)
        selected_layout.addWidget(self.selected_label)
        
        layout.addWidget(selected_frame)
        
        # Update the selected label to show current selection
        self.update_selected_display()
        
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
    
    def refresh_server_list(self):
        """Refresh the server list widget"""
        self.server_list.clear()
        
        for i, server in enumerate(self.servers):
            name = server.get("name", "Unnamed")
            ip = server.get("ip", "")
            port = server.get("port", "28015")
            
            item = QListWidgetItem(f"{name} - {ip}:{port}")
            self.server_list.addItem(item)
            
            # Select the previously selected server
            if i == self.selected_server_index:
                self.server_list.setCurrentRow(i)
    
    def add_server(self):
        """Add a new server to the list"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self._widget)
        dialog.setWindowTitle("Add Server")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        # Server name
        name_input = QLineEdit()
        name_input.setPlaceholderText("My Server")
        name_input.setMinimumHeight(32)
        form.addRow("Server Name:", name_input)
        
        # Server IP
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("192.168.1.50 or play.example.com")
        ip_input.setMinimumHeight(32)
        form.addRow("Server IP:", ip_input)
        
        # Server Port
        port_input = QLineEdit()
        port_input.setText("28015")
        port_input.setPlaceholderText("28015")
        port_input.setMinimumHeight(32)
        form.addRow("Server Port:", port_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            name = name_input.text().strip()
            ip = ip_input.text().strip()
            port = port_input.text().strip()
            
            if not name:
                QMessageBox.warning(self._widget, "Missing Name", "Please enter a server name")
                return
            
            if not ip:
                QMessageBox.warning(self._widget, "Missing IP", "Please enter a server IP address")
                return
            
            if not port:
                port = "28015"
            
            # Add to list
            self.servers.append({
                "name": name,
                "ip": ip,
                "port": port
            })
            
            self.config["rust_servers"] = self.servers
            self.refresh_server_list()
            self.update_selected_display()
    
    def remove_server(self):
        """Remove selected server from the list"""
        current_row = self.server_list.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self._widget, "No Selection", "Please select a server to remove")
            return
        
        server = self.servers[current_row]
        result = QMessageBox.question(
            self._widget,
            "Confirm Remove",
            f"Remove server '{server['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            self.servers.pop(current_row)
            
            # Update selected index
            if self.selected_server_index == current_row:
                self.selected_server_index = -1
            elif self.selected_server_index > current_row:
                self.selected_server_index -= 1
            
            self.config["rust_servers"] = self.servers
            self.config["rust_selected_server"] = self.selected_server_index
            self.refresh_server_list()
            self.update_selected_display()
    
    def update_selected_display(self):
        """Update the selected server display label"""
        if not hasattr(self, 'selected_label'):
            return
            
        if self.selected_server_index >= 0 and self.selected_server_index < len(self.servers):
            server = self.servers[self.selected_server_index]
            self.selected_label.setText(f"🎯 {server['name']} - {server['ip']}:{server['port']}")
            self.selected_label.setStyleSheet("color: #44ff44; padding: 8px; font-weight: bold;")
        else:
            self.selected_label.setText("⚠️ No server selected - please select a server from the list")
            self.selected_label.setStyleSheet("color: #ffa500; padding: 8px;")
    
    def on_server_selected(self):
        """Called when a server is selected in the list"""
        current_row = self.server_list.currentRow()
        self.selected_server_index = current_row
        self.config["rust_selected_server"] = current_row
        
        self.update_selected_display()
        
        if current_row >= 0 and current_row < len(self.servers):
            server = self.servers[current_row]
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"✓ Selected: {server['name']} ({server['ip']}:{server['port']})")
                self.status_label.setStyleSheet("color: #44ff44; padding: 10px;")
    
    def test_connection(self):
        """Test launching Rust with current settings"""
        if self.selected_server_index < 0 or self.selected_server_index >= len(self.servers):
            QMessageBox.warning(
                self._widget,
                "No Server Selected",
                "Please select a server from the list first"
            )
            return
        
        server = self.servers[self.selected_server_index]
        
        self.status_label.setText("🚀 Launching Rust...")
        self.status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        
        try:
            self.launch_rust(server)
            self.status_label.setText(f"✅ Launched: {server['name']}")
            self.status_label.setStyleSheet("color: #44ff44; padding: 10px;")
            
            QMessageBox.information(
                self._widget,
                "Success",
                f"Rust is launching and connecting to:\n{server['name']}\n{server['ip']}:{server['port']}\n\nCheck your game!"
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
        if self.selected_server_index < 0 or self.selected_server_index >= len(self.servers):
            return False
        return True
    
    def launch_rust(self, server=None):
        """Launch Rust and connect to server using steam://run protocol"""
        if server is None:
            if not self.validate_settings():
                return
            server = self.servers[self.selected_server_index]
        
        # Use steam://run/APPID//+connect%20IP:PORT
        # 252490 is Rust's Steam App ID
        # URL encode the +connect command
        rust_app_id = "252490"
        connect_command = f"+connect%20{server['ip']}:{server['port']}"
        
        # Format: steam://run/252490//+connect%20IP:PORT
        steam_url = f"steam://run/{rust_app_id}//{connect_command}"
        
        print(f"[Rust Auto-Connect] Opening Steam URL: {steam_url}")
        
        # Use os.startfile to open the steam:// URL
        os.startfile(steam_url)
        
        print(f"[Rust Auto-Connect] Launched Rust connecting to {server['name']} ({server['ip']}:{server['port']})")
    
    def on_telegram_message(self, message: str):
        """Called when Telegram message received - launch Rust"""
        print(f"[Rust Auto-Connect] on_telegram_message called. Enabled: {self.enabled}, Message: {message}")
        
        if not self.enabled:
            print("[Rust Auto-Connect] Plugin is disabled, skipping")
            return
        
        if not self.validate_settings():
            print("[Rust Auto-Connect] No server selected, skipping launch")
            return
        
        server = self.servers[self.selected_server_index]
        print(f"[Rust Auto-Connect] Raid alert received! Launching Rust to {server['name']}...")
        
        try:
            self.launch_rust(server)
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText(f"🚀 Launched: {server['name']}")
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
