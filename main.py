"""
RustPlus Raid Alarms - Plugin-based Application
Main application with Telegram listener and plugin system
"""

import sys
import json
import importlib.util
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTabWidget,
                               QTextEdit, QFrame, QScrollArea, QSplitter,
                               QCheckBox, QLineEdit, QSpinBox, QDialog,
                               QFormLayout, QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from telegram_service import TelegramService
from plugin_base import PluginBase

CONFIG_FILE = "config.json"


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
        
        # Plugin system
        self.plugins = []
        self.plugin_widgets = {}
        self.loaded_plugin_keys = set()  # track loaded plugin files
        
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
        
        # Auto-start Telegram listener
        QTimer.singleShot(500, self.telegram_service.start)
    
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

        title = QLabel("Telegram Listener")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        hero_layout.addWidget(title)

        subtitle = QLabel("Live raid alerts piped into plugins and actions")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        hero_layout.addWidget(subtitle)

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
        self.start_btn.clicked.connect(self.telegram_service.start)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏸ Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 11))
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setStyleSheet(self.get_button_style("#c50f1f"))
        self.stop_btn.clicked.connect(self.telegram_service.stop)
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

        # Activity log card
        log_frame = QFrame()
        log_frame.setObjectName("card")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(16, 16, 16, 16)
        log_layout.setSpacing(10)

        log_header = QHBoxLayout()
        log_label = QLabel("Activity Log")
        log_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        log_label.setStyleSheet("color: #e6e6e6;")
        log_header.addWidget(log_label)
        log_header.addStretch()
        log_layout.addLayout(log_header)

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

        layout.addStretch()

        return widget
    
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
        core_btn = QPushButton("🏠 Core")
        core_btn.setFont(QFont("Segoe UI", 10))
        core_btn.setMinimumHeight(38)
        core_btn.setStyleSheet(self.get_tab_button_style(True))
        core_btn.clicked.connect(lambda: self.switch_tab(0))
        tab_layout.addWidget(core_btn)
        
        # Store tab buttons
        self.tab_buttons = [core_btn]
        
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
            btn.setStyleSheet(self.get_tab_button_style(i == index))
    
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

            # Package plugin
            if path.is_dir():
                plugin_file = path / "__init__.py"
                if plugin_file.exists():
                    self.load_plugin(plugin_file, module_name=f"plugins.{path.name}")
                else:
                    self.log(f"⚠ Plugin {path.name} missing __init__.py")

            # Single-file plugin
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

            plugin_btn = QPushButton(f"{plugin.get_icon()} {plugin.get_name()}")
            plugin_btn.setFont(QFont("Segoe UI", 10))
            plugin_btn.setMinimumHeight(38)
            plugin_btn.setStyleSheet(self.get_tab_button_style(False))
            plugin_btn.clicked.connect(lambda checked, idx=tab_index: self.switch_tab(idx))
            self.plugin_buttons_layout.addWidget(plugin_btn)
            self.tab_buttons.append(plugin_btn)

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
        
        # Notify all plugins
        for plugin in self.plugins:
            try:
                plugin.on_telegram_message(message)
            except Exception as e:
                self.log(f"✗ Plugin {plugin.get_name()} error: {str(e)}")
    
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
    
    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Config was updated, reload Telegram service
            self.telegram_service.stop()
            QTimer.singleShot(500, self.telegram_service.start)
    
    def log(self, message):
        """Add message to activity log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_display.append(f"[{timestamp}] {message}")
    
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
        self.telegram_service.stop()
        self.save_config()
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
        button_box.accepted.connect(self.accept)
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


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
