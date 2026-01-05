import sys
import time
import threading
import requests
import json
import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QRadioButton, QButtonGroup, QSpinBox, QFrame,
                               QDialog, QTextEdit, QColorDialog, QMessageBox,
                               QTabWidget, QProgressBar, QToolTip, QComboBox,
                               QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QPropertyAnimation, QEasingCurve, QObject
from PySide6.QtGui import QFont, QColor, QIcon, QTextCursor
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from led_controllers import create_led_controller, GoveeController

CONFIG_FILE = "config.json"

class EmittingStream(QObject):
    """Stream that emits signals for GUI logging"""
    textWritten = Signal(str)

    def write(self, text):
        if text.strip():  # Only emit non-empty strings
            self.textWritten.emit(text.strip())

    def flush(self):
        pass

class TelegramWorker(QThread):
    """Worker thread for polling Telegram"""
    status_update = Signal(str, str)  # message, color
    log_message = Signal(str)  # for logging to GUI
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        self.trigger_callback = None
        
    def run(self):
        self.log_message.emit("[TELEGRAM] Starting Telegram bot connection...")
        self.status_update.emit("Connecting to Telegram...", "orange")
        
        bot_token = self.config.get("telegram_bot_token", "")
        chat_id = self.config.get("telegram_chat_id", "")
        
        if not bot_token or not chat_id:
            error_msg = "ERROR: Telegram bot token or chat ID not set!"
            self.log_message.emit(f"[TELEGRAM] {error_msg}")
            self.status_update.emit(error_msg, "red")
            return
        
        # Validate bot token format
        if ":" not in bot_token or len(bot_token.split(":")) != 2:
            error_msg = "ERROR: Invalid bot token format! Should be like: 123456789:ABCdefGHI..."
            self.log_message.emit(f"[TELEGRAM] {error_msg}")
            self.status_update.emit(error_msg, "red")
            return
        
        # Create one event loop for this thread and keep it alive
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            print(f"[TELEGRAM] Connecting to bot...")
            print(f"[TELEGRAM] Bot token: {bot_token[:10]}...{bot_token[-10:]}")
            print(f"[TELEGRAM] Chat ID: {chat_id}")
            
            # Create bot with custom timeout
            from telegram.request import HTTPXRequest
            request = HTTPXRequest(connection_pool_size=1, connect_timeout=30, read_timeout=30)
            bot = Bot(token=bot_token, request=request)
            
            # Test connection with timeout
            print("[TELEGRAM] Testing bot connection (30s timeout)...")
            bot_info = asyncio.wait_for(bot.get_me(), timeout=30.0)
            bot_info = loop.run_until_complete(bot_info)
            print(f"[TELEGRAM] ✓ Connected as @{bot_info.username} ({bot_info.first_name})")
            self.status_update.emit(f"✓ Connected as @{bot_info.username}! Waiting for messages...", "green")
                
        except asyncio.TimeoutError:
            error_msg = "ERROR: Connection timed out! Check your internet connection."
            self.log_message.emit(f"[TELEGRAM] {error_msg}")
            self.status_update.emit(error_msg, "red")
            return
        except TelegramError as e:
            if "Unauthorized" in str(e):
                error_msg = "ERROR: Invalid bot token! Check your bot token."
            elif "Not Found" in str(e):
                error_msg = "ERROR: Bot not found! Check your bot token."
            elif "Forbidden" in str(e):
                error_msg = "ERROR: Bot access forbidden! Make sure bot is active."
            else:
                error_msg = f"Telegram error: {str(e)}"
            self.log_message.emit(f"[TELEGRAM] {error_msg}")
            self.status_update.emit(error_msg, "red")
            return
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            self.log_message.emit(f"[TELEGRAM] {error_msg}")
            self.status_update.emit(error_msg, "red")
            return

        self.log_message.emit(f"[TELEGRAM] Starting polling loop (every {self.config.get('polling_rate', 2)} seconds...)")
        last_update_id = 0
        
        while self.running:
            try:
                # Use the same event loop throughout with timeout and offset
                get_updates_params = {"timeout": 5, "offset": last_update_id + 1 if last_update_id > 0 else None}
                get_updates_task = asyncio.wait_for(bot.get_updates(**get_updates_params), timeout=10.0)
                updates = loop.run_until_complete(get_updates_task)
                
                print(f"[TELEGRAM] Received {len(updates)} updates")
                
                # Process all updates
                for update in updates:
                    last_update_id = update.update_id
                    print(f"[TELEGRAM] Processing update ID: {update.update_id}")
                    
                    # Check for regular messages
                    if update.message:
                        message_chat_id = str(update.message.chat_id)
                        message_id = update.message.message_id
                        message_text = update.message.text or ""
                        
                        print(f"[TELEGRAM] Message from chat {message_chat_id}, expected {chat_id}")
                        print(f"[TELEGRAM] Message text: '{message_text}'")
                        
                        if message_chat_id == str(chat_id):
                            if message_id > self.config.get("last_message_id", 0):
                                print(f"[TELEGRAM] ✓ New message detected! ID: {message_id}")
                                
                                if self.trigger_callback:
                                    self.trigger_callback()
                                
                                self.config["last_message_id"] = message_id
                                with open(CONFIG_FILE, "w") as f:
                                    json.dump(self.config, f, indent=4)
                                print(f"[TELEGRAM] Updated last_message_id to {message_id}")
                            else:
                                print(f"[TELEGRAM] Message ID {message_id} already processed (last: {self.config.get('last_message_id', 0)})")
                        else:
                            print(f"[TELEGRAM] Ignoring message from different chat: {message_chat_id}")
                    
                    # Check for channel posts
                    elif update.channel_post:
                        post_chat_id = str(update.channel_post.chat_id)
                        post_id = update.channel_post.message_id
                        post_text = update.channel_post.text or ""
                        
                        print(f"[TELEGRAM] Channel post from chat {post_chat_id}, expected {chat_id}")
                        print(f"[TELEGRAM] Post text: '{post_text}'")
                        
                        if post_chat_id == str(chat_id):
                            if post_id > self.config.get("last_message_id", 0):
                                print(f"[TELEGRAM] ✓ New channel post detected! ID: {post_id}")
                                
                                if self.trigger_callback:
                                    self.trigger_callback()
                                
                                self.config["last_message_id"] = post_id
                                with open(CONFIG_FILE, "w") as f:
                                    json.dump(self.config, f, indent=4)
                                print(f"[TELEGRAM] Updated last_message_id to {post_id}")
                            else:
                                print(f"[TELEGRAM] Post ID {post_id} already processed (last: {self.config.get('last_message_id', 0)})")
                        else:
                            print(f"[TELEGRAM] Ignoring post from different channel: {post_chat_id}")
                    
                    else:
                        print(f"[TELEGRAM] Update type not handled: {type(update)}")

            except asyncio.TimeoutError:
                print("[TELEGRAM] Polling timeout (normal, continuing...)")
            except Exception as e:
                print(f"[ERROR] Failed to poll Telegram: {str(e)}")
                self.status_update.emit(f"Error polling: {str(e)[:50]}", "red")

            # Use configurable polling rate with interruptible sleep
            sleep_time = self.config.get("polling_rate", 2)
            for i in range(sleep_time * 10):  # Check every 0.1 seconds
                if not self.running:
                    break
                time.sleep(0.1)
        
        # Clean up the event loop when done
        loop.close()
    
    def stop(self):
        self.running = False
        # Force quit to avoid waiting for sleep
        self.quit()


