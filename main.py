"""
RustPlus Raid Alarms - Plugin-based Application
Main application with Telegram listener and plugin system
"""

import sys
import json
import importlib.util
import urllib.request
import subprocess
import zipfile
import tempfile
import shutil
from pathlib import Path
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTabWidget,
                               QTextEdit, QFrame, QScrollArea, QSplitter,
                               QCheckBox, QLineEdit, QSpinBox, QDialog,
                               QFormLayout, QDialogButtonBox, QSizePolicy, QListWidget,
                               QListWidgetItem, QMessageBox, QProgressDialog)
from PySide6.QtCore import Qt, Signal, QTimer, QPoint, QMimeData, QSize, QThread
from PySide6.QtGui import QFont, QColor, QPalette, QDrag, QCursor

from telegram_service import TelegramService
from relay_server import RelayServer, RelayClient
from fcm_service import FCMService
from plugin_base import PluginBase

CONFIG_FILE = "config.json"


class DraggableButton(QPushButton):
    """Custom button that supports drag-and-drop reordering"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.drag_start_position = None
        self.is_core_tab = False  # Core tab shouldn't be draggable
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.is_core_tab:
            self.drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self.is_core_tab:
            return
        if self.drag_start_position is None:
            return
        if (event.position().toPoint() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(id(self)))  # Use object id as identifier
        drag.setMimeData(mime_data)
        drag.exec(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            # Walk up to find handler
            handler = self
            while handler is not None and not hasattr(handler, 'handle_tab_reorder'):
                handler = handler.parent()
            if handler is not None and hasattr(handler, 'handle_tab_reorder'):
                source_id = event.mimeData().text()
                target_id = str(id(self))
                handler.handle_tab_reorder(source_id, target_id)


class ModernTab(QWidget):
    """Custom styled tab widget"""
    def __init__(self, label_text):
        super().__init__()
        self.label_text = label_text
        
    def get_label(self):
        return self.label_text


class MainWindow(QMainWindow):
    """Main application window with vertical tab sidebar"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RustPlus Raid Alarms")
        self.setGeometry(100, 100, 1400, 800)
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize Telegram service
        self.telegram_service = TelegramService(self.config)
        self.telegram_service.message_received.connect(self.on_telegram_message)
        self.telegram_service.status_changed.connect(self.on_telegram_status)
        
        # Initialize FCM service
        self.fcm_service = FCMService(self.config)
        self.fcm_service.message_received.connect(self.on_fcm_notification)
        self.fcm_service.status_changed.connect(self.on_fcm_status)
        self.fcm_service.auth_completed.connect(self.on_fcm_auth_completed)
        self.fcm_service.server_paired.connect(self.on_fcm_server_paired)
        
        # Relay server/client
        self.relay_server = RelayServer(port=5555)
        self.relay_server.status_changed.connect(self.on_relay_server_status)
        self.relay_server.tunnel_url_ready.connect(self.on_tunnel_url_ready)
        self.relay_client = None  # Created when connecting to a server
        
        # Plugin system
        self.plugins = []
        self.plugin_widgets = {}
        self.loaded_plugin_keys = set()  # track loaded plugin files
        self.tab_button_map = {}  # Map button IDs to (button, tab_index, plugin)
        self.plugin_enabled = {}  # Track enabled/disabled state per plugin
        self.show_example_plugins = self.config.get("show_example_plugins", False)
        self.store_plugins_data = []  # cache of store metadata for search filtering
        
        # Setup UI
        self.setup_ui()
        self.apply_dark_theme()
        
        # Load plugins
        self.load_plugins()

        # Watch for new plugins periodically (no restart needed)
        self.plugin_watch_timer = QTimer(self)
        self.plugin_watch_timer.setInterval(5000)
        self.plugin_watch_timer.timeout.connect(self.load_plugins)
        self.plugin_watch_timer.start()
        
        # Check if in relay mode and restore connection
        if self.config.get("relay_mode", False) and self.config.get("relay_client_server"):
            QTimer.singleShot(1000, self.restore_relay_connection)
        elif self.config.get("fcm_mode", False):
            # Auto-start FCM listener if in FCM mode and keyword set
            if self.fcm_service.is_authenticated() and bool((self.config.get("fcm_filter_keyword", "") or "").strip()):
                QTimer.singleShot(500, self.fcm_service.start)
                self.log("Auto-starting FCM mode...")
            else:
                self.log("FCM mode enabled but keyword/auth not ready; not auto-starting")
        else:
            # Auto-start Telegram listener if not in relay or FCM mode
            QTimer.singleShot(500, self.telegram_service.start)
        
        # Update connection mode UI after tabs are created
        QTimer.singleShot(1500, self.update_connection_mode_status)
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            # Create default config
            data = {}

        # Ensure defaults
        default_config = {
            "telegram_bot_token": "",
            "telegram_chat_id": "",
            "last_message_id": 0,
            "polling_rate": 2,
            "filter_enabled": False,
            "filter_keyword": "",
            "led_type": "wled",
            "wled_ip": "",
            "govee_api_key": "",
            "govee_device_id": "",
            "govee_model": "",
            "hue_bridge_ip": "",
            "hue_username": "",
            "action": "on",
            "color": "#ffffff",
            "effect": "0",
            "preset": "0",
            "scene": "0",
            "brightness": "100",
            "show_example_plugins": False,
        }

        # Merge defaults without overwriting existing values
        for k, v in default_config.items():
            data.setdefault(k, v)

        self.save_config(data)
        return data
    
    def save_config(self, config=None):
        """Save configuration to JSON file"""
        if config is None:
            config = self.config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    
    def setup_ui(self):
        """Setup the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with splitter
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Content area (left side)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack widget to hold different views
        self.content_stack = QTabWidget()
        self.content_stack.setTabPosition(QTabWidget.West)
        self.content_stack.setDocumentMode(True)
        # Completely hide the tab bar to avoid double tabs
        self.content_stack.tabBar().setVisible(False)
        content_layout.addWidget(self.content_stack)
        
        # Telegram Tab (always first)
        telegram_tab = self.create_telegram_tab()
        self.content_stack.addTab(telegram_tab, "")
        
        # Logs Tab (always second)
        logs_tab = self.create_logs_tab()
        self.content_stack.addTab(logs_tab, "")
        
        # Clan Tab (always third)
        clan_tab = self.create_clan_tab()
        self.content_stack.addTab(clan_tab, "")
        
        # Plugin Store Tab (always fourth)
        plugin_store_tab = self.create_plugin_store_tab()
        self.content_stack.addTab(plugin_store_tab, "")
        
        # Beta Features Tab (always fifth)
        beta_tab = self.create_beta_tab()
        self.content_stack.addTab(beta_tab, "")
        
        # Vertical tab bar (right side)
        self.tab_bar = self.create_vertical_tab_bar()
        
        # Add to splitter (navigation on the left)
        splitter.addWidget(self.tab_bar)
        splitter.addWidget(content_widget)
        splitter.setStretchFactor(1, 1)  # Content takes most space
        splitter.setSizes([220, 1200])
        
        main_layout.addWidget(splitter)
    
    def create_telegram_tab(self):
        """Create the Telegram core tab with a cleaner layout"""
        # Create scroll area
        from PySide6.QtWidgets import QScrollArea
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505053;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Hero header
        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(8)

        self.core_title = QLabel("Telegram Listener")
        self.core_title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.core_title.setStyleSheet("color: #ffffff;")
        hero_layout.addWidget(self.core_title)

        self.core_subtitle = QLabel("Live raid alerts piped into plugins and actions")
        self.core_subtitle.setFont(QFont("Segoe UI", 11))
        self.core_subtitle.setStyleSheet("color: #b8b8b8;")
        hero_layout.addWidget(self.core_subtitle)

        pill_row = QHBoxLayout()
        pill_row.setSpacing(10)

        self.pill_status = QLabel("● Connecting")
        self.pill_status.setObjectName("pillMuted")
        pill_row.addWidget(self.pill_status)

        self.pill_poll = QLabel(f"Polling {self.config.get('polling_rate', 2)}s")
        self.pill_poll.setObjectName("pill")
        pill_row.addWidget(self.pill_poll)

        pill_row.addStretch()

        hero_layout.addLayout(pill_row)

        layout.addWidget(hero)

        # Relay mode warning (hidden by default)
        self.core_relay_warning = QFrame()
        self.core_relay_warning.setObjectName("card")
        self.core_relay_warning.setStyleSheet("QFrame#card { background-color: #2d2520; border: 1px solid #ffa500; }")
        relay_warning_layout = QVBoxLayout(self.core_relay_warning)
        relay_warning_layout.setContentsMargins(12, 12, 12, 12)
        
        relay_warning_label = QLabel("⚠️ <b>Relay Mode Active</b><br>You're connected to a relay server. Your local Telegram service is disabled.<br>These settings won't take effect until you disconnect from relay.")
        relay_warning_label.setStyleSheet("color: #ffa500; font-size: 10pt;")
        relay_warning_label.setWordWrap(True)
        relay_warning_layout.addWidget(relay_warning_label)
        
        self.core_relay_warning.hide()
        layout.addWidget(self.core_relay_warning)

        # Status + controls card
        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.setSpacing(12)

        status_header = QHBoxLayout()
        status_label = QLabel("Status")
        status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        status_label.setStyleSheet("color: #e6e6e6;")
        status_header.addWidget(status_label)
        status_header.addStretch()
        status_layout.addLayout(status_header)

        self.status_display = QLabel("Initializing...")
        self.status_display.setFont(QFont("Segoe UI", 14))
        self.status_display.setStyleSheet("color: #ffa500; padding: 6px 0;")
        self.status_display.setWordWrap(True)
        status_layout.addWidget(self.status_display)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFont(QFont("Segoe UI", 11))
        self.start_btn.setMinimumHeight(42)
        self.start_btn.setStyleSheet(self.get_button_style("#0e639c"))
        self.start_btn.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏸ Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 11))
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setStyleSheet(self.get_button_style("#c50f1f"))
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        button_layout.addWidget(self.stop_btn)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setFont(QFont("Segoe UI", 11))
        settings_btn.setMinimumHeight(42)
        settings_btn.setStyleSheet(self.get_button_style("#6c757d"))
        settings_btn.clicked.connect(self.open_settings)
        button_layout.addWidget(settings_btn)

        button_layout.addStretch()
        status_layout.addLayout(button_layout)

        # Polling rate control
        polling_row = QHBoxLayout()
        polling_row.setSpacing(10)
        polling_label = QLabel("Polling rate (seconds)")
        polling_label.setStyleSheet("color: #c7c7c7;")
        polling_row.addWidget(polling_label)

        self.poll_spin = QSpinBox()
        self.poll_spin.setRange(1, 60)
        self.poll_spin.setValue(int(self.config.get("polling_rate", 2)))
        self.poll_spin.setMinimumWidth(90)
        self.poll_spin.valueChanged.connect(self.on_polling_rate_change)
        polling_row.addWidget(self.poll_spin)
        polling_row.addStretch()
        status_layout.addLayout(polling_row)

        layout.addWidget(status_frame)

        # Filter card
        filter_frame = QFrame()
        filter_frame.setObjectName("card")
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(16, 16, 16, 16)
        filter_layout.setSpacing(10)

        filter_header = QHBoxLayout()
        filter_label = QLabel("Message Filter (optional)")
        filter_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        filter_label.setStyleSheet("color: #e6e6e6;")
        filter_header.addWidget(filter_label)
        filter_header.addStretch()
        filter_layout.addLayout(filter_header)

        filter_row = QHBoxLayout()
        self.filter_checkbox = QCheckBox("Enable keyword filter")
        self.filter_checkbox.setChecked(bool(self.config.get("filter_enabled", False)))
        self.filter_checkbox.stateChanged.connect(self.on_filter_toggle)
        filter_row.addWidget(self.filter_checkbox)

        self.filter_input = QLineEdit(self.config.get("filter_keyword", ""))
        self.filter_input.setPlaceholderText("keyword to match (case-insensitive)")
        self.filter_input.editingFinished.connect(self.on_filter_keyword_change)
        filter_row.addWidget(self.filter_input)

        filter_layout.addLayout(filter_row)

        hint = QLabel("Off by default. When enabled, only messages containing the keyword will trigger plugins.")
        hint.setStyleSheet("color: #9aa0a6;")
        hint.setWordWrap(True)
        filter_layout.addWidget(hint)

        layout.addWidget(filter_frame)

        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll
    
    def create_logs_tab(self):
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)

        title_row = QHBoxLayout()
        
        title = QLabel("📋 Activity Logs")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        title_row.addWidget(title)
        
        title_row.addStretch()
        
        # Clear log button
        clear_log_btn = QPushButton("🧹 Clear Log")
        clear_log_btn.setFont(QFont("Segoe UI", 11))
        clear_log_btn.setMinimumHeight(36)
        clear_log_btn.setStyleSheet(self.get_button_style("#6c757d"))
        clear_log_btn.clicked.connect(self.clear_log)
        title_row.addWidget(clear_log_btn)
        
        header_layout.addLayout(title_row)

        subtitle = QLabel("Real-time activity and event monitoring")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Activity log card
        log_frame = QFrame()
        log_frame.setObjectName("card")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(10)

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 10))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #111214;
                color: #d4d4d4;
                border: 1px solid #303136;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.log_display, 1)

        layout.addWidget(log_frame, 1)

        return widget
    
    def create_clan_tab(self):
        """Create clan tab for sharing and collaboration features"""
        # Create scroll area
        from PySide6.QtWidgets import QScrollArea
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505053;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QFrame()
        header.setObjectName("heroCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("👥 Clan Sharing")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)

        subtitle = QLabel("Share alerts with your team using encrypted codes or relay server")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header)

        # Telegram Clan Codes Section
        telegram_frame = QFrame()
        telegram_frame.setObjectName("card")
        telegram_layout = QVBoxLayout(telegram_frame)
        telegram_layout.setContentsMargins(16, 16, 16, 16)
        telegram_layout.setSpacing(12)

        telegram_header = QLabel("📱 Telegram Clan Codes")
        telegram_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        telegram_header.setStyleSheet("color: #e6e6e6;")
        telegram_layout.addWidget(telegram_header)

        telegram_desc = QLabel("Share encrypted Telegram bot credentials with your clan. Everyone gets the same bot setup.")
        telegram_desc.setStyleSheet("color: #9aa0a6;")
        telegram_desc.setWordWrap(True)
        telegram_layout.addWidget(telegram_desc)

        telegram_buttons = QHBoxLayout()
        
        export_telegram_btn = QPushButton("📤 Export Clan Code")
        export_telegram_btn.setFont(QFont("Segoe UI", 11))
        export_telegram_btn.setMinimumHeight(42)
        export_telegram_btn.setStyleSheet(self.get_button_style("#28a745"))
        export_telegram_btn.clicked.connect(self.export_clan_code)
        telegram_buttons.addWidget(export_telegram_btn)
        
        import_telegram_btn = QPushButton("📥 Import Clan Code")
        import_telegram_btn.setFont(QFont("Segoe UI", 11))
        import_telegram_btn.setMinimumHeight(42)
        import_telegram_btn.setStyleSheet(self.get_button_style("#17a2b8"))
        import_telegram_btn.clicked.connect(self.import_clan_code)
        telegram_buttons.addWidget(import_telegram_btn)
        
        telegram_layout.addLayout(telegram_buttons)

        telegram_warning = QLabel("⚠️ Note: Multiple people using the same bot may experience polling conflicts. Use Relay Server for better experience.")
        telegram_warning.setStyleSheet("color: #ffa500; font-size: 9pt;")
        telegram_warning.setWordWrap(True)
        telegram_layout.addWidget(telegram_warning)

        layout.addWidget(telegram_frame)

        # Relay Server Section
        relay_frame = QFrame()
        relay_frame.setObjectName("card")
        relay_layout = QVBoxLayout(relay_frame)
        relay_layout.setContentsMargins(16, 16, 16, 16)
        relay_layout.setSpacing(12)

        relay_header = QLabel("🌐 Relay Server (Recommended)")
        relay_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        relay_header.setStyleSheet("color: #e6e6e6;")
        relay_layout.addWidget(relay_header)

        relay_desc = QLabel("Host a relay server so your clan can connect to YOU. Only one person needs Telegram setup, auto-tunnels with ngrok (no port forwarding).")
        relay_desc.setStyleSheet("color: #9aa0a6;")
        relay_desc.setWordWrap(True)
        relay_layout.addWidget(relay_desc)

        # Server Mode Toggle
        self.clan_server_checkbox = QCheckBox("Enable Relay Server Mode")
        self.clan_server_checkbox.setChecked(bool(self.config.get("server_mode_enabled", False)))
        self.clan_server_checkbox.stateChanged.connect(self.on_server_mode_toggle)
        self.clan_server_checkbox.setStyleSheet("font-size: 11pt; padding: 8px;")
        relay_layout.addWidget(self.clan_server_checkbox)

        self.clan_server_status_label = QLabel("Server offline")
        self.clan_server_status_label.setStyleSheet("color: #888888; padding: 6px; background-color: #1a1a1a; border-radius: 6px;")
        self.clan_server_status_label.setWordWrap(True)
        relay_layout.addWidget(self.clan_server_status_label)

        relay_buttons = QHBoxLayout()
        
        export_server_btn = QPushButton("🌐 Export Server Code")
        export_server_btn.setFont(QFont("Segoe UI", 11))
        export_server_btn.setMinimumHeight(42)
        export_server_btn.setStyleSheet(self.get_button_style("#6c42f5"))
        export_server_btn.clicked.connect(self.export_server_code)
        relay_buttons.addWidget(export_server_btn)
        
        import_server_btn = QPushButton("🌐 Import Server Code")
        import_server_btn.setFont(QFont("Segue UI", 11))
        import_server_btn.setMinimumHeight(42)
        import_server_btn.setStyleSheet(self.get_button_style("#17a2b8"))
        import_server_btn.clicked.connect(self.import_server_code)
        relay_buttons.addWidget(import_server_btn)
        
        relay_layout.addLayout(relay_buttons)

        # Ngrok Setup Section
        ngrok_setup_frame = QFrame()
        ngrok_setup_frame.setObjectName("card")
        ngrok_setup_frame.setStyleSheet("QFrame#card { background-color: #1a1a1a; }")
        ngrok_setup_layout = QVBoxLayout(ngrok_setup_frame)
        ngrok_setup_layout.setContentsMargins(12, 12, 12, 12)
        ngrok_setup_layout.setSpacing(8)

        ngrok_title = QLabel("🔧 Ngrok Authentication (Optional)")
        ngrok_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ngrok_title.setStyleSheet("color: #e6e6e6;")
        ngrok_setup_layout.addWidget(ngrok_title)

        ngrok_info = QLabel("For internet access (not just local WiFi), set up your ngrok authtoken:")
        ngrok_info.setStyleSheet("color: #9aa0a6; font-size: 9pt;")
        ngrok_info.setWordWrap(True)
        ngrok_setup_layout.addWidget(ngrok_info)

        authtoken_layout = QHBoxLayout()
        
        self.ngrok_authtoken_input = QLineEdit()
        self.ngrok_authtoken_input.setPlaceholderText("Paste your ngrok authtoken here...")
        self.ngrok_authtoken_input.setEchoMode(QLineEdit.Password)
        self.ngrok_authtoken_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                padding: 8px;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        authtoken_layout.addWidget(self.ngrok_authtoken_input, 1)

        save_authtoken_btn = QPushButton("💾 Save")
        save_authtoken_btn.setMinimumHeight(36)
        save_authtoken_btn.setStyleSheet(self.get_button_style("#28a745"))
        save_authtoken_btn.clicked.connect(self.save_ngrok_authtoken)
        authtoken_layout.addWidget(save_authtoken_btn)

        ngrok_setup_layout.addLayout(authtoken_layout)

        ngrok_hint = QLabel("💡 Get your authtoken: <a href='https://dashboard.ngrok.com/get-started/your-authtoken' style='color: #17a2b8;'>dashboard.ngrok.com/get-started/your-authtoken</a>")
        ngrok_hint.setStyleSheet("color: #9aa0a6; font-size: 9pt;")
        ngrok_hint.setOpenExternalLinks(True)
        ngrok_hint.setWordWrap(True)
        ngrok_setup_layout.addWidget(ngrok_hint)

        relay_layout.addWidget(ngrok_setup_frame)

        layout.addWidget(relay_frame)

        # Connection Mode Status
        mode_frame = QFrame()
        mode_frame.setObjectName("card")
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(10)

        mode_header = QLabel("📡 Current Connection Mode")
        mode_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        mode_header.setStyleSheet("color: #e6e6e6;")
        mode_layout.addWidget(mode_header)

        self.clan_mode_status = QLabel("🔹 Direct Telegram Mode")
        self.clan_mode_status.setStyleSheet("color: #17a2b8; padding: 8px; background-color: #1a1a1a; border-radius: 6px; font-size: 11pt;")
        self.clan_mode_status.setWordWrap(True)
        mode_layout.addWidget(self.clan_mode_status)

        # Disconnect button (hidden by default)
        self.disconnect_relay_btn = QPushButton("🔌 Disconnect from Relay & Use Direct Telegram")
        self.disconnect_relay_btn.setMinimumHeight(40)
        self.disconnect_relay_btn.setStyleSheet(self.get_button_style("#dc3545"))
        self.disconnect_relay_btn.clicked.connect(self.disconnect_from_relay)
        self.disconnect_relay_btn.hide()
        mode_layout.addWidget(self.disconnect_relay_btn)

        mode_hint = QLabel("💡 You can only use one mode at a time. Connect to a relay server to switch from direct Telegram, or disconnect to go back.")
        mode_hint.setStyleSheet("color: #9aa0a6; font-size: 9pt;")
        mode_hint.setWordWrap(True)
        mode_layout.addWidget(mode_hint)

        layout.addWidget(mode_frame)

        # Info Section
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(8)

        info_header = QLabel("💡 How It Works")
        info_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        info_header.setStyleSheet("color: #e6e6e6;")
        info_layout.addWidget(info_header)

        info_text = QLabel(
            "<b>Telegram Clan Codes:</b><br>"
            "• One person sets up Telegram bot<br>"
            "• Export encrypted code with password<br>"
            "• Clan members import code to get same bot<br>"
            "• ⚠️ May conflict if multiple people online<br><br>"
            
            "<b>Relay Server (Better!):</b><br>"
            "• Host enables Server Mode (gets Telegram messages)<br>"
            "• Export server code (includes public ngrok URL)<br>"
            "• Clan members import server code and connect<br>"
            "• ✅ No conflicts, no Telegram setup needed for members<br>"
            "• 🔒 Optional password protection"
        )
        info_text.setStyleSheet("color: #d4d4d4; line-height: 1.4;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_frame)

        layout.addStretch()
        
        scroll.setWidget(widget)
        return scroll

    def apply_store_filter(self):
        """Filter and render plugin store list based on search text."""
        if not hasattr(self, 'store_plugins_data'):
            return

        search_text = self.store_search.text().strip().lower() if hasattr(self, 'store_search') else ""

        def matches_search(info):
            if not search_text:
                return True
            haystack = " ".join([
                info.get('name', ''),
                info.get('author', ''),
                info.get('description', ''),
                " ".join(info.get('tags', []))
            ]).lower()
            return search_text in haystack

        self.plugin_store_list.clear()
        installed = self.get_installed_plugins()

        for plugin_info in self.store_plugins_data:
            if not matches_search(plugin_info):
                continue

            # Create list item
            item = QListWidgetItem()

            # Create widget for the item
            item_widget = QWidget()
            item_widget.setStyleSheet("background: transparent;")
            item_widget.setMinimumHeight(130)
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(12, 12, 12, 12)
            item_layout.setSpacing(16)

            # Icon
            icon_label = QLabel(plugin_info.get("icon", "📦"))
            icon_label.setFont(QFont("Segoe UI", 28))
            icon_label.setFixedSize(50, 50)
            icon_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(icon_label)

            # Info section
            info_layout = QVBoxLayout()
            info_layout.setSpacing(6)

            # Name and version
            name_label = QLabel(f"<b>{plugin_info['name']}</b> <span style='color: #888;'>v{plugin_info['version']}</span>")
            name_label.setFont(QFont("Segoe UI", 14))
            name_label.setStyleSheet("color: #e6e6e6;")
            info_layout.addWidget(name_label)

            # Author
            author_label = QLabel(f"by {plugin_info.get('author', 'Unknown')}")
            author_label.setFont(QFont("Segoe UI", 10))
            author_label.setStyleSheet("color: #888888;")
            info_layout.addWidget(author_label)

            # Description
            desc_label = QLabel(plugin_info.get('description', 'No description'))
            desc_label.setFont(QFont("Segoe UI", 10))
            desc_label.setStyleSheet("color: #b8b8b8;")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(55)
            info_layout.addWidget(desc_label)

            # Tags
            tags = plugin_info.get('tags', [])
            if tags:
                tags_text = " ".join([f"<span style='background-color: #3e3e42; padding: 2px 6px; border-radius: 3px; font-size: 9px;'>{tag}</span>" for tag in tags[:4]])
                tags_label = QLabel(tags_text)
                tags_label.setStyleSheet("color: #888888;")
                tags_label.setMaximumHeight(20)
                info_layout.addWidget(tags_label)

            info_layout.addStretch()
            item_layout.addLayout(info_layout, 1)

            # Install/Update button
            plugin_id = plugin_info['id']
            installed_version = installed.get(plugin_id)

            btn = QPushButton()
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            btn.setFixedSize(110, 40)

            if installed_version:
                if installed_version != plugin_info['version']:
                    btn.setText("⬆️ Update")
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #16825d;
                            color: white;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 16px;
                        }
                        QPushButton:hover {
                            background-color: #1a9c70;
                        }
                    """)
                else:
                    btn.setText("✓ Installed")
                    btn.setEnabled(False)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #2d2d30;
                            color: #888888;
                            border: 1px solid #3e3e42;
                            border-radius: 6px;
                            padding: 8px 16px;
                        }
                    """)
            else:
                btn.setText("⬇️ Install")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0e639c;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                    }
                    QPushButton:hover {
                        background-color: #1177bb;
                    }
                """)

            btn.clicked.connect(lambda checked, p=plugin_info: self.install_plugin(p))
            item_layout.addWidget(btn)

            # Set item size and widget
            item.setSizeHint(QSize(0, 130))
            self.plugin_store_list.addItem(item)
            self.plugin_store_list.setItemWidget(item, item_widget)

        if self.plugin_store_list.count() == 0:
            self.store_status_label.setText("No plugins match your search")
            self.store_status_label.setStyleSheet("color: #888888; padding: 10px;")
        else:
            self.store_status_label.setText(f"✓ Showing {self.plugin_store_list.count()} plugin(s)")
            self.store_status_label.setStyleSheet("color: #00ff00; padding: 10px;")
    
    def create_beta_tab(self):
        """Create the Beta Features tab for FCM direct notifications"""
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505053;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Hero header
        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        hero_layout.setSpacing(8)
        
        title = QLabel("🧪 FCM Direct Notifications (Beta)")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        hero_layout.addWidget(title)
        
        subtitle = QLabel("Connect directly to Rust+ servers via Firebase Cloud Messaging")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        hero_layout.addWidget(subtitle)
        
        layout.addWidget(hero)
        
        # Warning banner
        warning_frame = QFrame()
        warning_frame.setObjectName("card")
        warning_frame.setStyleSheet("QFrame#card { background-color: #3d2a00; border-left: 4px solid #ffa500; }")
        warning_layout = QVBoxLayout(warning_frame)
        warning_layout.setContentsMargins(12, 12, 12, 12)
        
        warning_label = QLabel("⚠️ <b>Beta Feature</b> - This mode bypasses Telegram and connects directly to Rust+ servers. "
                               "You can only use ONE mode at a time (Telegram, Relay, or FCM).")
        warning_label.setStyleSheet("color: #ffa500; font-size: 10pt;")
        warning_label.setWordWrap(True)
        warning_layout.addWidget(warning_label)
        
        layout.addWidget(warning_frame)
        
        # Status section
        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(16, 16, 16, 16)
        status_layout.setSpacing(10)
        
        status_header = QLabel("📊 FCM Status")
        status_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        status_header.setStyleSheet("color: #e6e6e6;")
        status_layout.addWidget(status_header)
        
        # Authentication status
        auth_row = QHBoxLayout()
        auth_label = QLabel("Authentication:")
        auth_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        auth_row.addWidget(auth_label)
        
        self.fcm_auth_status = QLabel("Not authenticated")
        self.fcm_auth_status.setStyleSheet("color: #888888; font-size: 10pt;")
        auth_row.addWidget(self.fcm_auth_status)
        auth_row.addStretch()
        status_layout.addLayout(auth_row)
        
        # Listener status
        listener_row = QHBoxLayout()
        listener_label = QLabel("Listener Status:")
        listener_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        listener_row.addWidget(listener_label)
        
        self.fcm_listener_status = QLabel("● Offline")
        self.fcm_listener_status.setStyleSheet("color: #888888; padding: 4px 8px; background-color: #1a1a1a; border-radius: 4px; font-size: 10pt;")
        listener_row.addWidget(self.fcm_listener_status)
        listener_row.addStretch()
        status_layout.addLayout(listener_row)

        # Start/Stop timestamp
        time_row = QHBoxLayout()
        time_label = QLabel("Session:")
        time_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        time_row.addWidget(time_label)

        self.fcm_session_time = QLabel("Not started")
        self.fcm_session_time.setStyleSheet("color: #9aa0a6; font-size: 9pt;")
        time_row.addWidget(self.fcm_session_time)
        time_row.addStretch()
        status_layout.addLayout(time_row)
        
        # Notifications count
        notif_row = QHBoxLayout()
        notif_label = QLabel("Notifications Received:")
        notif_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        notif_row.addWidget(notif_label)
        
        self.fcm_notif_count = QLabel("0")
        self.fcm_notif_count.setStyleSheet("color: #00ff00; font-size: 10pt; font-weight: bold;")
        notif_row.addWidget(self.fcm_notif_count)
        notif_row.addStretch()
        status_layout.addLayout(notif_row)
        
        # Paired server info
        paired_row = QHBoxLayout()
        paired_label = QLabel("Paired Server:")
        paired_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        paired_row.addWidget(paired_label)
        
        self.fcm_paired_server = QLabel("Not paired")
        self.fcm_paired_server.setStyleSheet("color: #888888; font-size: 10pt;")
        paired_row.addWidget(self.fcm_paired_server)
        paired_row.addStretch()
        status_layout.addLayout(paired_row)
        
        # Disconnect server button
        self.fcm_disconnect_server_btn = QPushButton("🔌 Disconnect Server")
        self.fcm_disconnect_server_btn.setFont(QFont("Segoe UI", 10))
        self.fcm_disconnect_server_btn.setMinimumHeight(36)
        self.fcm_disconnect_server_btn.setStyleSheet(self.get_button_style("#dc3545"))
        self.fcm_disconnect_server_btn.clicked.connect(self.on_fcm_disconnect_server)
        self.fcm_disconnect_server_btn.hide()
        status_layout.addWidget(self.fcm_disconnect_server_btn)
        
        # Last notification
        self.fcm_last_notif = QLabel("No notifications yet")
        self.fcm_last_notif.setStyleSheet("color: #888888; font-size: 9pt; font-style: italic; padding: 8px; background-color: #1a1a1a; border-radius: 4px;")
        self.fcm_last_notif.setWordWrap(True)
        status_layout.addWidget(self.fcm_last_notif)
        
        layout.addWidget(status_frame)
        
        # Controls section
        controls_frame = QFrame()
        controls_frame.setObjectName("card")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(16, 16, 16, 16)
        controls_layout.setSpacing(12)
        
        controls_header = QLabel("🎮 Controls")
        controls_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        controls_header.setStyleSheet("color: #e6e6e6;")
        controls_layout.addWidget(controls_header)
        
        # Mandatory keyword input
        keyword_row = QHBoxLayout()
        keyword_label = QLabel("Required Keyword:")
        keyword_label.setStyleSheet("color: #d4d4d4; font-size: 10pt;")
        keyword_row.addWidget(keyword_label)

        self.fcm_keyword_input = QLineEdit()
        self.fcm_keyword_input.setPlaceholderText("e.g. raid, alarm, base...")
        self.fcm_keyword_input.setMinimumHeight(36)
        self.fcm_keyword_input.setClearButtonEnabled(True)
        self.fcm_keyword_input.setText(self.config.get("fcm_filter_keyword", ""))
        self.fcm_keyword_input.textChanged.connect(self.on_fcm_keyword_change)
        self.fcm_keyword_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 6px 10px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border-color: #dc3545;
            }
        """)
        keyword_row.addWidget(self.fcm_keyword_input, 1)

        required_hint = QLabel("✳️ Required: FCM mode only forwards alerts containing this keyword")
        required_hint.setStyleSheet("color: #dc3545; font-size: 9pt;")
        keyword_row.addWidget(required_hint)

        controls_layout.addLayout(keyword_row)

        # Authentication button
        self.fcm_auth_btn = QPushButton("🔐 Authenticate with Steam")
        self.fcm_auth_btn.setFont(QFont("Segoe UI", 11))
        self.fcm_auth_btn.setMinimumHeight(42)
        self.fcm_auth_btn.setStyleSheet(self.get_button_style("#0e639c"))
        self.fcm_auth_btn.clicked.connect(self.on_fcm_authenticate)
        controls_layout.addWidget(self.fcm_auth_btn)
        
        # Start/Stop buttons
        button_row = QHBoxLayout()
        
        self.fcm_start_btn = QPushButton("▶️ Start FCM Mode")
        self.fcm_start_btn.setFont(QFont("Segoe UI", 11))
        self.fcm_start_btn.setMinimumHeight(42)
        self.fcm_start_btn.setStyleSheet(self.get_button_style("#28a745"))
        self.fcm_start_btn.clicked.connect(self.on_fcm_start)
        self.fcm_start_btn.setEnabled(False)
        button_row.addWidget(self.fcm_start_btn)
        
        self.fcm_stop_btn = QPushButton("⏹️ Stop FCM Mode")
        self.fcm_stop_btn.setFont(QFont("Segoe UI", 11))
        self.fcm_stop_btn.setMinimumHeight(42)
        self.fcm_stop_btn.setStyleSheet(self.get_button_style("#dc3545"))
        self.fcm_stop_btn.clicked.connect(self.on_fcm_stop)
        self.fcm_stop_btn.setEnabled(False)
        button_row.addWidget(self.fcm_stop_btn)
        
        controls_layout.addLayout(button_row)
        
        # Switch back to Telegram button
        self.fcm_switch_telegram_btn = QPushButton("🔄 Switch to Telegram Mode")
        self.fcm_switch_telegram_btn.setFont(QFont("Segoe UI", 11))
        self.fcm_switch_telegram_btn.setMinimumHeight(42)
        self.fcm_switch_telegram_btn.setStyleSheet(self.get_button_style("#6c42f5"))
        self.fcm_switch_telegram_btn.clicked.connect(self.on_fcm_switch_to_telegram)
        self.fcm_switch_telegram_btn.hide()
        controls_layout.addWidget(self.fcm_switch_telegram_btn)
        
        layout.addWidget(controls_frame)
        
        # How it works section
        info_frame = QFrame()
        info_frame.setObjectName("card")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(8)
        
        info_header = QLabel("💡 How It Works")
        info_header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        info_header.setStyleSheet("color: #e6e6e6;")
        info_layout.addWidget(info_header)
        
        info_text = QLabel(
            "<b>FCM Direct Mode:</b><br>"
            "• Receives notifications directly from Rust+ companion app<br>"
            "• No Telegram bot required<br>"
            "• Uses Firebase Cloud Messaging (same as the official app)<br>"
            "• Requires Node.js for initial setup<br>"
            "<br>"
            "<b>Setup Steps:</b><br>"
            "1. Click 'Authenticate with Steam' and login<br>"
            "2. Node.js will setup FCM credentials automatically<br>"
            "3. Click 'Start FCM Mode' to begin listening<br>"
            "4. Pair with your Rust+ server in-game<br>"
            "<br>"
            "<b>Requirements:</b><br>"
            "• Node.js and npm installed on your system<br>"
            "• Internet connection for authentication<br>"
            "• Keyword filter works the same as Telegram mode"
        )
        info_text.setStyleSheet("color: #b8b8b8; font-size: 10pt; line-height: 1.4;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_frame)
        
        layout.addStretch()
        
        # Check initial auth status
        QTimer.singleShot(500, self.update_fcm_ui_status)
        
        scroll.setWidget(widget)
        return scroll
    
    def create_plugin_store_tab(self):
        """Create the plugin store tab with Store and Installed sub-tabs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create tab widget for Store/Installed
        plugin_tabs = QTabWidget()
        plugin_tabs.setTabPosition(QTabWidget.North)
        plugin_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #d4d4d4;
                padding: 10px 20px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 11px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #ffffff;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
        """)
        
        # Store tab
        store_tab = self.create_store_subtab()
        plugin_tabs.addTab(store_tab, "🛒 Store")
        
        # Installed tab
        installed_tab = self.create_installed_subtab()
        plugin_tabs.addTab(installed_tab, "📦 Installed")
        
        layout.addWidget(plugin_tabs)
        
        # Auto-load store on first show
        QTimer.singleShot(500, self.load_plugin_store)
        
        return widget
    
    def create_store_subtab(self):
        """Create the Store sub-tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4e4e52;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header with refresh + search
        header_frame = QFrame()
        header_frame.setObjectName("heroCard")
        header_frame.setMaximumHeight(190)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(10)
        
        title = QLabel("Browse Available Plugins")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Install plugins from the community repository")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)
        
        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        actions_row.setAlignment(Qt.AlignLeft)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        refresh_btn.clicked.connect(self.load_plugin_store)
        actions_row.addWidget(refresh_btn)

        self.store_search = QLineEdit()
        self.store_search.setPlaceholderText("Search plugins by name, author, tag, or description")
        self.store_search.setMinimumHeight(36)
        self.store_search.setClearButtonEnabled(True)
        self.store_search.textChanged.connect(self.apply_store_filter)
        self.store_search.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 6px 10px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border-color: #0e639c;
            }
        """)
        actions_row.addWidget(self.store_search, 1)

        actions_row.addStretch()
        header_layout.addLayout(actions_row)
        
        layout.addWidget(header_frame)
        
        # Plugin list
        self.plugin_store_list = QListWidget()
        self.plugin_store_list.setFont(QFont("Segoe UI", 10))
        self.plugin_store_list.setSpacing(8)
        self.plugin_store_list.setMinimumHeight(400)
        self.plugin_store_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plugin_store_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 0px;
                margin: 4px;
            }
            QListWidget::item:hover {
                background-color: #2d2d30;
                border-color: #007acc;
            }
            QListWidget::item:selected {
                background-color: #094771;
                border-color: #007acc;
            }
        """)
        layout.addWidget(self.plugin_store_list, 1)
        
        # Status label
        self.store_status_label = QLabel("Click 'Refresh Plugin List' to load available plugins")
        self.store_status_label.setFont(QFont("Segoe UI", 10))
        self.store_status_label.setStyleSheet("color: #888888; padding: 10px;")
        self.store_status_label.setAlignment(Qt.AlignCenter)
        self.store_status_label.setMaximumHeight(40)
        layout.addWidget(self.store_status_label, 0)
        
        scroll.setWidget(widget)
        return scroll
    
    def create_installed_subtab(self):
        """Create the Installed sub-tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4e4e52;
            }
        """)
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("heroCard")
        header_frame.setMaximumHeight(150)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        title = QLabel("Installed Plugins")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Manage your installed plugins")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setMinimumHeight(36)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        refresh_btn.clicked.connect(self.load_installed_plugins)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_frame)
        
        # Plugin list
        self.installed_plugins_list = QListWidget()
        self.installed_plugins_list.setFont(QFont("Segoe UI", 10))
        self.installed_plugins_list.setSpacing(8)
        self.installed_plugins_list.setMinimumHeight(400)
        self.installed_plugins_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.installed_plugins_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 8px;
                padding: 8px;
            }
            QListWidget::item {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 0px;
                margin: 4px;
            }
            QListWidget::item:hover {
                background-color: #2d2d30;
                border-color: #007acc;
            }
            QListWidget::item:selected {
                background-color: #094771;
                border-color: #007acc;
            }
        """)
        layout.addWidget(self.installed_plugins_list, 1)
        
        # Status label
        self.installed_status_label = QLabel("No plugins installed")
        self.installed_status_label.setFont(QFont("Segoe UI", 10))
        self.installed_status_label.setStyleSheet("color: #888888; padding: 10px;")
        self.installed_status_label.setAlignment(Qt.AlignCenter)
        self.installed_status_label.setMaximumHeight(40)
        layout.addWidget(self.installed_status_label, 0)
        
        scroll.setWidget(widget)
        
        # Auto-load on first show
        QTimer.singleShot(500, self.load_installed_plugins)
        
        return scroll
    
    def load_installed_plugins(self):
        """Load installed plugins and display in the Installed tab"""
        self.installed_status_label.setText("Loading installed plugins...")
        self.installed_status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        self.installed_plugins_list.clear()
        
        try:
            plugins_dir = Path("plugins")
            
            if not plugins_dir.exists():
                self.installed_status_label.setText("No plugins installed")
                self.installed_status_label.setStyleSheet("color: #888888; padding: 10px;")
                return
            
            installed_plugins = []
            
            for plugin_path in plugins_dir.iterdir():
                if plugin_path.name.startswith("__"):
                    continue

                # Determine plugin entry file and id
                entry_file = None
                plugin_id = plugin_path.stem if plugin_path.is_file() else plugin_path.name

                if plugin_path.is_dir():
                    init_file = plugin_path / "__init__.py"
                    if init_file.exists():
                        entry_file = init_file
                    else:
                        py_files = [p for p in plugin_path.iterdir() if p.suffix == ".py" and not p.name.startswith("__")]
                        if py_files:
                            entry_file = py_files[0]
                elif plugin_path.is_file() and plugin_path.suffix == ".py":
                    entry_file = plugin_path

                if entry_file is None:
                    continue
                
                # Try to load plugin info
                try:
                    module_name = f"plugins.installed.{plugin_id}"
                    search_locations = [str(entry_file.parent)] if entry_file.parent else None
                    spec = importlib.util.spec_from_file_location(
                        module_name,
                        str(entry_file),
                        submodule_search_locations=search_locations
                    )
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'Plugin'):
                        plugin_instance = module.Plugin(None, {})
                        
                        plugin_info = {
                            'id': plugin_id,
                            'name': plugin_instance.get_name() if hasattr(plugin_instance, 'get_name') else plugin_id,
                            'icon': plugin_instance.get_icon() if hasattr(plugin_instance, 'get_icon') else "📦",
                            'version': plugin_instance.get_version() if hasattr(plugin_instance, 'get_version') else "1.0.0",
                            'author': plugin_instance.get_author() if hasattr(plugin_instance, 'get_author') else "Unknown",
                            'description': plugin_instance.get_description() if hasattr(plugin_instance, 'get_description') else "No description",
                            'homepage': plugin_instance.get_homepage() if hasattr(plugin_instance, 'get_homepage') else "",
                            'path': plugin_path
                        }
                        
                        installed_plugins.append(plugin_info)
                except Exception as e:
                    self.log(f"Error loading plugin {plugin_id}: {e}")
            
            if not installed_plugins:
                self.installed_status_label.setText("No plugins installed")
                self.installed_status_label.setStyleSheet("color: #888888; padding: 10px;")
                return
            
            for plugin_info in installed_plugins:
                # Create list item
                item = QListWidgetItem()
                
                # Create widget for the item
                item_widget = QWidget()
                item_widget.setStyleSheet("background: transparent;")
                item_widget.setMinimumHeight(130)
                item_layout = QHBoxLayout(item_widget)
                item_layout.setContentsMargins(12, 12, 12, 12)
                item_layout.setSpacing(16)
                
                # Icon
                icon_label = QLabel(plugin_info.get("icon", "📦"))
                icon_label.setFont(QFont("Segoe UI", 28))
                icon_label.setFixedSize(50, 50)
                icon_label.setAlignment(Qt.AlignCenter)
                item_layout.addWidget(icon_label)
                
                # Info section
                info_layout = QVBoxLayout()
                info_layout.setSpacing(6)
                
                # Name and version
                name_label = QLabel(f"<b>{plugin_info['name']}</b> <span style='color: #888;'>v{plugin_info['version']}</span>")
                name_label.setFont(QFont("Segoe UI", 14))
                name_label.setStyleSheet("color: #e6e6e6;")
                info_layout.addWidget(name_label)
                
                # Author
                author_label = QLabel(f"by {plugin_info.get('author', 'Unknown')}")
                author_label.setFont(QFont("Segoe UI", 10))
                author_label.setStyleSheet("color: #888888;")
                info_layout.addWidget(author_label)
                
                # Description
                desc_label = QLabel(plugin_info.get('description', 'No description'))
                desc_label.setFont(QFont("Segoe UI", 10))
                desc_label.setStyleSheet("color: #b8b8b8;")
                desc_label.setWordWrap(True)
                desc_label.setMaximumHeight(55)
                info_layout.addWidget(desc_label)
                
                # Plugin ID/path
                path_label = QLabel(f"<span style='color: #666; font-size: 9px;'>ID: {plugin_info['id']}</span>")
                path_label.setMaximumHeight(18)
                info_layout.addWidget(path_label)
                
                info_layout.addStretch()
                item_layout.addLayout(info_layout, 1)
                
                # Uninstall button
                uninstall_btn = QPushButton("🗑️ Uninstall")
                uninstall_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
                uninstall_btn.setFixedSize(110, 40)
                uninstall_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #a12f2f;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                    }
                    QPushButton:hover {
                        background-color: #c93c3c;
                    }
                """)
                uninstall_btn.clicked.connect(lambda checked, p=plugin_info: self.uninstall_plugin(p))
                item_layout.addWidget(uninstall_btn)
                
                # Set item size and widget
                item.setSizeHint(QSize(0, 130))
                self.installed_plugins_list.addItem(item)
                self.installed_plugins_list.setItemWidget(item, item_widget)
            
            self.installed_status_label.setText(f"✓ {len(installed_plugins)} plugin(s) installed")
            self.installed_status_label.setStyleSheet("color: #00ff00; padding: 10px;")
            
        except Exception as e:
            self.installed_status_label.setText(f"❌ Failed to load: {str(e)}")
            self.installed_status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            self.log(f"Installed plugins error: {e}")
    
    def uninstall_plugin(self, plugin_info):
        """Uninstall a plugin"""
        plugin_name = plugin_info['name']
        plugin_path = plugin_info['path']
        
        # Confirm uninstallation
        reply = QMessageBox.question(
            self,
            "Uninstall Plugin",
            f"Are you sure you want to uninstall {plugin_name}?\n\n"
            f"This will delete the plugin folder and cannot be undone.\n"
            f"You can reinstall it later from the Plugin Store.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.log(f"🗑️ Uninstalling {plugin_name}...")
            
            # Delete plugin folder
            shutil.rmtree(plugin_path)
            
            self.log(f"✓ Uninstalled {plugin_name}")
            
            QMessageBox.information(
                self,
                "Plugin Uninstalled",
                f"{plugin_name} has been uninstalled.\n\nRestart the application to complete removal."
            )
            
            # Refresh both lists
            self.load_installed_plugins()
            self.load_plugin_store()
            
        except Exception as e:
            self.log(f"❌ Failed to uninstall {plugin_name}: {e}")
            QMessageBox.critical(
                self,
                "Uninstall Failed",
                f"Failed to uninstall {plugin_name}:\n\n{str(e)}"
            )
    
    def load_plugin_store(self):
        """Load plugins from GitHub index.json"""
        self.store_status_label.setText("Loading plugins...")
        self.store_status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        self.plugin_store_list.clear()

        # Clear any previous filter results but keep the text; filtering happens after fetch
        
        try:
            # Fetch index from GitHub
            index_url = "https://raw.githubusercontent.com/eman225511/RustPlusRaidAlarmPlugins/refs/heads/main/index.json"
            with urllib.request.urlopen(index_url, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            plugins = data.get("plugins", [])

            if not plugins:
                self.store_status_label.setText("No plugins available")
                self.store_status_label.setStyleSheet("color: #888888; padding: 10px;")
                return

            # cache and render with current filter
            self.store_plugins_data = plugins
            self.apply_store_filter()
            self.store_status_label.setText(f"✓ Loaded {len(plugins)} plugin(s)")
            self.store_status_label.setStyleSheet("color: #00ff00; padding: 10px;")
            
        except Exception as e:
            self.store_status_label.setText(f"❌ Failed to load: {str(e)}")
            self.store_status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            self.log(f"Plugin store error: {e}")
    
    def get_installed_plugins(self):
        """Get dictionary of installed plugins {id: version}"""
        installed = {}
        plugins_dir = Path("plugins")
        
        if not plugins_dir.exists():
            return installed
        
        for plugin_path in plugins_dir.iterdir():
            if plugin_path.name.startswith("__"):
                continue

            # Determine entry file and plugin id
            entry_file = None
            plugin_id = plugin_path.stem if plugin_path.is_file() else plugin_path.name

            if plugin_path.is_dir():
                init_file = plugin_path / "__init__.py"
                if init_file.exists():
                    entry_file = init_file
                else:
                    py_files = sorted(p for p in plugin_path.glob("*.py") if not p.name.startswith("__"))
                    if py_files:
                        entry_file = py_files[0]
            elif plugin_path.is_file() and plugin_path.suffix == ".py":
                entry_file = plugin_path

            if entry_file is None:
                continue
            
            # Try to load plugin to get version
            try:
                module_name = f"plugins.installed_meta.{plugin_id}"
                search_locations = [str(entry_file.parent)] if entry_file.parent else None
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    str(entry_file),
                    submodule_search_locations=search_locations
                )
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                if hasattr(module, 'Plugin'):
                    plugin_instance = module.Plugin(None, {})
                    if hasattr(plugin_instance, 'get_version'):
                        installed[plugin_id] = plugin_instance.get_version()
                    else:
                        installed[plugin_id] = "1.0.0"
            except Exception:
                # If can't load, just mark as installed with unknown version
                installed[plugin_id] = "unknown"
        
        return installed
    
    def install_plugin(self, plugin_info):
        """Download and install a plugin"""
        plugin_id = plugin_info['id']
        plugin_name = plugin_info['name']
        download_url = plugin_info.get('download_url', '')
        
        if not download_url:
            QMessageBox.warning(self, "Install Error", f"No download URL for {plugin_name}")
            return
        
        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install Plugin",
            f"Install {plugin_name} v{plugin_info['version']}?\n\n"
            f"Author: {plugin_info.get('author', 'Unknown')}\n"
            f"Size: ~{plugin_info.get('size_kb', '?')} KB\n\n"
            "⚠️ Only install plugins from trusted sources!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.log(f"📦 Downloading {plugin_name}...")
            
            # Create plugins directory if needed
            plugins_dir = Path("plugins")
            plugins_dir.mkdir(exist_ok=True)
            
            # Download to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = temp_file.name
                with urllib.request.urlopen(download_url, timeout=30) as response:
                    temp_file.write(response.read())
            
            # Extract to plugins directory
            plugin_path = plugins_dir / plugin_id
            
            # Backup existing if updating
            if plugin_path.exists():
                backup_path = plugins_dir / f"{plugin_id}_backup"
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.move(str(plugin_path), str(backup_path))
            
            # Extract zip
            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                zip_ref.extractall(plugin_path)
            
            # Clean up temp file
            Path(temp_path).unlink()
            
            # Check and optionally install dependencies
            deps_ok = self.ensure_plugin_dependencies(plugin_info, plugin_path)

            self.log(f"✓ Installed {plugin_name} v{plugin_info['version']}")
            
            # Reload plugins
            QMessageBox.information(
                self,
                "Plugin Installed",
                f"{plugin_name} has been installed!\n\n"
                + ("Dependencies installed. " if deps_ok else "Some dependencies may be missing. ")
                + "Restart the application to load the plugin."
            )
            
            # Refresh both store and installed lists
            self.load_plugin_store()
            self.load_installed_plugins()
            
        except Exception as e:
            self.log(f"❌ Failed to install {plugin_name}: {e}")
            QMessageBox.critical(
                self,
                "Installation Failed",
                f"Failed to install {plugin_name}:\n\n{str(e)}"
            )

    def ensure_plugin_dependencies(self, plugin_info, plugin_path):
        """Ensure required Python packages are installed for a plugin.

        Returns True if all dependencies are satisfied or installed, False otherwise.
        """
        requires = set()

        # From index.json metadata
        for req in plugin_info.get('requires', []) or []:
            req = req.strip()
            if req:
                requires.add(req)

        # From plugin-local requirements.txt
        req_file = plugin_path / "requirements.txt"
        if req_file.exists():
            try:
                for line in req_file.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith('#'):
                        requires.add(line)
            except Exception as e:
                self.log(f"⚠ Unable to read requirements.txt for {plugin_info.get('name', '')}: {e}")

        if not requires:
            return True

        def canonical_mod(req):
            mod = req.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0].split(';')[0]
            return mod.strip().replace('-', '_')

        missing = []
        for req in sorted(requires):
            mod_name = canonical_mod(req)
            try:
                if importlib.util.find_spec(mod_name) is None:
                    missing.append(req)
            except Exception:
                missing.append(req)

        if not missing:
            return True

        req_list = "\n".join(f"- {r}" for r in missing)
        install_now = QMessageBox.question(
            self,
            "Install Plugin Dependencies",
            f"{plugin_info.get('name', 'This plugin')} requires packages:\n\n{req_list}\n\nInstall them now?",
            QMessageBox.Yes | QMessageBox.No
        )

        if install_now == QMessageBox.Yes:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
                self.log(f"✓ Installed dependencies for {plugin_info.get('name', '')}: {', '.join(missing)}")
                # Offer to append to root requirements.txt for future installs
                add_reqs = QMessageBox.question(
                    self,
                    "Persist Dependencies",
                    "Add these packages to requirements.txt for next launch?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if add_reqs == QMessageBox.Yes:
                    reqs_path = Path("requirements.txt")
                    existing = set()
                    if reqs_path.exists():
                        try:
                            existing = {line.strip() for line in reqs_path.read_text().splitlines() if line.strip() and not line.startswith('#')}
                        except Exception:
                            existing = set()
                    to_append = [req for req in missing if req not in existing]
                    if to_append:
                        with reqs_path.open("a", encoding="utf-8") as f:
                            for req in to_append:
                                f.write(f"\n{req}")
                    self.log("✓ requirements.txt updated for plugin dependencies")
                return True
            except Exception as e:
                self.log(f"❌ Failed to install dependencies for {plugin_info.get('name', '')}: {e}")
                QMessageBox.critical(
                    self,
                    "Dependency Install Failed",
                    f"Failed to install dependencies:\n\n{str(e)}"
                )
                return False

        # User chose not to install now
        return False
    
    def create_vertical_tab_bar(self):
        """Create vertical tab bar on the right"""
        tab_widget = QWidget()
        tab_widget.setMaximumWidth(220)
        tab_widget.setStyleSheet("""
            QWidget {
                background-color: #1b1c1f;
                border-left: 1px solid #2a2b30;
            }
        """)
        
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(12, 16, 12, 16)
        tab_layout.setSpacing(8)
        
        # Title
        title = QLabel("Navigation")
        title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title.setStyleSheet("color: #d7d7d7; padding: 6px;")
        title.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(title)
        
        # Core button
        core_btn = DraggableButton("🏠 Core")
        core_btn.is_core_tab = True  # Core tab shouldn't be draggable
        core_btn.setFont(QFont("Segoe UI", 10))
        core_btn.setMinimumHeight(38)
        core_btn.setStyleSheet(self.get_tab_button_style(True))
        core_btn.clicked.connect(lambda: self.switch_tab(0))
        tab_layout.addWidget(core_btn)
        
        # Logs button
        logs_btn = DraggableButton("📋 Logs")
        logs_btn.is_core_tab = True  # Logs tab shouldn't be draggable
        logs_btn.setFont(QFont("Segoe UI", 10))
        logs_btn.setMinimumHeight(38)
        logs_btn.setStyleSheet(self.get_tab_button_style(False))
        logs_btn.clicked.connect(lambda: self.switch_tab(1))
        tab_layout.addWidget(logs_btn)
        
        # Clan button
        clan_btn = DraggableButton("👥 Clan")
        clan_btn.is_core_tab = True  # Clan tab shouldn't be draggable
        clan_btn.setFont(QFont("Segoe UI", 10))
        clan_btn.setMinimumHeight(38)
        clan_btn.setStyleSheet(self.get_tab_button_style(False))
        clan_btn.clicked.connect(lambda: self.switch_tab(2))
        tab_layout.addWidget(clan_btn)
        
        # Plugin Store button
        store_btn = DraggableButton("🛒 Plugin Store")
        store_btn.is_core_tab = True  # Store tab shouldn't be draggable
        store_btn.setFont(QFont("Segoe UI", 10))
        store_btn.setMinimumHeight(38)
        store_btn.setStyleSheet(self.get_tab_button_style(False))
        store_btn.clicked.connect(lambda: self.switch_tab(3))
        tab_layout.addWidget(store_btn)
        
        # Beta Features button
        beta_btn = DraggableButton("🧪 Beta Features")
        beta_btn.is_core_tab = True  # Beta tab shouldn't be draggable
        beta_btn.setFont(QFont("Segoe UI", 10))
        beta_btn.setMinimumHeight(38)
        beta_btn.setStyleSheet(self.get_tab_button_style(False))
        beta_btn.clicked.connect(lambda: self.switch_tab(4))
        tab_layout.addWidget(beta_btn)
        
        # Store tab buttons
        self.tab_buttons = [core_btn, logs_btn, clan_btn, store_btn, beta_btn]
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #2f3035;")
        tab_layout.addWidget(separator)
        
        # Plugin section
        plugin_label = QLabel("Plugins")
        plugin_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        plugin_label.setStyleSheet("color: #9aa0a6; padding: 6px;")
        plugin_label.setAlignment(Qt.AlignCenter)
        tab_layout.addWidget(plugin_label)
        
        # Show example plugins checkbox
        self.show_examples_checkbox = QCheckBox("Show Example Plugins (For Devs)")
        self.show_examples_checkbox.setChecked(self.show_example_plugins)
        self.show_examples_checkbox.setStyleSheet("""
            QCheckBox {
                color: #9aa0a6;
                font-size: 9px;
                padding: 4px 6px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)
        self.show_examples_checkbox.toggled.connect(self.on_show_examples_changed)
        tab_layout.addWidget(self.show_examples_checkbox)
        
        # Plugin buttons container
        self.plugin_buttons_layout = QVBoxLayout()
        self.plugin_buttons_layout.setSpacing(6)
        tab_layout.addLayout(self.plugin_buttons_layout)
        
        tab_layout.addStretch()
        
        return tab_widget
    
    def switch_tab(self, index):
        """Switch to a specific tab and update button styles"""
        self.content_stack.setCurrentIndex(index)
        
        # Update button styles
        for i, btn in enumerate(self.tab_buttons):
            if i == 0:
                tab_idx = 0  # core tab
            elif i == 1:
                tab_idx = 1  # logs tab
            elif i == 2:
                tab_idx = 2  # clan tab
            elif i == 3:
                tab_idx = 3  # plugin store tab
            elif i == 4:
                tab_idx = 4  # beta tab
            else:
                mapping = self.tab_button_map.get(str(id(btn)), {})
                tab_idx = mapping.get('tab_index', i)
            btn.setStyleSheet(self.get_tab_button_style(tab_idx == index))
    
    def handle_tab_reorder(self, source_id, target_id):
        """Handle reordering of tabs when dragged and dropped"""
        if source_id == target_id:
            return
        
        # Find source and target buttons in the list
        source_idx = None
        target_idx = None

        for i, btn in enumerate(self.tab_buttons):
            if str(id(btn)) == source_id:
                source_idx = i
            if str(id(btn)) == target_id:
                target_idx = i

        if source_idx is None or target_idx is None:
            return

        # Don't allow reordering with fixed tabs (Core=0, Logs=1, Clan=2, Store=3, Beta=4)
        if source_idx <= 4 or target_idx <= 4:
            return

        source_btn = self.tab_buttons[source_idx]
        target_btn = self.tab_buttons[target_idx]

        source_row = self.tab_button_map[str(id(source_btn))]['row_widget']
        target_row = self.tab_button_map[str(id(target_btn))]['row_widget']

        # Find layout positions of the rows
        def index_of_row(row_widget):
            for i in range(self.plugin_buttons_layout.count()):
                item = self.plugin_buttons_layout.itemAt(i)
                if item and item.widget() is row_widget:
                    return i
            return -1

        source_row_idx = index_of_row(source_row)
        target_row_idx = index_of_row(target_row)
        if source_row_idx == -1 or target_row_idx == -1:
            return

        # Remove source row
        self.plugin_buttons_layout.removeWidget(source_row)
        source_row.setParent(None)
        self.tab_buttons.pop(source_idx)

        # Adjust target index if needed
        if source_row_idx < target_row_idx:
            target_row_idx -= 1

        # Insert row and button back
        self.plugin_buttons_layout.insertWidget(target_row_idx, source_row)
        self.tab_buttons.insert(target_idx, source_btn)

        # Rebuild tab_button_map in new order (preserve tab_index and flags)
        new_map = {}
        for btn in self.tab_buttons[3:]:  # skip core, logs, and clan
            old = self.tab_button_map.get(str(id(btn)), {})
            new_map[str(id(btn))] = old
        self.tab_button_map.update(new_map)

        # Reattach the row to layout
        source_row.show()

        # Update the tab indices and reconnect click handlers
        self.update_tab_indices()
    
    def update_tab_indices(self):
        """Update tab indices after reordering"""
        for i, btn in enumerate(self.tab_buttons):
            # Determine the correct content_stack index for this button
            if i == 0:
                tab_idx = 0  # Core tab always 0
            elif i == 1:
                tab_idx = 1  # Logs tab always 1
            elif i == 2:
                tab_idx = 2  # Clan tab always 2
            else:
                mapping = self.tab_button_map.get(str(id(btn)), {})
                tab_idx = mapping.get('tab_index', i)

            try:
                btn.clicked.disconnect()
            except TypeError:
                # No connections to disconnect
                pass
            btn.clicked.connect(lambda checked=False, idx=tab_idx: self.switch_tab(idx))
    
    def get_tab_button_style(self, active=False):
        """Get stylesheet for tab buttons"""
        if active:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0e639c, stop:1 #0b79c8);
                    color: #ffffff;
                    border: 1px solid #0b79c8;
                    border-radius: 8px;
                    padding: 10px 12px;
                    text-align: left;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #1185d1;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: transparent;
                    color: #c7c7c7;
                    border: 1px solid transparent;
                    border-radius: 8px;
                    padding: 10px 12px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #22242a;
                    border: 1px solid #2d3036;
                }
            """
    
    def get_button_style(self, bg_color):
        """Get stylesheet for action buttons"""
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
    
    def load_plugins(self):
        """Dynamically load all plugins from the plugins directory.

        Supports both package folders (with __init__.py) and single .py files.
        """
        plugins_dir = Path("plugins")

        if not plugins_dir.exists():
            plugins_dir.mkdir()
            self.log("Created plugins directory")
            return

        # Ensure plugins dir on sys.path for package imports
        abs_plugins = str(plugins_dir.resolve())
        if abs_plugins not in sys.path:
            sys.path.insert(0, abs_plugins)

        for path in sorted(plugins_dir.iterdir()):
            if path.name.startswith('_'):
                continue

            # Package or folder plugin
            if path.is_dir():
                plugin_file = path / "__init__.py"
                if plugin_file.exists():
                    # Standard package
                    self.load_plugin(plugin_file, module_name=f"plugins.{path.name}")
                else:
                    # Try first .py file in the folder as a single-file plugin
                    py_files = sorted(p for p in path.glob("*.py") if not p.name.startswith("__"))
                    if py_files:
                        first_py = py_files[0]
                        self.load_plugin(first_py, module_name=f"plugins.{path.name}.{first_py.stem}")
                    else:
                        self.log(f"⚠ Plugin {path.name} missing __init__.py and no .py files found")

            # Single-file plugin at root
            elif path.is_file() and path.suffix == ".py":
                self.load_plugin(path, module_name=f"plugins.{path.stem}")

    def load_plugin(self, plugin_file: Path, module_name: str):
        """Load a single plugin from file"""
        plugin_key = str(plugin_file.resolve())

        # Avoid reloading already loaded plugins
        if plugin_key in self.loaded_plugin_keys:
            return

        try:
            if plugin_file.name == "__init__.py":
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    str(plugin_file),
                    submodule_search_locations=[str(plugin_file.parent)]
                )
            else:
                spec = importlib.util.spec_from_file_location(module_name, str(plugin_file))

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, 'Plugin'):
                self.log(f"⚠ Plugin {module_name} missing Plugin class")
                return

            plugin_class = module.Plugin
            plugin = plugin_class(self.telegram_service, self.config)

            if not isinstance(plugin, PluginBase):
                self.log(f"⚠ Plugin {module_name} doesn't inherit from PluginBase")
                return

            plugin_widget = plugin.get_widget()

            tab_index = self.content_stack.addTab(
                plugin_widget,
                ""
            )
            
            # Check if this is an example plugin (name or path contains "example")
            plugin_name = plugin.get_name()
            is_example = (
                "example" in plugin_name.lower()
                or "example" in plugin_file.name.lower()
                or "example" in plugin_file.parent.name.lower()
            )

            # Create plugin row with button and checkbox
            plugin_row = QWidget()
            plugin_row_layout = QHBoxLayout(plugin_row)
            plugin_row_layout.setContentsMargins(0, 0, 0, 0)
            plugin_row_layout.setSpacing(4)
            
            plugin_btn = DraggableButton(f"{plugin.get_icon()} {plugin_name}")
            plugin_btn.setFont(QFont("Segoe UI", 10))
            plugin_btn.setMinimumHeight(38)
            plugin_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            plugin_btn.setStyleSheet(self.get_tab_button_style(False))
            plugin_btn.clicked.connect(lambda checked, idx=tab_index: self.switch_tab(idx))
            
            # Enable/disable checkbox
            enable_checkbox = QCheckBox()
            # If plugin_enabled key exists in config, use that value; otherwise default to False
            config_key = f"plugin_enabled_{plugin_name}"
            if config_key in self.config:
                enable_checkbox.setChecked(self.config[config_key])
            else:
                enable_checkbox.setChecked(False)
            enable_checkbox.setToolTip(f"Enable/disable {plugin_name}")
            enable_checkbox.setStyleSheet("""
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            # Use toggled(bool) to avoid partial-check edge cases and get a clean bool
            enable_checkbox.toggled.connect(
                lambda checked, p=plugin: self.on_plugin_enabled_changed(p, checked)
            )
            
            plugin_row_layout.addWidget(plugin_btn)
            plugin_row_layout.addWidget(enable_checkbox)
            
            # Add to layout first
            self.plugin_buttons_layout.addWidget(plugin_row)
            self.tab_buttons.append(plugin_btn)
            
            # Then set visibility (must be done after adding to layout)
            if is_example and not self.show_example_plugins:
                plugin_row.hide()
            else:
                plugin_row.show()
            
            # Store mapping for reordering
            btn_id = str(id(plugin_btn))
            self.tab_button_map[btn_id] = {
                'button': plugin_btn,
                'tab_index': tab_index,
                'plugin': plugin,
                'row_widget': plugin_row,
                'checkbox': enable_checkbox,
                'is_example': is_example
            }
            
            # Store enabled state
            self.plugin_enabled[plugin_name] = enable_checkbox.isChecked()
            
            # Initialize plugin with correct enabled state
            try:
                if enable_checkbox.isChecked():
                    plugin.on_enable()
                else:
                    plugin.on_disable()
            except Exception as e:
                self.log(f"⚠ Error initializing {plugin_name} state: {str(e)}")

            self.plugins.append(plugin)
            self.plugin_widgets[plugin.get_name()] = plugin_widget

            # mark as loaded
            self.loaded_plugin_keys.add(plugin_key)

            self.log(f"✓ Loaded plugin: {plugin.get_name()}")

        except Exception as e:
            self.log(f"✗ Failed to load plugin {module_name}: {str(e)}")
    
    def on_telegram_message(self, message):
        """Handle incoming Telegram messages"""
        self.log(f"📨 Telegram message received: {message[:50]}...")
        
        # Broadcast to relay server if enabled
        if self.config.get("server_mode_enabled", False):
            self.relay_server.broadcast_message(message)
        
        # Notify all enabled plugins
        for plugin in self.plugins:
            try:
                plugin_name = plugin.get_name()
                # Only notify if plugin is enabled
                if self.plugin_enabled.get(plugin_name, True):
                    plugin.on_telegram_message(message)
            except Exception as e:
                self.log(f"✗ Plugin {plugin.get_name()} error: {str(e)}")
    
    def on_start_clicked(self):
        """Handle start button click - starts appropriate service based on mode"""
        if self.config.get("fcm_mode", False):
            # FCM mode - start FCM service
            if not self.fcm_service.is_authenticated():
                self.log("❌ Not authenticated. Please authenticate first in Beta tab.")
                return
            self.fcm_service.start()
            self.log("🔄 Starting FCM service...")
        elif self.config.get("relay_mode", False) and self.relay_client:
            # Relay mode - reconnect relay client
            self.relay_client.connect()
            self.log("🔄 Reconnecting to relay server...")
        else:
            # Direct Telegram mode
            self.telegram_service.start()
    
    def on_stop_clicked(self):
        """Handle stop button click - stops appropriate service based on mode"""
        if self.config.get("fcm_mode", False):
            # FCM mode - stop FCM service
            self.fcm_service.stop()
            self.log("⏸ FCM service stopped")
        elif self.config.get("relay_mode", False) and self.relay_client:
            # Relay mode - disconnect relay client
            self.relay_client.disconnect()
            self.log("⏸ Disconnected from relay server")
        else:
            # Direct Telegram mode
            self.telegram_service.stop()
    
    def on_telegram_status(self, status, color):
        """Update Telegram status display"""
        self.status_display.setText(status)
        self.status_display.setStyleSheet(f"color: {color}; padding: 6px 0;")

        # Update pill chip to mirror status
        self.pill_status.setText(status)
        self.pill_status.setStyleSheet(
            f"background-color: #22242a; border: 1px solid #2f3035; "
            f"color: {color}; padding: 6px 10px; border-radius: 999px; font-weight: 600;"
        )

        self.log(f"[Telegram] {status}")

    def on_polling_rate_change(self, value: int):
        """Update polling rate in config and pill"""
        self.config["polling_rate"] = int(value)
        self.save_config()
        self.pill_poll.setText(f"Polling {int(value)}s")

    def on_filter_toggle(self, state):
        """Enable/disable keyword filtering"""
        self.config["filter_enabled"] = bool(state)
        self.save_config()

    def on_filter_keyword_change(self):
        """Update keyword filter text"""
        self.config["filter_keyword"] = self.filter_input.text().strip()
        self.save_config()
    
    def on_fcm_notification(self, message):
        """Handle incoming FCM notifications"""
        self.log(f"📨 FCM notification received: {message[:50]}...")
        
        # Update last notification display
        if hasattr(self, 'fcm_last_notif'):
            self.fcm_last_notif.setText(f"Last: {message[:100]}")
            self.fcm_last_notif.setStyleSheet("color: #00ff00; font-size: 9pt; padding: 8px; background-color: #1a1a1a; border-radius: 4px;")
        
        # Update notification count
        if hasattr(self, 'fcm_notif_count'):
            try:
                count = int(self.fcm_notif_count.text()) + 1
                self.fcm_notif_count.setText(str(count))
            except:
                self.fcm_notif_count.setText("1")

        # Broadcast to relay server if enabled (same as Telegram)
        if self.config.get("server_mode_enabled", False):
            try:
                self.relay_server.broadcast_message(message)
            except Exception as e:
                self.log(f"✗ Relay broadcast error: {str(e)}")
        
        # Notify all enabled plugins (same as Telegram)
        for plugin in self.plugins:
            try:
                plugin_name = plugin.get_name()
                if self.plugin_enabled.get(plugin_name, True):
                    plugin.on_telegram_message(message)
            except Exception as e:
                self.log(f"✗ Plugin {plugin.get_name()} error: {str(e)}")
    
    def on_fcm_status(self, status, color):
        """Update FCM status display"""
        if hasattr(self, 'fcm_listener_status'):
            self.fcm_listener_status.setText(status)
            self.fcm_listener_status.setStyleSheet(f"color: {color}; padding: 4px 8px; background-color: #1a1a1a; border-radius: 4px; font-size: 10pt;")
        
        self.log(f"[FCM] {status}")
    
    def on_fcm_auth_completed(self, success, message):
        """Handle FCM authentication completion"""
        if success:
            self.log(f"✓ FCM authentication successful!")
            QMessageBox.information(self, "Authentication Complete", message)
            self.update_fcm_ui_status()
        else:
            self.log(f"✗ FCM authentication failed: {message}")
            QMessageBox.warning(self, "Authentication Failed", message)
    
    def on_fcm_authenticate(self):
        """Start FCM authentication flow"""
        # Show beta acknowledgment dialog on first use
        if not self.config.get("fcm_beta_acknowledged", False):
            from PySide6.QtWidgets import QMessageBox
            result = QMessageBox.question(
                self,
                "Beta Feature",
                "This is a beta feature that uses direct Rust+ notifications.\n\n"
                "⚠️ This will:\n"
                "• Open your browser for Steam login\n"
                "• Use Node.js to setup FCM credentials\n"
                "• Bypass Telegram completely when active\n\n"
                "Would you like to proceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
            
            self.config["fcm_beta_acknowledged"] = True
            self.save_config()
        
        self.log("Starting FCM authentication...")
        self.fcm_service.start_auth_flow()
    
    def on_fcm_start(self):
        """Start FCM mode"""
        # Enforce mandatory keyword
        keyword = (self.config.get("fcm_filter_keyword", "") or "").strip()
        if not keyword:
            QMessageBox.warning(
                self,
                "Keyword Required",
                "Please set the required keyword in the Beta tab before starting FCM mode."
            )
            return
        # Stop other services first
        if self.telegram_service.isRunning():
            self.telegram_service.stop()
            self.log("Stopped Telegram service")
        
        if self.relay_client and self.relay_client.is_connected():
            self.relay_client.disconnect()
            self.log("Disconnected from relay server")
        
        # Set FCM mode in config
        self.config["fcm_mode"] = True
        self.config["relay_mode"] = False
        self.save_config()
        
        # Start FCM service
        self.fcm_service.start()
        self.log("🧪 FCM mode started")
        
        # Update UI
        self.fcm_start_btn.setEnabled(False)
        self.fcm_stop_btn.setEnabled(True)
        self.fcm_switch_telegram_btn.show()

        # Update session timestamp
        try:
            import time as _time
            ts = _time.strftime('%Y-%m-%d %H:%M:%S')
            if hasattr(self, 'fcm_session_time'):
                self.fcm_session_time.setText(f"Started at {ts}")
                self.fcm_session_time.setStyleSheet("color: #00ff00; font-size: 9pt; font-weight: bold;")
        except:
            pass
        
        # Update connection mode status
        self.update_connection_mode_status()
    
    def on_fcm_stop(self):
        """Stop FCM mode"""
        self.fcm_service.stop()
        self.log("FCM mode stopped")
        
        # Update UI
        self.fcm_start_btn.setEnabled(True)
        self.fcm_stop_btn.setEnabled(False)

        # Update session timestamp
        try:
            import time as _time
            ts = _time.strftime('%Y-%m-%d %H:%M:%S')
            if hasattr(self, 'fcm_session_time'):
                self.fcm_session_time.setText(f"Stopped at {ts}")
                self.fcm_session_time.setStyleSheet("color: #ffa500; font-size: 9pt; font-weight: bold;")
        except:
            pass
    
    def on_fcm_switch_to_telegram(self):
        """Switch from FCM mode back to Telegram mode"""
        from PySide6.QtWidgets import QMessageBox
        result = QMessageBox.question(
            self,
            "Switch to Telegram Mode",
            "This will stop FCM mode and switch back to Telegram.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result != QMessageBox.Yes:
            return
        
        # Stop FCM
        self.fcm_service.stop()
        
        # Clear FCM mode from config
        self.config["fcm_mode"] = False
        self.save_config()
        
        # Start Telegram
        self.telegram_service.start()
        
        # Update UI
        self.fcm_start_btn.setEnabled(True)
        self.fcm_stop_btn.setEnabled(False)
        self.fcm_switch_telegram_btn.hide()
        
        # Update connection mode status
        self.update_connection_mode_status()
        
        self.log("Switched back to Telegram mode")
    
    def update_fcm_ui_status(self):
        """Update FCM UI based on current authentication status"""
        if hasattr(self, 'fcm_auth_status'):
            if self.fcm_service.is_authenticated():
                self.fcm_auth_status.setText("✓ Authenticated")
                self.fcm_auth_status.setStyleSheet("color: #00ff00; font-size: 10pt; font-weight: bold;")
                self.fcm_auth_btn.setText("🔄 Re-authenticate")
                # Gate start by keyword presence
                has_kw = bool((self.config.get("fcm_filter_keyword", "") or "").strip())
                self.fcm_start_btn.setEnabled(has_kw)
            else:
                self.fcm_auth_status.setText("Not authenticated")
                self.fcm_auth_status.setStyleSheet("color: #888888; font-size: 10pt;")
                self.fcm_auth_btn.setText("🔐 Authenticate with Steam")
                self.fcm_start_btn.setEnabled(False)
        
        # Update paired server display
        if hasattr(self, 'fcm_paired_server'):
            if self.fcm_service.is_paired():
                server_info = f"{self.fcm_service.paired_server_name} ({self.fcm_service.paired_server_ip}:{self.fcm_service.paired_server_port})"
                self.fcm_paired_server.setText(server_info)
                self.fcm_paired_server.setStyleSheet("color: #00ff00; font-size: 10pt; font-weight: bold;")
                self.fcm_disconnect_server_btn.show()
            else:
                self.fcm_paired_server.setText("Not paired")
                self.fcm_paired_server.setStyleSheet("color: #888888; font-size: 10pt;")
                self.fcm_disconnect_server_btn.hide()
    
    def on_fcm_keyword_change(self):
        """Update mandatory FCM keyword and UI gating"""
        kw = self.fcm_keyword_input.text().strip()
        self.config["fcm_filter_keyword"] = kw
        self.save_config()
        # Update start button enable state
        has_kw = bool(kw)
        # Only enable if authenticated as well
        if self.fcm_service.is_authenticated():
            self.fcm_start_btn.setEnabled(has_kw)

    def on_fcm_server_paired(self, server_name, server_address):
        """Handle server pairing event"""
        if server_name and server_address:
            self.log(f"✓ Paired with server: {server_name} @ {server_address}")
            self.update_fcm_ui_status()
        else:
            self.log("Server pairing removed")
            self.update_fcm_ui_status()
    
    def on_fcm_disconnect_server(self):
        """Disconnect from paired server"""
        from PySide6.QtWidgets import QMessageBox
        
        if not self.fcm_service.is_paired():
            return
        
        result = QMessageBox.question(
            self,
            "Disconnect Server",
            f"Disconnect from {self.fcm_service.paired_server_name}?\n\n"
            f"This will unpair the server. You'll need to pair again in-game to receive notifications from it.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            if self.fcm_service.delete_pairing():
                self.log(f"Disconnected from {self.fcm_service.paired_server_name}")
                QMessageBox.information(
                    self,
                    "Server Disconnected",
                    "Server has been unpaired. Pair with a new server in-game to receive notifications."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to disconnect server. Check logs for details."
                )
    
    def on_server_mode_toggle(self, state):
        """Enable/disable relay server mode"""
        enabled = bool(state)
        
        if enabled:
            # Ask for password (optional)
            from PySide6.QtWidgets import QMessageBox
            
            result = QMessageBox.question(
                self,
                "Server Password",
                "Set a password for your relay server?\n\n"
                "✅ Recommended - only clan members with password can connect\n"
                "⚠️ Skip - anyone with server code can connect",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Cancel:
                self.clan_server_checkbox.setChecked(False)
                return
            
            password = None
            if result == QMessageBox.Yes:
                password = self.show_password_dialog(
                    "Set Server Password",
                    "Enter password for relay server:\n(Share this with your clan)"
                )
                
                if password is None:  # User cancelled
                    self.clan_server_checkbox.setChecked(False)
                    return
                
                if password:
                    self.config["server_password"] = password
                    self.relay_server.set_password(password)
                    self.log("🔒 Server password protection enabled")
            
            self.config["server_mode_enabled"] = enabled
            self.save_config()
            self.relay_server.start()
            self.log("🌐 Relay server mode enabled - broadcasting to clients")
        else:
            self.config["server_mode_enabled"] = enabled
            self.save_config()
            self.relay_server.stop()
            self.log("🌐 Relay server mode disabled")
    
    def show_password_dialog(self, title, message):
        """Show a custom password dialog with show/hide toggle"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QHBoxLayout
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                font-size: 11pt;
            }
            QLineEdit {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                padding: 8px;
                border-radius: 4px;
                font-size: 11pt;
            }
            QCheckBox {
                color: #d4d4d4;
                font-size: 10pt;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10pt;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton#cancelButton {
                background-color: #3e3e42;
            }
            QPushButton#cancelButton:hover {
                background-color: #505053;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Message label
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # Password input
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText("Enter password...")
        layout.addWidget(password_input)
        
        # Show password checkbox
        show_password_checkbox = QCheckBox("Show password")
        show_password_checkbox.stateChanged.connect(
            lambda state: password_input.setEchoMode(
                QLineEdit.Normal if state else QLineEdit.Password
            )
        )
        layout.addWidget(show_password_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Show dialog and return result
        if dialog.exec() == QDialog.Accepted:
            return password_input.text()
        return None
    
    def save_ngrok_authtoken(self):
        """Save ngrok authtoken configuration"""
        from PySide6.QtWidgets import QMessageBox
        import subprocess
        
        authtoken = self.ngrok_authtoken_input.text().strip()
        
        if not authtoken:
            QMessageBox.warning(
                self,
                "No Token",
                "Please paste your ngrok authtoken in the input box.\n\n"
                "Get it from: https://dashboard.ngrok.com/get-started/your-authtoken"
            )
            return
        
        try:
            # Run ngrok config command
            result = subprocess.run(
                ['ngrok', 'config', 'add-authtoken', authtoken],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "✅ Success",
                    "Ngrok authtoken saved successfully!\n\n"
                    "You can now enable Relay Server Mode for internet access.\n"
                    "If server is already running, disable and re-enable it to apply changes."
                )
                self.log("✓ Ngrok authtoken configured successfully")
                self.ngrok_authtoken_input.clear()
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                QMessageBox.warning(
                    self,
                    "Configuration Failed",
                    f"Failed to configure ngrok authtoken:\n\n{error_msg}\n\n"
                    "Make sure ngrok is installed. Install pyngrok with:\n"
                    "pip install pyngrok"
                )
                self.log(f"✗ Ngrok config failed: {error_msg}")
                
        except FileNotFoundError:
            # ngrok command not found - try using pyngrok's ngrok binary
            try:
                from pyngrok import conf, installer
                
                # Ensure ngrok is installed
                ngrok_path = conf.get_default().ngrok_path
                installer.install_ngrok(ngrok_path)
                
                # Run config with pyngrok's ngrok
                result = subprocess.run(
                    [ngrok_path, 'config', 'add-authtoken', authtoken],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "✅ Success",
                        "Ngrok authtoken saved successfully!\n\n"
                        "You can now enable Relay Server Mode for internet access.\n"
                        "If server is already running, disable and re-enable it to apply changes."
                    )
                    self.log("✓ Ngrok authtoken configured successfully")
                    self.ngrok_authtoken_input.clear()
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    raise Exception(error_msg)
                    
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Configuration Failed",
                    f"Failed to configure ngrok:\n\n{str(e)}\n\n"
                    "Make sure pyngrok is installed:\n"
                    "pip install pyngrok"
                )
                self.log(f"✗ Ngrok config failed: {str(e)}")
                
        except subprocess.TimeoutExpired:
            QMessageBox.warning(
                self,
                "Timeout",
                "Ngrok configuration timed out. Please try again."
            )
            self.log("✗ Ngrok config timeout")
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Unexpected error:\n\n{str(e)}"
            )
            self.log(f"✗ Ngrok config error: {str(e)}")
    
    def on_relay_server_status(self, status, color):
        """Update relay server status display"""
        if hasattr(self, 'clan_server_status_label'):
            self.clan_server_status_label.setText(status)
            self.clan_server_status_label.setStyleSheet(f"color: {color}; padding: 6px; background-color: #1a1a1a; border-radius: 6px;")
    
    def on_tunnel_url_ready(self, url):
        """Handle ngrok tunnel URL"""
        self.log(f"🌐 Public relay URL: {url}")
        # We'll show this in the clan code export
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Config was saved in dialog, now persist to file and reload Telegram service
            self.save_config()
            self.telegram_service.stop()
            QTimer.singleShot(500, self.telegram_service.start)
    
    def generate_clan_key(self, password: str) -> bytes:
        """Generate encryption key from password using PBKDF2"""
        # Use a fixed salt for clan codes so same password = same key
        salt = b'RustPlusRaidAlarms-Clan-Salt-v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return urlsafe_b64encode(kdf.derive(password.encode()))
    
    def export_server_code(self):
        """Export relay server connection info"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QTextEdit
        
        if not self.config.get("server_mode_enabled", False):
            QMessageBox.warning(
                self,
                "Server Mode Disabled",
                "Please enable 'Relay Server Mode' in the Core tab first."
            )
            return
        
        # Get connection info
        conn_info = self.relay_server.get_connection_info()
        
        if not conn_info['public']:
            # No public URL - offer local network option
            result = QMessageBox.question(
                self,
                "No Public Access",
                "⚠️ Ngrok tunnel not available (not configured or failed to start).\n\n"
                "Your relay server is running on LOCAL NETWORK ONLY.\n"
                "Clan members must be on the same WiFi/LAN to connect.\n\n"
                f"Local URL: {conn_info['local']}\n\n"
                "Options:\n"
                "• Continue - Export local network code (same WiFi only)\n"
                "• Cancel - Set up ngrok for internet access\n\n"
                "To set up ngrok:\n"
                "1. Sign up: https://dashboard.ngrok.com/signup\n"
                "2. Get authtoken: https://dashboard.ngrok.com/get-started/your-authtoken\n"
                "3. Run: ngrok config add-authtoken YOUR_TOKEN\n"
                "4. Restart server mode\n\n"
                "Continue with local network only?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
            
            # Use local network URL
            server_url = conn_info['local']
        else:
            server_url = conn_info['public']
        
        # Create server code
        import base64
        server_data = {
            'type': 'relay_server',
            'url': server_url,
            'version': 1
        }
        
        # Obfuscate: base64 encode the JSON
        server_json = json.dumps(server_data)
        obfuscated = base64.b64encode(server_json.encode()).decode('utf-8')
        
        # Wrap with headers
        server_code = (
            "-----BEGIN RUSTPLUS SERVER CODE-----\n"
            f"{obfuscated}\n"
            "-----END RUSTPLUS SERVER CODE-----"
        )
        
        # Show dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Server Code Generated")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        network_type = "🌐 Internet (Public)" if conn_info['public'] else "🏠 Local Network Only"
        label = QLabel(f"✅ Server Code Created!\n\nNetwork: {network_type}\nShare this code with your clan members.\n\nLocal: {conn_info['local']}\nPublic: {conn_info['public'] or 'Not available'}")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: #28a745; padding: 10px;")
        layout.addWidget(label)
        
        code_display = QTextEdit()
        code_display.setPlainText(server_code)
        code_display.setReadOnly(True)
        code_display.setFont(QFont("Consolas", 10))
        code_display.setStyleSheet("""
            QTextEdit {
                background-color: #111214;
                color: #00ff00;
                border: 2px solid #28a745;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout.addWidget(code_display)
        
        # Show password hint if password is set
        password_hint = ""
        if self.config.get("server_password"):
            password_hint = f"\n\n🔒 Password: {self.config.get('server_password')}\n(Share this password with your clan!)"
        
        hint = QLabel(f"💡 Clan members import this code to connect to YOUR relay server.\nThey don't need Telegram bot setup - they connect to you!{password_hint}")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #17a2b8; padding: 10px;")
        layout.addWidget(hint)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.exec()
        self.log("✓ Server code exported")
    
    def import_server_code(self):
        """Import relay server connection info and connect"""
        from PySide6.QtWidgets import QMessageBox, QDialog, QTextEdit, QLabel
        
        # Create input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Server Code")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Paste the server code below:")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: #d4d4d4; padding: 10px;")
        layout.addWidget(label)
        
        code_input = QTextEdit()
        code_input.setPlaceholderText("Paste server code here...")
        code_input.setFont(QFont("Consolas", 10))
        code_input.setStyleSheet("""
            QTextEdit {
                background-color: #111214;
                color: #d4d4d4;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout.addWidget(code_input)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        server_code = code_input.toPlainText().strip()
        if not server_code:
            return
        
        try:
            # Remove header/footer if present and extract base64 content
            import base64
            
            server_code_clean = server_code.strip()
            
            if "-----BEGIN RUSTPLUS SERVER CODE-----" in server_code_clean:
                # Extract content between headers
                lines = server_code_clean.split('\n')
                code_lines = []
                in_content = False
                
                for line in lines:
                    if "-----BEGIN RUSTPLUS SERVER CODE-----" in line:
                        in_content = True
                        continue
                    elif "-----END RUSTPLUS SERVER CODE-----" in line:
                        break
                    elif in_content:
                        code_lines.append(line.strip())
                
                obfuscated = ''.join(code_lines)
                # Decode from base64 to get original JSON
                decoded = base64.b64decode(obfuscated).decode('utf-8')
                server_data = json.loads(decoded)
            else:
                # Legacy format - plain JSON
                server_data = json.loads(server_code_clean)
            
            if server_data.get('type') != 'relay_server':
                raise ValueError("Invalid server code type")
            
            server_url = server_data.get('url')
            if not server_url:
                raise ValueError("Missing server URL")
            
            # Confirm
            result = QMessageBox.question(
                self,
                "Confirm Import",
                f"Connect to relay server:\n{server_url}\n\nYou will receive alerts from this server instead of directly from Telegram.\n\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
            
            # Ask for password if server requires it
            password = self.show_password_dialog(
                "Server Password",
                "Enter relay server password:\n(If the server has no password, leave blank)"
            )
            
            if password is None:  # User cancelled
                return
            
            # Disconnect existing client if any
            if self.relay_client:
                self.relay_client.disconnect()
            
            # Create and connect new client
            self.relay_client = RelayClient(server_url, password=password if password else None)
            self.relay_client.message_received.connect(self.on_relay_message)
            self.relay_client.status_changed.connect(self.on_relay_client_status)
            self.relay_client.connect()
            
            # Save to config
            self.config["relay_client_server"] = server_url
            if password:
                self.config["relay_client_password"] = password
            self.config["relay_mode"] = True  # Mark as using relay mode
            self.save_config()
            
            # Update UI mode status
            self.update_connection_mode_status()
            
            QMessageBox.information(
                self,
                "Connected",
                f"Successfully connected to relay server!\n\n✅ You are now in RELAY MODE\n\nAlerts will come from the relay server instead of direct Telegram.\nYour Telegram service will be stopped to avoid conflicts."
            )
            
            # Stop Telegram service when in relay mode
            self.telegram_service.stop()
            
            self.log(f"✓ Connected to relay server: {server_url}")
            self.log("ℹ️ Switched to Relay Mode - Telegram service stopped")
            
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Invalid Code", "The server code is not valid JSON")
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to import server code:\n{str(e)}")
            self.log(f"✗ Server code import failed: {str(e)}")
    
    def on_relay_message(self, message):
        """Handle message received from relay client"""
        self.log(f"📨 Relay message received: {message[:50]}...")
        
        # Notify all enabled plugins (same as Telegram message)
        for plugin in self.plugins:
            try:
                plugin_name = plugin.get_name()
                if self.plugin_enabled.get(plugin_name, True):
                    plugin.on_telegram_message(message)
            except Exception as e:
                self.log(f"✗ Plugin {plugin.get_name()} error: {str(e)}")
    
    def on_relay_client_status(self, status, color):
        """Update relay client status"""
        self.log(f"🌐 Relay: {status}")
    
    def disconnect_from_relay(self):
        """Disconnect from relay server and switch back to direct Telegram"""
        from PySide6.QtWidgets import QMessageBox
        
        result = QMessageBox.question(
            self,
            "Switch to Direct Telegram",
            "Disconnect from relay server and switch back to direct Telegram mode?\n\n"
            "✅ Your Telegram service will restart\n"
            "✅ You'll receive alerts directly from Telegram bot\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result != QMessageBox.Yes:
            return
        
        # Disconnect relay client
        if self.relay_client:
            self.relay_client.disconnect()
            self.relay_client = None
        
        # Remove from config
        self.config.pop("relay_client_server", None)
        self.config.pop("relay_client_password", None)
        self.config["relay_mode"] = False
        self.save_config()
        
        # Restart Telegram service
        self.telegram_service.start()
        
        # Update UI
        self.update_connection_mode_status()
        
        self.log("✓ Disconnected from relay server")
        self.log("✓ Switched back to Direct Telegram Mode")
        
        QMessageBox.information(
            self,
            "Switched to Direct Telegram",
            "✅ Successfully switched to Direct Telegram Mode\n\n"
            "Your Telegram service is now active and receiving alerts directly."
        )
    
    def restore_relay_connection(self):
        """Restore relay client connection on app startup"""
        server_url = self.config.get("relay_client_server")
        password = self.config.get("relay_client_password")
        
        if not server_url:
            return
        
        try:
            self.log(f"🔄 Restoring relay connection to: {server_url}")
            
            # Create and connect relay client
            self.relay_client = RelayClient(server_url, password=password if password else None)
            self.relay_client.message_received.connect(self.on_relay_message)
            self.relay_client.status_changed.connect(self.on_relay_client_status)
            self.relay_client.connect()
            
            self.log(f"✓ Relay connection restored")
            
        except Exception as e:
            self.log(f"✗ Failed to restore relay connection: {str(e)}")
            # If restore fails, switch back to direct Telegram
            self.config["relay_mode"] = False
            self.save_config()
            self.telegram_service.start()
    
    def update_connection_mode_status(self):
        """Update the connection mode status display"""
        if not hasattr(self, 'clan_mode_status'):
            return
        
        if self.config.get("fcm_mode", False):
            # FCM mode
            self.clan_mode_status.setText("🧪 FCM Direct Mode (Beta)")
            self.clan_mode_status.setStyleSheet("color: #ffa500; padding: 8px; background-color: #1a1a1a; border-radius: 6px; font-size: 11pt;")
            self.disconnect_relay_btn.hide()
            
            # Update Core tab title
            if hasattr(self, 'core_title') and hasattr(self, 'core_subtitle'):
                self.core_title.setText("FCM Listener")
                self.core_subtitle.setText("Direct Rust+ notifications via Firebase Cloud Messaging")
            
            # Hide warning on Core tab
            if hasattr(self, 'core_relay_warning'):
                self.core_relay_warning.hide()
                
        elif self.config.get("relay_mode", False) and self.config.get("relay_client_server"):
            # Relay mode
            server_url = self.config.get("relay_client_server", "unknown")
            self.clan_mode_status.setText(f"🔹 Relay Mode - Connected to: {server_url}")
            self.clan_mode_status.setStyleSheet("color: #6c42f5; padding: 8px; background-color: #1a1a1a; border-radius: 6px; font-size: 11pt;")
            self.disconnect_relay_btn.show()
            
            # Update Core tab title
            if hasattr(self, 'core_title') and hasattr(self, 'core_subtitle'):
                self.core_title.setText("Relay Client")
                self.core_subtitle.setText(f"Connected to relay server: {server_url}")
            
            # Show warning on Core tab
            if hasattr(self, 'core_relay_warning'):
                self.core_relay_warning.show()
        else:
            # Direct Telegram mode
            self.clan_mode_status.setText("🔹 Direct Telegram Mode")
            self.clan_mode_status.setStyleSheet("color: #17a2b8; padding: 8px; background-color: #1a1a1a; border-radius: 6px; font-size: 11pt;")
            self.disconnect_relay_btn.hide()
            
            # Update Core tab title
            if hasattr(self, 'core_title') and hasattr(self, 'core_subtitle'):
                self.core_title.setText("Telegram Listener")
                self.core_subtitle.setText("Live raid alerts piped into plugins and actions")
            
            # Hide warning on Core tab
            if hasattr(self, 'core_relay_warning'):
                self.core_relay_warning.hide()
    
    def export_clan_code(self):
        """Export Telegram settings as encrypted clan code"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog, QTextEdit
        
        # Get Telegram settings
        bot_token = self.config.get("telegram_bot_token", "")
        chat_id = self.config.get("telegram_chat_id", "")
        
        if not bot_token or not chat_id:
            QMessageBox.warning(
                self,
                "Missing Settings",
                "Please configure your Telegram bot token and chat ID in Settings first."
            )
            return
        
        # Ask for password with show password option
        from PySide6.QtWidgets import QVBoxLayout, QCheckBox, QLineEdit
        
        password_dialog = QDialog(self)
        password_dialog.setWindowTitle("Create Clan Code")
        password_dialog.setMinimumWidth(400)
        
        pwd_layout = QVBoxLayout(password_dialog)
        
        pwd_label = QLabel("Enter a password for your clan code:\n(Share this password with your clan members)")
        pwd_label.setStyleSheet("color: #d4d4d4; padding: 10px;")
        pwd_layout.addWidget(pwd_label)
        
        pwd_input = QLineEdit()
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_input.setFont(QFont("Segoe UI", 11))
        pwd_input.setMinimumHeight(32)
        pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        pwd_layout.addWidget(pwd_input)
        
        show_pwd_check = QCheckBox("Show Password")
        show_pwd_check.setStyleSheet("color: #d4d4d4; padding: 5px;")
        show_pwd_check.stateChanged.connect(
            lambda state: pwd_input.setEchoMode(QLineEdit.Normal if state else QLineEdit.Password)
        )
        pwd_layout.addWidget(show_pwd_check)
        
        pwd_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        pwd_buttons.accepted.connect(password_dialog.accept)
        pwd_buttons.rejected.connect(password_dialog.reject)
        pwd_layout.addWidget(pwd_buttons)
        
        if password_dialog.exec() != QDialog.Accepted:
            return
        
        password = pwd_input.text()
        if not password:
            return
        
        # Create clan data
        clan_data = {
            "bot_token": bot_token,
            "chat_id": chat_id,
            "version": 1
        }
        
        try:
            # Encrypt the data
            key = self.generate_clan_key(password)
            fernet = Fernet(key)
            encrypted = fernet.encrypt(json.dumps(clan_data).encode())
            
            # Obfuscate further: base64 encode the encrypted data and add metadata wrapper
            import base64
            obfuscated = base64.b64encode(encrypted).decode('utf-8')
            
            # Create wrapped clan code with header/footer to make it look more official
            clan_code = (
                "-----BEGIN RUSTPLUS CLAN CODE-----\n"
                f"{obfuscated}\n"
                "-----END RUSTPLUS CLAN CODE-----"
            )
            
            # Show dialog with clan code
            dialog = QDialog(self)
            dialog.setWindowTitle("Clan Code Generated")
            dialog.setMinimumWidth(600)
            dialog.setMinimumHeight(300)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("✅ Clan Code Created!\n\nShare this code and password with your clan members:")
            label.setFont(QFont("Segoe UI", 11))
            label.setStyleSheet("color: #28a745; padding: 10px;")
            layout.addWidget(label)
            
            code_display = QTextEdit()
            code_display.setPlainText(clan_code)
            code_display.setReadOnly(True)
            code_display.setFont(QFont("Consolas", 10))
            code_display.setStyleSheet("""
                QTextEdit {
                    background-color: #111214;
                    color: #00ff00;
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            layout.addWidget(code_display)
            
            # Show password checkbox for generated code
            from PySide6.QtWidgets import QCheckBox
            show_code_check = QCheckBox(f"Show Password: {password}")
            show_code_check.setStyleSheet("color: #d4d4d4; padding: 5px;")
            show_code_check.stateChanged.connect(
                lambda state: show_code_check.setText(f"Show Password: {password}" if state else "Show Password: " + "●" * len(password))
            )
            show_code_check.setText("Show Password: " + "●" * len(password))
            layout.addWidget(show_code_check)
            
            hint = QLabel("⚠️ Keep your password secret! Anyone with the code + password can access your Telegram channel.")
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #ffa500; padding: 10px;")
            layout.addWidget(hint)
            
            button_box = QDialogButtonBox(QDialogButtonBox.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec()
            self.log("✓ Clan code exported successfully")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to create clan code:\n{str(e)}"
            )
            self.log(f"✗ Clan code export failed: {str(e)}")
    
    def import_clan_code(self):
        """Import Telegram settings from encrypted clan code"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog, QTextEdit, QLabel
        
        # Create input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Clan Code")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(350)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("Paste your clan code below:")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color: #d4d4d4; padding: 10px;")
        layout.addWidget(label)
        
        code_input = QTextEdit()
        code_input.setPlaceholderText("Paste clan code here...")
        code_input.setFont(QFont("Consolas", 10))
        code_input.setStyleSheet("""
            QTextEdit {
                background-color: #111214;
                color: #d4d4d4;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout.addWidget(code_input)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() != QDialog.Accepted:
            return
        
        clan_code = code_input.toPlainText().strip()
        if not clan_code:
            return
        
        # Ask for password with show password option
        from PySide6.QtWidgets import QCheckBox, QLineEdit
        
        password_dialog = QDialog(self)
        password_dialog.setWindowTitle("Enter Password")
        password_dialog.setMinimumWidth(400)
        
        pwd_layout = QVBoxLayout(password_dialog)
        
        pwd_label = QLabel("Enter the clan code password:\n(Ask your clan leader for the password)")
        pwd_label.setStyleSheet("color: #d4d4d4; padding: 10px;")
        pwd_layout.addWidget(pwd_label)
        
        pwd_input = QLineEdit()
        pwd_input.setEchoMode(QLineEdit.Password)
        pwd_input.setFont(QFont("Segoe UI", 11))
        pwd_input.setMinimumHeight(32)
        pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        pwd_layout.addWidget(pwd_input)
        
        show_pwd_check = QCheckBox("Show Password")
        show_pwd_check.setStyleSheet("color: #d4d4d4; padding: 5px;")
        show_pwd_check.stateChanged.connect(
            lambda state: pwd_input.setEchoMode(QLineEdit.Normal if state else QLineEdit.Password)
        )
        pwd_layout.addWidget(show_pwd_check)
        
        pwd_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        pwd_buttons.accepted.connect(password_dialog.accept)
        pwd_buttons.rejected.connect(password_dialog.reject)
        pwd_layout.addWidget(pwd_buttons)
        
        if password_dialog.exec() != QDialog.Accepted:
            return
        
        password = pwd_input.text()
        if not password:
            return
        
        try:
            # Remove header/footer if present and extract base64 content
            import base64
            
            # Strip whitespace and check for headers
            clan_code_clean = clan_code.strip()
            
            if "-----BEGIN RUSTPLUS CLAN CODE-----" in clan_code_clean:
                # Extract content between headers
                lines = clan_code_clean.split('\n')
                code_lines = []
                in_content = False
                
                for line in lines:
                    if "-----BEGIN RUSTPLUS CLAN CODE-----" in line:
                        in_content = True
                        continue
                    elif "-----END RUSTPLUS CLAN CODE-----" in line:
                        break
                    elif in_content:
                        code_lines.append(line.strip())
                
                obfuscated = ''.join(code_lines)
                # Decode from base64 to get original encrypted bytes
                encrypted_bytes = base64.b64decode(obfuscated)
            else:
                # Legacy format or raw encrypted data
                encrypted_bytes = clan_code_clean.encode()
            
            # Decrypt the clan code
            key = self.generate_clan_key(password)
            fernet = Fernet(key)
            decrypted = fernet.decrypt(encrypted_bytes)
            clan_data = json.loads(decrypted.decode('utf-8'))
            
            # Validate data
            if not isinstance(clan_data, dict):
                raise ValueError("Invalid clan code format")
            
            bot_token = clan_data.get("bot_token")
            chat_id = clan_data.get("chat_id")
            
            if not bot_token or not chat_id:
                raise ValueError("Clan code is missing required settings")
            
            # Confirm import
            result = QMessageBox.question(
                self,
                "Confirm Import",
                f"This will update your Telegram settings to:\n\n"
                f"Bot Token: {bot_token[:20]}...{bot_token[-10:]}\n"
                f"Chat ID: {chat_id}\n\n"
                f"Your current settings will be overwritten. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
            
            # Apply settings
            self.config["telegram_bot_token"] = bot_token
            self.config["telegram_chat_id"] = chat_id
            self.save_config()
            
            # Restart Telegram service
            self.telegram_service.stop()
            QTimer.singleShot(500, self.telegram_service.start)
            
            QMessageBox.information(
                self,
                "Import Successful",
                "✅ Clan code imported successfully!\n\nYour Telegram settings have been updated and the service has been restarted."
            )
            self.log("✓ Clan code imported and applied successfully")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import clan code:\n{str(e)}\n\nMake sure you entered the correct password."
            )
            self.log(f"✗ Clan code import failed: {str(e)}")
    
    def on_plugin_enabled_changed(self, plugin, is_enabled: bool):
        """Handle plugin enable/disable checkbox change"""
        plugin_name = plugin.get_name()
        is_enabled = bool(is_enabled)
        self.plugin_enabled[plugin_name] = is_enabled
        self.config[f"plugin_enabled_{plugin_name}"] = is_enabled
        self.save_config()
        
        try:
            if is_enabled:
                plugin.on_enable()
            else:
                plugin.on_disable()
        except Exception as e:
            # Keep UI responsive even if a plugin errors during toggle
            self.log(f"✗ Plugin '{plugin_name}' toggle error: {str(e)}")
        
        status = "enabled" if is_enabled else "disabled"
        self.log(f"Plugin '{plugin_name}' {status}")
    
    def on_show_examples_changed(self, checked: bool):
        """Handle show example plugins checkbox change"""
        # Ensure checkbox reflects the requested state
        if self.show_examples_checkbox.isChecked() != checked:
            self.show_examples_checkbox.setChecked(checked)

        self.show_example_plugins = bool(checked)
        self.config["show_example_plugins"] = self.show_example_plugins
        self.save_config()
        
        # Show/hide example plugin rows
        count_shown = 0
        count_total = 0
        for btn_id, mapping in self.tab_button_map.items():
            if mapping.get('is_example', False):
                count_total += 1
                row_widget = mapping['row_widget']
                if self.show_example_plugins:
                    row_widget.show()
                    count_shown += 1
                else:
                    row_widget.hide()

        # Force layout refresh to avoid stale visibility
        self.plugin_buttons_layout.update()
        self.tab_bar.update()

        # Diagnostics in log
        self.log(f"Show example toggle -> {'ON' if self.show_example_plugins else 'OFF'}, total examples: {count_total}, visible now: {count_shown}")
        
        if self.show_example_plugins:
            self.log(f"Example plugins shown ({count_shown} plugins)")
        else:
            self.log(f"Example plugins hidden")
    
    def log(self, message):
        """Add message to activity log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")

    def clear_log(self):
        """Clear activity log display"""
        self.log_display.clear()
    
    def apply_dark_theme(self):
        """Apply modern dark theme to application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #cccccc;
                padding: 12px 20px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #0e639c;
                color: #ffffff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
            QLabel {
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #2d2d30;
                border: 2px solid #3e3e42;
                border-radius: 5px;
                padding: 8px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border: 2px solid #0e639c;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4e4e52;
            }
            # Cards
            QFrame#card {
                background-color: #131418;
                border: 1px solid #2a2c33;
                border-radius: 14px;
            }
            QFrame#heroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f1f33, stop:1 #0b2a46);
                border: 1px solid #12395c;
                border-radius: 16px;
            }
            QLabel#pill, QLabel#pillMuted {
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 10pt;
                font-weight: 600;
            }
            QLabel#pill {
                background-color: #13293d;
                color: #7fcbff;
                border: 1px solid #1f4f73;
            }
            QLabel#pillMuted {
                background-color: #22242a;
                color: #9aa0a6;
                border: 1px solid #2f3035;
            }
        """)
    
    def closeEvent(self, event):
        """Handle application close"""
        print("[App] Closing application...")
        self.telegram_service.stop()
        
        # Stop relay server if running
        if self.relay_server:
            self.relay_server.stop()
        
        # Disconnect relay client if connected
        if self.relay_client:
            self.relay_client.disconnect()
        
        # Wait for thread to finish
        if self.telegram_service.isRunning():
            print("[App] Waiting for Telegram service to stop...")
            self.telegram_service.wait(5000)
        
        self.save_config()
        print("[App] Application closed cleanly")
        event.accept()


class SettingsDialog(QDialog):
    """Settings dialog for configuring Telegram credentials"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Telegram Settings")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Telegram Bot Configuration")
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setStyleSheet("color: #ffffff;")
        layout.addWidget(header)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        self.bot_token_input = QLineEdit(config.get("telegram_bot_token", ""))
        self.bot_token_input.setPlaceholderText("1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.bot_token_input.setMinimumHeight(35)
        form.addRow("Bot Token:", self.bot_token_input)
        
        self.chat_id_input = QLineEdit(config.get("telegram_chat_id", ""))
        self.chat_id_input.setPlaceholderText("-1001234567890")
        self.chat_id_input.setMinimumHeight(35)
        form.addRow("Chat ID:", self.chat_id_input)
        
        layout.addLayout(form)
        
        # Instructions
        instructions = QLabel(
            "<b>How to get these:</b><br>"
            "1. Create a bot with @BotFather on Telegram<br>"
            "2. Copy the bot token<br>"
            "3. Add bot to your channel/group<br>"
            "4. Get chat ID using @userinfobot or @getidsbot"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #b8b8b8; padding: 10px; background-color: #2d2d30; border-radius: 8px;")
        layout.addWidget(instructions)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
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
        layout.addWidget(button_box)
        
        # Apply dark theme to dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #2d2d30;
                border: 2px solid #3e3e42;
                border-radius: 5px;
                padding: 8px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border: 2px solid #0e639c;
            }
        """)
    
    def save_and_accept(self):
        """Save settings to config and close dialog"""
        self.config["telegram_bot_token"] = self.bot_token_input.text().strip()
        self.config["telegram_chat_id"] = self.chat_id_input.text().strip()
        self.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