class SetupDialog(QDialog):
    """Dialog showing Telegram setup instructions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rust+ WLED Setup Guide")
        self.setFixedSize(750, 700)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        
        setup_text = """🚀 RUST+ WLED TRIGGER SETUP GUIDE

🎯 OVERVIEW:
This app monitors your Telegram channel for Rust+ messages and triggers WLED actions.
When IFTTT sends Rust+ notifications to your channel, this app will detect them and 
control your WLED lights automatically!

1. CREATE YOUR TELEGRAM CHANNEL:
   • Open Telegram and create a new channel
   • Make it private (recommended for security)
   • Give it a name like "Rust+ Notifications"

2. CREATE A BOT:
   • Search for @BotFather on Telegram
   • Send /newbot command
   • Follow instructions to name your bot (e.g., "MyRustWLEDBot")
   • Copy the Bot Token (looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
   • Paste it in the 'Bot Token' field above

3. ADD BOTS TO YOUR CHANNEL:
   • Go to your channel settings → Administrators → Add Administrator
   • Search and add your newly created bot (give it "Post Messages" permission)
   • Search and add @IFTTT bot (this sends Rust+ notifications)
   • Both bots must be channel admins!

4. GET YOUR CHANNEL ID:
   Method A - Using @userinfobot:
   • Forward any message from your channel to @userinfobot
   • It will show the channel ID (starts with -100, like: -1001234567890)
   
   Method B - Using @RawDataBot:
   • Forward any message from your channel to @RawDataBot
   • Look for "forward_from_chat":{"id":-100xxxxxxxxx}
   
   Method C - Using bot API:
   • Post a test message in your channel
   • Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   • Look for "chat":{"id":-100xxxxxxxxx}

5. CONFIGURE IFTTT (IMPORTANT!):
   • Go to IFTTT.com and set up Rust+ integration
   • In the "Then" action, choose "Telegram" → "Send message to channel"
   • Set the channel to your newly created channel
   • Make sure IFTTT sends messages when Rust+ events occur

6. TEST THE SETUP:
   • Paste your channel ID (starts with -100) in the 'Chat ID' field above
   • Click 'Save Settings' in the main window
   • Send a test message to your channel (or trigger a Rust+ event)
   • Your WLED should trigger!

🔧 TROUBLESHOOTING:
   • Channel IDs always start with -100 (e.g., -1001234567890)
   • Both your bot AND @IFTTT must be channel admins
   • Your bot needs "Post Messages" permission in the channel
   • Test by sending any message to the channel first
   • Check the console output for detailed error messages

⚠️ SECURITY TIPS:
   • Keep your channel private
   • Don't share your bot token publicly
   • Only add trusted bots as administrators
   
🎮 RUST+ INTEGRATION:
   • This app works with IFTTT's Rust+ integration
   • Set up IFTTT to send notifications to your Telegram channel
   • Events like "Player Online", "Smart Alarm", "Cargo Ship" will trigger WLED
   • Customize your WLED action above (colors, effects, presets)
"""
        text_edit.setPlainText(setup_text)
        layout.addWidget(text_edit)
        
        # Close button
        close_btn = QPushButton("❌ Close")
        close_btn.setFont(QFont("Arial", 13, QFont.Bold))
        close_btn.setStyleSheet("""
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #2196f3, stop: 1 #1976d2);
            color: white;
            padding: 12px 35px;
            border-radius: 8px;
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)


class RustWLEDApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_config()
        self.telegram_worker = None
        self.current_color = QColor(self.config["color"])
        self.last_log_message = ""
        self.duplicate_count = 0
        
        self.setWindowTitle("Rust+ WLED Trigger")
        self.setFixedSize(850, 950)
        
        # Set window icon if available
        try:
            self.setWindowIcon(QIcon("logo.ico"))
        except:
            pass  # Icon not found, continue without it
        
        # Apply modern dark theme stylesheet with animations
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2b2b2b, stop: 1 #1e1e1e);
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #404040;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: 14px;
                selection-background-color: #0078d4;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
                background-color: #424242;
            }
            QLineEdit:hover {
                border: 2px solid #555555;
                background-color: #404040;
            }
            QPushButton {
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                border: none;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.2);
            }
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                spacing: 12px;
                color: #ffffff;
                padding: 8px 15px;
                margin: 2px;
                background-color: rgba(255, 255, 255, 0.08);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                min-height: 20px;
            }
            QRadioButton:hover {
                background-color: rgba(255, 255, 255, 0.15);
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QRadioButton::indicator {
                width: 22px;
                height: 22px;
                border-radius: 11px;
            }
            QRadioButton::indicator:unchecked {
                border: 3px solid #666666;
                background-color: #3c3c3c;
            }
            QRadioButton::indicator:checked {
                border: 3px solid #0078d4;
                background-color: #0078d4;
                background: qradialgradient(cx: 0.5, cy: 0.5, radius: 0.5,
                                           fx: 0.5, fy: 0.5, stop: 0 #ffffff, stop: 0.3 #0078d4);
            }
            QRadioButton::indicator:unchecked:hover {
                border: 3px solid #888888;
                background-color: #484848;
            }
            QRadioButton::indicator:checked:hover {
                border: 3px solid #1e88e5;
                background-color: #1e88e5;
            }
            QSpinBox {
                padding: 12px;
                border: 2px solid #404040;
                border-radius: 8px;
                background-color: #3c3c3c;
                color: #ffffff;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: 2px solid #0078d4;
                background-color: #424242;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                background-color: #505050;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #606060;
            }
            QFrame {
                color: #666666;
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 8px;
                padding: 12px;
                font-family: 'Consolas', monospace;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #707070;
            }
        """)
        
        self.init_ui()
        self.setup_logging()
        self.start_telegram_worker()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🎮 Rust+ WLED Trigger")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ffffff;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #0078d4, stop: 1 #00bcf2);
            padding: 20px;
            border-radius: 12px;
            margin: 10px;
        """)
        main_layout.addWidget(title)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #404040;
                border-radius: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(255, 255, 255, 0.08),
                                           stop: 1 rgba(255, 255, 255, 0.03));
                margin-top: 10px;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #3c3c3c, stop: 1 #2a2a2a);
                color: #ffffff;
                padding: 15px 30px;
                margin: 2px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #0078d4, stop: 1 #005a9e);
                color: #ffffff;
                border: 2px solid #00bcf2;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #505050, stop: 1 #3a3a3a);
                border: 2px solid #666666;
            }
        """)
        
        # Create tabs
        self.create_main_tab()
        self.create_settings_tab()
        self.create_logs_tab()
        
        # Connect LED type change to update action visibility (after both tabs are created)
        self.led_type_group.buttonClicked.connect(self.update_action_visibility)
        
        main_layout.addWidget(self.tab_widget)
        
        # Status label (outside tabs)
        self.status_label = QLabel("Configure Telegram settings and save!")
        self.status_label.setFont(QFont("Arial", 13))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(80)
        self.status_label.setStyleSheet("""
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 rgba(33, 150, 243, 0.2),
                                       stop: 1 rgba(33, 150, 243, 0.1));
            color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            border: 2px solid rgba(33, 150, 243, 0.3);
        """)
        main_layout.addWidget(self.status_label)
        
        # Main action buttons (outside tabs)
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setFont(QFont("Arial", 14, QFont.Bold))
        save_btn.setToolTip("Save all configuration settings to file")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2196f3, stop: 1 #1976d2);
                color: white;
                padding: 18px 35px;
                border-radius: 12px;
                font-weight: bold;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #42a5f5, stop: 1 #1e88e5);
                border: 2px solid #64b5f6;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #1976d2, stop: 1 #1565c0);
            }
        """)
        save_btn.clicked.connect(self.save_config)
        
        test_btn = QPushButton("🧪 Test LEDs")
        test_btn.setFont(QFont("Arial", 14, QFont.Bold))
        test_btn.setToolTip("Test the current LED configuration")
        test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #4caf50, stop: 1 #388e3c);
                color: white;
                padding: 18px 35px;
                border-radius: 12px;
                font-weight: bold;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #66bb6a, stop: 1 #43a047);
                border: 2px solid #81c784;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #388e3c, stop: 1 #2e7d32);
            }
        """)
        test_btn.clicked.connect(self.test_wled)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(test_btn)
        main_layout.addLayout(buttons_layout)
        
        main_layout.addStretch()
        central_widget.setLayout(main_layout)
    
    def create_main_tab(self):
        """Create the main control tab"""
        main_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Action on Trigger
        action_title = QLabel("⚡ Action on Trigger")
        action_title.setFont(QFont("Arial", 16, QFont.Bold))
        action_title.setStyleSheet("""
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.1);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0px;
        """)
        layout.addWidget(action_title)
        
        # Radio buttons for actions
        self.action_group = QButtonGroup()
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(5)
        
        self.radio_on = QRadioButton("💡 Turn ON")
        self.radio_off = QRadioButton("🌙 Turn OFF")
        self.radio_color = QRadioButton("🎨 Set Color")
        self.radio_effect = QRadioButton("✨ Set Effect (WLED)")
        self.radio_preset = QRadioButton("🎭 Run Preset (WLED)")
        self.radio_scene = QRadioButton("🎪 Run Scene (Govee)")
        self.radio_brightness = QRadioButton("☀️ Set Brightness (Govee/Hue)")
        
        for i, radio in enumerate([self.radio_on, self.radio_off, self.radio_color, 
                                   self.radio_effect, self.radio_preset, self.radio_scene,
                                   self.radio_brightness]):
            radio.setFont(QFont("Arial", 14, QFont.Bold))
            radio.setStyleSheet("color: #ffffff; font-weight: bold;")
            self.action_group.addButton(radio, i)
            actions_layout.addWidget(radio)
        
        # Set current action
        action_map = {"on": 0, "off": 1, "color": 2, "effect": 3, "preset": 4, "scene": 5, "brightness": 6}
        current_action = self.config.get("action", "on")
        action_index = action_map.get(current_action, 0)
        self.action_group.button(action_index).setChecked(True)
        
        layout.addLayout(actions_layout)
        
        # Add spacing
        layout.addSpacing(20)
        
        # Color picker
        color_layout = QHBoxLayout()
        color_label = QLabel("🎨 Color:")
        color_label.setFont(QFont("Arial", 14, QFont.Bold))
        color_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.color_button = QPushButton("🎨 Pick Color")
        self.color_button.setStyleSheet("""
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #9c27b0, stop: 1 #7b1fa2);
            color: white;
            border-radius: 8px;
            font-weight: bold;
            padding: 10px 20px;
        """)
        self.color_button.clicked.connect(self.pick_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(120, 50)
        self.color_preview.setStyleSheet(f"""
            background-color: {self.current_color.name()};
            border: 3px solid #666666;
            border-radius: 8px;
        """)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Effect, Preset, Scene, and Brightness
        params_layout = QVBoxLayout()
        
        # First row: Effect and Preset (WLED)
        wled_row = QHBoxLayout()
        effect_label = QLabel("✨ Effect #:")
        effect_label.setFont(QFont("Arial", 14, QFont.Bold))
        effect_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.effect_spin = QSpinBox()
        self.effect_spin.setRange(0, 255)
        self.effect_spin.setValue(int(self.config.get("effect", 0)))
        self.effect_spin.setFont(QFont("Arial", 14))
        
        preset_label = QLabel("🎭 Preset #:")
        preset_label.setFont(QFont("Arial", 14, QFont.Bold))
        preset_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.preset_spin = QSpinBox()
        self.preset_spin.setRange(0, 255)
        self.preset_spin.setValue(int(self.config.get("preset", 0)))
        self.preset_spin.setFont(QFont("Arial", 14))
        
        wled_row.addWidget(effect_label)
        wled_row.addWidget(self.effect_spin)
        wled_row.addSpacing(30)
        wled_row.addWidget(preset_label)
        wled_row.addWidget(self.preset_spin)
        wled_row.addStretch()
        
        # Second row: Scene and Brightness (Govee/Hue)
        govee_row = QHBoxLayout()
        scene_label = QLabel("🎪 Scene #:")
        scene_label.setFont(QFont("Arial", 14, QFont.Bold))
        scene_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.scene_spin = QSpinBox()
        self.scene_spin.setRange(0, 50)  # Govee typically has limited scenes
        self.scene_spin.setValue(int(self.config.get("scene", 0)))
        self.scene_spin.setFont(QFont("Arial", 14))
        
        brightness_label = QLabel("☀️ Brightness:")
        brightness_label.setFont(QFont("Arial", 14, QFont.Bold))
        brightness_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(1, 100)
        self.brightness_spin.setValue(int(self.config.get("brightness", 100)))
        self.brightness_spin.setFont(QFont("Arial", 14))
        self.brightness_spin.setSuffix("%")
        
        govee_row.addWidget(scene_label)
        govee_row.addWidget(self.scene_spin)
        govee_row.addSpacing(30)
        govee_row.addWidget(brightness_label)
        govee_row.addWidget(self.brightness_spin)
        govee_row.addStretch()
        
        params_layout.addLayout(wled_row)
        params_layout.addLayout(govee_row)
        layout.addLayout(params_layout)
        
        layout.addStretch()
        main_tab.setLayout(layout)
        self.tab_widget.addTab(main_tab, "🎮 Control")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = QWidget()
        
        # Create scroll area for settings
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #606060;
                border-radius: 6px;
                min-height: 20px;
            }
        """)
        
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # LED Type Selection
        led_type_group = QGroupBox("🔌 LED Type Selection")
        led_type_group.setFont(QFont("Arial", 16, QFont.Bold))
        led_type_group.setStyleSheet("""
            QGroupBox {
                color: #ffffff;
                border: 2px solid #404040;
                border-radius: 12px;
                padding-top: 15px;
                margin-top: 10px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(255, 255, 255, 0.08),
                                           stop: 1 rgba(255, 255, 255, 0.03));
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)
        
        led_type_layout = QVBoxLayout()
        
        # LED Type radio buttons
        self.led_type_group = QButtonGroup()
        
        self.radio_wled = QRadioButton("💻 WLED (Local Network LED Controller)")
        self.radio_govee = QRadioButton("📱 Govee (WiFi Smart LEDs)")  
        self.radio_hue = QRadioButton("🌈 Philips Hue (Coming Soon)")
        
        self.radio_hue.setEnabled(False)  # Disable until implemented
        self.radio_hue.setStyleSheet("color: #666666;")  # Gray out disabled option
        
        for i, radio in enumerate([self.radio_wled, self.radio_govee, self.radio_hue]):
            radio.setFont(QFont("Arial", 14, QFont.Bold))
            self.led_type_group.addButton(radio, i)
            led_type_layout.addWidget(radio)
        
        # Set current LED type
        led_type_map = {"wled": 0, "govee": 1, "philips_hue": 2}
        current_type = led_type_map.get(self.config.get("led_type", "wled"), 0)
        self.led_type_group.button(current_type).setChecked(True)
        
        led_type_group.setLayout(led_type_layout)
        layout.addWidget(led_type_group)
        
        # WLED Settings Group
        self.wled_group = QGroupBox("💻 WLED Settings")
        self.wled_group.setFont(QFont("Arial", 16, QFont.Bold))
        self.wled_group.setStyleSheet(led_type_group.styleSheet())
        
        wled_layout = QVBoxLayout()
        
        # WLED IP
        wled_ip_layout = QHBoxLayout()
        wled_ip_label = QLabel("💻 WLED IP:")
        wled_ip_label.setFont(QFont("Arial", 14, QFont.Bold))
        wled_ip_label.setMinimumWidth(130)
        wled_ip_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.ip_entry = QLineEdit(self.config.get("wled_ip", "192.168.1.50"))
        self.ip_entry.setFont(QFont("Arial", 13))
        self.ip_entry.setPlaceholderText("192.168.1.100")
        self.ip_entry.setToolTip("Enter the IP address of your WLED device")
        wled_ip_layout.addWidget(wled_ip_label)
        wled_ip_layout.addWidget(self.ip_entry)
        
        wled_layout.addLayout(wled_ip_layout)
        self.wled_group.setLayout(wled_layout)
        layout.addWidget(self.wled_group)
        
        # Govee Settings Group
        self.govee_group = QGroupBox("📱 Govee Settings")
        self.govee_group.setFont(QFont("Arial", 16, QFont.Bold))
        self.govee_group.setStyleSheet(led_type_group.styleSheet())
        
        govee_layout = QVBoxLayout()
        
        # Govee API Key
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("🔑 API Key:")
        api_key_label.setFont(QFont("Arial", 14, QFont.Bold))
        api_key_label.setMinimumWidth(130)
        api_key_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.govee_api_key_entry = QLineEdit(self.config.get("govee_api_key", ""))
        self.govee_api_key_entry.setFont(QFont("Arial", 13))
        self.govee_api_key_entry.setEchoMode(QLineEdit.Password)
        self.govee_api_key_entry.setPlaceholderText("Your Govee API Key")
        self.govee_api_key_entry.setToolTip("Get your API key from Govee developer portal")
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.govee_api_key_entry)
        
        # Govee Device ID
        device_id_layout = QHBoxLayout()
        device_id_label = QLabel("📱 Device ID:")
        device_id_label.setFont(QFont("Arial", 14, QFont.Bold))
        device_id_label.setMinimumWidth(130)
        device_id_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.govee_device_id_entry = QLineEdit(self.config.get("govee_device_id", ""))
        self.govee_device_id_entry.setFont(QFont("Arial", 13))
        self.govee_device_id_entry.setPlaceholderText("AB:CD:EF:12:34:56:78:90")
        self.govee_device_id_entry.setToolTip("Device MAC address from Govee API")
        device_id_layout.addWidget(device_id_label)
        device_id_layout.addWidget(self.govee_device_id_entry)
        
        # Govee Model
        model_layout = QHBoxLayout()
        model_label = QLabel("🏷️ Model:")
        model_label.setFont(QFont("Arial", 14, QFont.Bold))
        model_label.setMinimumWidth(130)
        model_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.govee_model_entry = QLineEdit(self.config.get("govee_model", ""))
        self.govee_model_entry.setFont(QFont("Arial", 13))
        self.govee_model_entry.setPlaceholderText("H6163")
        self.govee_model_entry.setToolTip("Device model from Govee API")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.govee_model_entry)
        
        # Get Devices button
        get_devices_btn = QPushButton("📋 Get My Devices")
        get_devices_btn.setFont(QFont("Arial", 12, QFont.Bold))
        get_devices_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #9c27b0, stop: 1 #7b1fa2);
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 10px 20px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ba68c8, stop: 1 #9c27b0);
                border: 2px solid #ce93d8;
            }
        """)
        get_devices_btn.clicked.connect(self.get_govee_devices)
        
        govee_layout.addLayout(api_key_layout)
        govee_layout.addLayout(device_id_layout)
        govee_layout.addLayout(model_layout)
        govee_layout.addWidget(get_devices_btn, alignment=Qt.AlignCenter)
        
        self.govee_group.setLayout(govee_layout)
        layout.addWidget(self.govee_group)
        
        # Philips Hue Settings Group (placeholder)
        self.hue_group = QGroupBox("🌈 Philips Hue Settings (Coming Soon)")
        self.hue_group.setFont(QFont("Arial", 16, QFont.Bold))
        self.hue_group.setStyleSheet(led_type_group.styleSheet())
        self.hue_group.setEnabled(False)
        
        hue_layout = QVBoxLayout()
        hue_placeholder = QLabel("🚧 Philips Hue integration will be added in a future update")
        hue_placeholder.setFont(QFont("Arial", 12))
        hue_placeholder.setStyleSheet("color: #666666; text-align: center; padding: 20px;")
        hue_placeholder.setAlignment(Qt.AlignCenter)
        hue_layout.addWidget(hue_placeholder)
        
        self.hue_group.setLayout(hue_layout)
        layout.addWidget(self.hue_group)
        
        # Telegram Settings
        telegram_group = QGroupBox("💬 Telegram Settings")
        telegram_group.setFont(QFont("Arial", 16, QFont.Bold))
        telegram_group.setStyleSheet(led_type_group.styleSheet())
        
        telegram_layout = QVBoxLayout()
        
        # Bot Token
        token_layout = QHBoxLayout()
        token_label = QLabel("🤖 Bot Token:")
        token_label.setFont(QFont("Arial", 14, QFont.Bold))
        token_label.setMinimumWidth(130)
        token_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.bot_token_entry = QLineEdit(self.config.get("telegram_bot_token", ""))
        self.bot_token_entry.setFont(QFont("Arial", 13))
        self.bot_token_entry.setEchoMode(QLineEdit.Password)
        self.bot_token_entry.setPlaceholderText("123456789:ABCdefGHIjklMNOpqr")
        self.bot_token_entry.setToolTip("Bot token from @BotFather (123456789:ABC...)")
        setup_btn = QPushButton("📋 Setup Help")
        setup_btn.setToolTip("Show detailed setup instructions")
        setup_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ff9800, stop: 1 #f57c00);
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 8px 16px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ffb74d, stop: 1 #ff9800);
                border: 2px solid #ffcc02;
            }
        """)
        setup_btn.clicked.connect(self.show_setup_dialog)
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.bot_token_entry)
        token_layout.addWidget(setup_btn)
        
        # Chat ID
        chat_layout = QHBoxLayout()
        chat_label = QLabel("💬 Chat ID:")
        chat_label.setFont(QFont("Arial", 14, QFont.Bold))
        chat_label.setMinimumWidth(130)
        chat_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.chat_id_entry = QLineEdit(self.config.get("telegram_chat_id", ""))
        self.chat_id_entry.setFont(QFont("Arial", 13))
        self.chat_id_entry.setPlaceholderText("-1001234567890")
        self.chat_id_entry.setToolTip("Channel ID (starts with -100) or personal chat ID")
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.chat_id_entry)
        
        # Polling Rate
        polling_layout = QHBoxLayout()
        polling_label = QLabel("🔄 Polling Rate:")
        polling_label.setFont(QFont("Arial", 14, QFont.Bold))
        polling_label.setMinimumWidth(130)
        polling_label.setStyleSheet("color: #ffffff; padding: 5px;")
        self.polling_spin = QSpinBox()
        self.polling_spin.setRange(1, 30)
        self.polling_spin.setValue(int(self.config.get("polling_rate", 2)))
        self.polling_spin.setFont(QFont("Arial", 14))
        self.polling_spin.setSuffix(" sec")
        self.polling_spin.setToolTip("How often to check for new messages (1-30 seconds)")
        polling_layout.addWidget(polling_label)
        polling_layout.addWidget(self.polling_spin)
        polling_layout.addStretch()
        
        telegram_layout.addLayout(token_layout)
        telegram_layout.addLayout(chat_layout)
        telegram_layout.addLayout(polling_layout)
        
        telegram_group.setLayout(telegram_layout)
        layout.addWidget(telegram_group)
        
        # Connect LED type change to show/hide settings
        self.led_type_group.buttonClicked.connect(self.on_led_type_changed)
        self.on_led_type_changed()  # Set initial visibility
        
        # Update action visibility after UI is fully rendered
        QTimer.singleShot(100, self.update_action_visibility)
        
        layout.addStretch()
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        settings_tab.setLayout(main_layout)
        
        self.tab_widget.addTab(settings_tab, "⚙️ Settings")
    
    def create_logs_tab(self):
        """Create the logs tab"""
        logs_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("📜 Application Logs")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Logs text area
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 2px solid #444444;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                padding: 10px;
            }
        """)
        layout.addWidget(self.logs_text)
        
        # Clear logs button
        clear_btn = QPushButton("🗑️ Clear Logs")
        clear_btn.setFixedHeight(40)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ff6b6b, stop: 1 #e74c3c);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: bold;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ff8a80, stop: 1 #ff5252);
                border: 2px solid #ff9999;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #c62828, stop: 1 #b71c1c);
            }
        """)
        clear_btn.clicked.connect(self.clear_logs)
        layout.addWidget(clear_btn)
        
        logs_tab.setLayout(layout)
        self.tab_widget.addTab(logs_tab, "📜 Logs")
    
    def setup_logging(self):
        """Setup logging to redirect stdout to the logs tab"""
        self.log_stream = EmittingStream()
        self.log_stream.textWritten.connect(self.append_log)
        
        # Redirect stdout to our custom stream
        sys.stdout = self.log_stream
        
        # Initial log message
        self.append_log("Application started - Logging initialized")
    
    def append_log(self, text):
        """Append text to the logs tab with duplicate handling"""
        if hasattr(self, 'logs_text'):
            # Handle duplicate messages
            if text == self.last_log_message:
                self.duplicate_count += 1
                # Move to end and select the entire last line
                cursor = self.logs_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
                
                # Replace the entire line with updated count
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                formatted_text = f"[{timestamp}] {text} (x{self.duplicate_count + 1})"
                cursor.removeSelectedText()
                cursor.insertText(formatted_text)
                
                self.logs_text.setTextCursor(cursor)
                self.logs_text.ensureCursorVisible()
                return
            
            # Reset duplicate tracking for new message
            self.last_log_message = text
            self.duplicate_count = 0
            
            cursor = self.logs_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            
            # Add timestamp
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            formatted_text = f"[{timestamp}] {text}"
            
            cursor.insertText(formatted_text + "\n")
            self.logs_text.setTextCursor(cursor)
            
            # Auto-scroll to bottom
            self.logs_text.ensureCursorVisible()
    
    def clear_logs(self):
        """Clear the logs text area"""
        if hasattr(self, 'logs_text'):
            self.logs_text.clear()
            # Reset duplicate tracking
            self.last_log_message = ""
            self.duplicate_count = 0
            self.append_log("Logs cleared")
    
    def on_led_type_changed(self):
        """Handle LED type radio button changes"""
        selected_id = self.led_type_group.checkedId()
        
        # Show/hide appropriate settings groups
        self.wled_group.setVisible(selected_id == 0)  # WLED
        self.govee_group.setVisible(selected_id == 1)  # Govee
        self.hue_group.setVisible(selected_id == 2)    # Philips Hue
        
        # Update action visibility in control tab
        self.update_action_visibility()
    
    def update_action_visibility(self):
        """Update visibility of action radio buttons based on selected LED type"""
        if not hasattr(self, 'led_type_group'):
            return  # Not initialized yet
        
        selected_id = self.led_type_group.checkedId()
        
        # All LED types support these basic actions
        self.radio_on.setVisible(True)
        self.radio_off.setVisible(True)
        self.radio_color.setVisible(True)
        
        # WLED-specific actions
        if selected_id == 0:  # WLED
            self.radio_effect.setVisible(True)
            self.radio_preset.setVisible(True)
            self.radio_scene.setVisible(False)
            self.radio_brightness.setVisible(False)
            self.radio_effect.setText("✨ Set Effect (WLED)")
            self.radio_preset.setText("🎭 Run Preset (WLED)")
        
        # Govee-specific actions
        elif selected_id == 1:  # Govee
            self.radio_effect.setVisible(False)
            self.radio_preset.setVisible(False)
            self.radio_scene.setVisible(True)
            self.radio_brightness.setVisible(True)
        
        # Philips Hue actions (future)
        elif selected_id == 2:  # Philips Hue
            self.radio_effect.setVisible(False)
            self.radio_preset.setVisible(False)
            self.radio_scene.setVisible(False)
            self.radio_brightness.setVisible(True)
        
        # Ensure a valid action is selected based on LED type
        current_button = self.action_group.checkedButton()
        if current_button:
            # Check if the action is compatible with the current LED type
            should_reset = False
            
            if selected_id == 0:  # WLED
                # WLED doesn't support scene
                if current_button in [self.radio_scene]:
                    should_reset = True
            elif selected_id == 1:  # Govee
                # Govee doesn't support WLED-specific effect/preset
                if current_button in [self.radio_effect, self.radio_preset]:
                    should_reset = True
            elif selected_id == 2:  # Philips Hue
                # Hue doesn't support WLED or Govee specific actions
                if current_button in [self.radio_effect, self.radio_preset, self.radio_scene]:
                    should_reset = True
            
            if should_reset:
                self.radio_on.setChecked(True)
        else:
            # If no button is selected at all, default to "on"
            self.radio_on.setChecked(True)
    
    
    def get_govee_devices(self):
        """Get and display available Govee devices"""
        api_key = self.govee_api_key_entry.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Missing API Key", 
                              "Please enter your Govee API key first.")
            return
        
        try:
            # Create a temporary Govee controller to get devices
            from led_controllers import GoveeController
            temp_controller = GoveeController(api_key, "", "")
            devices = temp_controller.get_devices()
            
            if not devices:
                QMessageBox.information(self, "No Devices", 
                                      "No Govee devices found. Make sure your API key is correct.")
                return
            
            # Create a dialog to show devices
            dialog = QDialog(self)
            dialog.setWindowTitle("Available Govee Devices")
            dialog.setFixedSize(600, 400)
            
            layout = QVBoxLayout()
            
            info_label = QLabel("Select a device to auto-fill the settings:")
            info_label.setFont(QFont("Arial", 12, QFont.Bold))
            layout.addWidget(info_label)
            
            # Create list of devices
            device_list = QTextEdit()
            device_list.setReadOnly(True)
            device_list.setFont(QFont("Consolas", 10))
            
            device_text = ""
            for i, device in enumerate(devices):
                device_text += f"Device {i+1}:\n"
                device_text += f"  Name: {device.get('deviceName', 'Unknown')}\n"
                device_text += f"  Device ID: {device.get('device', 'N/A')}\n"
                device_text += f"  Model: {device.get('model', 'N/A')}\n"
                device_text += f"  Controllable: {'Yes' if device.get('controllable') else 'No'}\n"
                device_text += f"  Retrievable: {'Yes' if device.get('retrievable') else 'No'}\n"
                device_text += "  Capabilities: " + ", ".join(device.get('supportCmds', [])) + "\n"
                device_text += "\n"
            
            device_list.setPlainText(device_text)
            layout.addWidget(device_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            for i, device in enumerate(devices):
                if device.get('controllable'):  # Only show controllable devices
                    btn = QPushButton(f"Use Device {i+1}")
                    btn.clicked.connect(lambda checked, dev=device: self.select_govee_device(dev, dialog))
                    button_layout.addWidget(btn)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get Govee devices: {str(e)}")
    
    def select_govee_device(self, device, dialog):
        """Select and populate a Govee device"""
        self.govee_device_id_entry.setText(device.get('device', ''))
        self.govee_model_entry.setText(device.get('model', ''))
        dialog.accept()
        
        # Show success message
        QMessageBox.information(self, "Device Selected", 
                              f"Selected: {device.get('deviceName', 'Unknown Device')}\n"
                              f"Model: {device.get('model', 'N/A')}")
    
    
    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                self.config = json.load(f)
            print(f"[INFO] Loaded config from {CONFIG_FILE}")
            
            # Migrate old config format to new format
            if "led_type" not in self.config:
                print("[INFO] Migrating old config format...")
                self.config["led_type"] = "wled"  # Default to WLED for existing users
                
                # Add new fields with defaults
                new_fields = {
                    "scene": "0",
                    "brightness": "100",
                    "govee_api_key": "",
                    "govee_device_id": "",
                    "govee_model": "",
                    "hue_bridge_ip": "",
                    "hue_username": ""
                }
                
                for field, default_value in new_fields.items():
                    if field not in self.config:
                        self.config[field] = default_value
                
                # Save the migrated config
                with open(CONFIG_FILE, "w") as f:
                    json.dump(self.config, f, indent=4)
                print("[INFO] Config migration completed!")
                
        except:
            print(f"[INFO] Config file not found. Creating default config...")
            self.config = {
                "led_type": "wled",  # "wled", "govee", or "philips_hue"
                "action": "on",
                "color": "#ffffff",
                "effect": "0",
                "preset": "0",
                "scene": "0",  # For Govee scenes
                "brightness": "100",  # For Govee/Hue
                # WLED settings
                "wled_ip": "192.168.1.50",
                # Govee settings
                "govee_api_key": "",
                "govee_device_id": "",
                "govee_model": "",
                # Philips Hue settings (for future)
                "hue_bridge_ip": "",
                "hue_username": "",
                # Telegram settings
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "last_message_id": 0,
                "polling_rate": 2
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"[INFO] Created default config file: {CONFIG_FILE}")
    
    def save_config(self):
        # Store old telegram settings to check if they changed
        old_bot_token = self.config.get("telegram_bot_token", "")
        old_chat_id = self.config.get("telegram_chat_id", "")
        
        # Get selected LED type
        led_type_map = {0: "wled", 1: "govee", 2: "philips_hue"}
        self.config["led_type"] = led_type_map.get(self.led_type_group.checkedId(), "wled")
        
        # Save LED-specific settings
        self.config["wled_ip"] = self.ip_entry.text()
        self.config["govee_api_key"] = self.govee_api_key_entry.text()
        self.config["govee_device_id"] = self.govee_device_id_entry.text()
        self.config["govee_model"] = self.govee_model_entry.text()
        
        # Save Telegram settings
        self.config["telegram_bot_token"] = self.bot_token_entry.text()
        self.config["telegram_chat_id"] = self.chat_id_entry.text()
        self.config["polling_rate"] = self.polling_spin.value()
        
        # Get selected action
        action_map = {0: "on", 1: "off", 2: "color", 3: "effect", 4: "preset", 5: "scene", 6: "brightness"}
        self.config["action"] = action_map.get(self.action_group.checkedId(), "on")
        
        # Save action parameters
        self.config["color"] = self.current_color.name()
        self.config["effect"] = str(self.effect_spin.value())
        self.config["preset"] = str(self.preset_spin.value())
        self.config["scene"] = str(self.scene_spin.value())
        self.config["brightness"] = str(self.brightness_spin.value())
        
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)
        
        led_type = self.config.get("led_type", "wled")
        print(f"[INFO] Settings saved: LED Type={led_type}, Action={self.config['action']}")
        self.update_status("✓ Settings Saved Successfully!", "green")
        
        # Visual feedback - briefly highlight save button
        save_button = self.sender()
        save_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #4caf50, stop: 1 #388e3c);
                color: white;
                padding: 18px 35px;
                border-radius: 12px;
                font-weight: bold;
                border: 2px solid #81c784;
            }
        """)
        
        # Reset button style after 1 second
        QTimer.singleShot(1000, lambda: save_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2196f3, stop: 1 #1976d2);
                color: white;
                padding: 18px 35px;
                border-radius: 12px;
                font-weight: bold;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #42a5f5, stop: 1 #1e88e5);
                border: 2px solid #64b5f6;
            }
        """))
        
        # Only restart telegram worker if telegram settings changed
        new_bot_token = self.config.get("telegram_bot_token", "")
        new_chat_id = self.config.get("telegram_chat_id", "")
        
        if old_bot_token != new_bot_token or old_chat_id != new_chat_id:
            print("[INFO] Telegram settings changed, restarting worker...")
            self.restart_telegram_worker()
    
    def pick_color(self):
        color = QColorDialog.getColor(self.current_color, self, "Pick a Color")
        if color.isValid():
            self.current_color = color
            self.color_preview.setStyleSheet(f"""
                background-color: {color.name()};
                border: 3px solid #666666;
                border-radius: 8px;
            """)
    
    def show_setup_dialog(self):
        dialog = SetupDialog(self)
        dialog.exec()
    
    def test_wled(self):
        print("[INFO] Testing LED connection...")
        
        # Visual feedback - show testing state
        sender = self.sender()
        original_text = sender.text()
        sender.setText("🔄 Testing...")
        sender.setEnabled(False)
        
        # Update config from UI without saving to file or restarting telegram
        led_type_map = {0: "wled", 1: "govee", 2: "philips_hue"}
        self.config["led_type"] = led_type_map.get(self.led_type_group.checkedId(), "wled")
        self.config["wled_ip"] = self.ip_entry.text()
        self.config["govee_api_key"] = self.govee_api_key_entry.text()
        self.config["govee_device_id"] = self.govee_device_id_entry.text()
        self.config["govee_model"] = self.govee_model_entry.text()
        self.config["polling_rate"] = self.polling_spin.value()
        action_map = {0: "on", 1: "off", 2: "color", 3: "effect", 4: "preset", 5: "scene", 6: "brightness"}
        self.config["action"] = action_map.get(self.action_group.checkedId(), "on")
        self.config["color"] = self.current_color.name()
        self.config["effect"] = str(self.effect_spin.value())
        self.config["preset"] = str(self.preset_spin.value())
        self.config["scene"] = str(self.scene_spin.value())
        self.config["brightness"] = str(self.brightness_spin.value())
        
        self.trigger_led()
        
        # Reset button after 2 seconds
        QTimer.singleShot(2000, lambda: [
            sender.setText(original_text),
            sender.setEnabled(True)
        ])
    
    def trigger_led(self):
        """Trigger LED action using the appropriate controller"""
        led_type = self.config.get("led_type", "wled")
        action = self.config.get("action", "on")
        
        print(f"[LED] Triggering {led_type.upper()} action: {action}")
        
        try:
            # Create the appropriate LED controller
            controller = create_led_controller(led_type, self.config)
            if not controller:
                self.update_status("❌ Error: LED controller not configured properly", "red")
                return
            
            # Test connection first
            if not controller.test_connection():
                self.update_status("❌ Error: Cannot connect to LED device", "red")
                return
            
            # Execute the action
            success = False
            if action == "on":
                success = controller.turn_on()
                print(f"[LED] Turn ON result: {success}")
            elif action == "off":
                success = controller.turn_off()
                print(f"[LED] Turn OFF result: {success}")
            elif action == "color":
                color = self.config.get("color", "#ffffff")
                success = controller.set_color(color)
                print(f"[LED] Set color {color} result: {success}")
            elif action == "brightness" and hasattr(controller, 'set_brightness'):
                brightness = int(self.config.get("brightness", 100))
                success = controller.set_brightness(brightness)
                print(f"[LED] Set brightness {brightness}% result: {success}")
            elif action == "effect" and hasattr(controller, 'set_effect'):
                effect = int(self.config.get("effect", 0))
                success = controller.set_effect(effect)
                print(f"[LED] Set effect #{effect} result: {success}")
            elif action == "preset" and hasattr(controller, 'set_preset'):
                preset = int(self.config.get("preset", 0))
                success = controller.set_preset(preset)
                print(f"[LED] Set preset #{preset} result: {success}")
            elif action == "scene" and hasattr(controller, 'set_scene'):
                scene = int(self.config.get("scene", 0))
                success = controller.set_scene(scene)
                print(f"[LED] Set scene #{scene} result: {success}")
            else:
                print(f"[LED] Action '{action}' not supported for {led_type}")
                self.update_status(f"❌ Error: Action '{action}' not supported for {led_type.upper()}", "red")
                return
            
            if success:
                print(f"[LED] ✓ {led_type.upper()} action successful!")
                self.update_status(f"✓ {led_type.upper()} {action.title()} Successful!", "green")
            else:
                print(f"[LED] ❌ {led_type.upper()} action failed!")
                self.update_status(f"❌ {led_type.upper()} {action.title()} Failed!", "red")
        
        except Exception as e:
            print(f"[ERROR] LED control failed: {str(e)}")
            self.update_status(f"❌ Error: {str(e)[:50]}", "red")
    
    def update_status(self, message, color):
        color_map = {
            "green": ("""
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(76, 175, 80, 0.3),
                                           stop: 1 rgba(76, 175, 80, 0.1));
                color: #a5d6a7;
                border: 2px solid rgba(76, 175, 80, 0.5);
            """),
            "red": ("""
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(244, 67, 54, 0.3),
                                           stop: 1 rgba(244, 67, 54, 0.1));
                color: #ef9a9a;
                border: 2px solid rgba(244, 67, 54, 0.5);
            """),
            "orange": ("""
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(255, 152, 0, 0.3),
                                           stop: 1 rgba(255, 152, 0, 0.1));
                color: #ffcc02;
                border: 2px solid rgba(255, 152, 0, 0.5);
            """),
            "blue": ("""
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 rgba(33, 150, 243, 0.3),
                                           stop: 1 rgba(33, 150, 243, 0.1));
                color: #90caf9;
                border: 2px solid rgba(33, 150, 243, 0.5);
            """)
        }
        style = color_map.get(color, color_map["blue"])
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"{style} padding: 20px; border-radius: 12px;")
    
    def start_telegram_worker(self):
        self.telegram_worker = TelegramWorker(self.config)
        self.telegram_worker.status_update.connect(self.update_status)
        self.telegram_worker.log_message.connect(self.append_log)
        self.telegram_worker.trigger_callback = self.trigger_led
        self.telegram_worker.start()
    
    def restart_telegram_worker(self):
        if self.telegram_worker and self.telegram_worker.isRunning():
            self.telegram_worker.stop()
            self.telegram_worker.wait()
        self.start_telegram_worker()
    
    def closeEvent(self, event):
        if self.telegram_worker and self.telegram_worker.isRunning():
            self.telegram_worker.stop()
            self.telegram_worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RustWLEDApp()
    window.show()
    sys.exit(app.exec())
