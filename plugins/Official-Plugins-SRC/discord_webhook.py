"""
Discord Webhook Plugin - Send raid alerts to Discord

A simple single-file plugin that posts messages to Discord via webhooks.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFrame, QTextEdit, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from plugin_base import PluginBase
import requests
import json
from datetime import datetime


class Plugin(PluginBase):
    """Discord Webhook Plugin"""
    
    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.widget = None
    
    def get_name(self):
        return "Discord Webhook"
    
    def get_icon(self):
        return "💬"
    
    def get_description(self):
        return "Send raid alerts to Discord channels via webhooks"

    def get_version(self):
        return "1.0.0"

    def get_author(self):
        return "RustPlusRaidAlarms Team"

    def get_homepage(self):
        return "https://github.com/eman225511/RustPlusRaidAlarms"
    
    def get_widget(self):
        if self.widget is None:
            self.widget = self._build_ui()
        return self.widget
    
    def _build_ui(self):
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
        
        title = QLabel("💬 Discord Webhook")
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
        
        subtitle = QLabel("Post raid alerts to Discord channels")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header)
        
        # Webhook URL Group
        webhook_group = QGroupBox("Webhook Configuration")
        webhook_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        webhook_group.setStyleSheet(self.get_groupbox_style())
        webhook_layout = QVBoxLayout(webhook_group)
        
        # Instructions
        instructions = QLabel(
            "📝 <b>How to get a webhook URL:</b><br>"
            "1. Open Discord → Server Settings → Integrations<br>"
            "2. Click 'Webhooks' → 'New Webhook'<br>"
            "3. Choose a channel and copy the webhook URL"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #b8b8b8; padding: 10px; background-color: #2d2d30; border-radius: 8px;")
        webhook_layout.addWidget(instructions)
        
        # Webhook URL input
        url_row = QHBoxLayout()
        url_label = QLabel("Webhook URL:")
        url_label.setMinimumWidth(120)
        url_label.setFont(QFont("Segoe UI", 10))
        url_row.addWidget(url_label)
        
        self.webhook_url_input = QLineEdit(self.config.get("discord_webhook_url", ""))
        self.webhook_url_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.webhook_url_input.setMinimumHeight(32)
        self.webhook_url_input.textChanged.connect(self.save_config_data)
        url_row.addWidget(self.webhook_url_input)
        
        webhook_layout.addLayout(url_row)
        
        # Bot name
        name_row = QHBoxLayout()
        name_label = QLabel("Bot Name:")
        name_label.setMinimumWidth(120)
        name_label.setFont(QFont("Segoe UI", 10))
        name_row.addWidget(name_label)
        
        self.bot_name_input = QLineEdit(self.config.get("discord_bot_name", "Raid Alert Bot"))
        self.bot_name_input.setPlaceholderText("Raid Alert Bot")
        self.bot_name_input.setMinimumHeight(32)
        self.bot_name_input.textChanged.connect(self.save_config_data)
        name_row.addWidget(self.bot_name_input)
        
        webhook_layout.addLayout(name_row)
        
        layout.addWidget(webhook_group)
        
        # Message Configuration
        message_group = QGroupBox("Message Settings")
        message_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        message_group.setStyleSheet(self.get_groupbox_style())
        message_layout = QVBoxLayout(message_group)
        
        # Mention everyone checkbox
        self.mention_everyone = QCheckBox("@everyone on raid alerts")
        self.mention_everyone.setFont(QFont("Segoe UI", 10))
        self.mention_everyone.setChecked(self.config.get("discord_mention_everyone", False))
        self.mention_everyone.stateChanged.connect(self.save_config_data)
        message_layout.addWidget(self.mention_everyone)
        
        # Custom role mention
        role_row = QHBoxLayout()
        role_label = QLabel("Role to mention:")
        role_label.setMinimumWidth(120)
        role_label.setFont(QFont("Segoe UI", 10))
        role_row.addWidget(role_label)
        
        self.role_id_input = QLineEdit(self.config.get("discord_role_id", ""))
        self.role_id_input.setPlaceholderText("Role ID (optional, e.g., 123456789012345678)")
        self.role_id_input.setMinimumHeight(32)
        self.role_id_input.textChanged.connect(self.save_config_data)
        role_row.addWidget(self.role_id_input)
        
        message_layout.addLayout(role_row)
        
        # Custom message
        msg_label = QLabel("Message template:")
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setStyleSheet("color: #b8b8b8; margin-top: 10px;")
        message_layout.addWidget(msg_label)
        
        self.message_template = QTextEdit()
        self.message_template.setPlaceholderText("🚨 **RAID ALERT!** 🚨\n\nYou are being raided in Rust!\n{telegram_message}")
        self.message_template.setMinimumHeight(100)
        self.message_template.setMaximumHeight(150)
        
        default_template = self.config.get(
            "discord_message_template",
            "🚨 **RAID ALERT!** 🚨\n\nYou are being raided in Rust!\n\n{telegram_message}"
        )
        self.message_template.setPlainText(default_template)
        self.message_template.textChanged.connect(self.save_config_data)
        message_layout.addWidget(self.message_template)
        
        template_hint = QLabel("💡 Use {telegram_message} to include the original Telegram message")
        template_hint.setFont(QFont("Segoe UI", 9))
        template_hint.setStyleSheet("color: #888888;")
        message_layout.addWidget(template_hint)
        
        layout.addWidget(message_group)
        
        # Test Button
        test_frame = QFrame()
        test_frame.setObjectName("card")
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(16, 16, 16, 16)
        
        test_btn = QPushButton("💬 Send Test Message")
        test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        test_btn.setMinimumHeight(48)
        test_btn.setStyleSheet(self.get_button_style("#5865F2"))  # Discord blurple color
        test_btn.clicked.connect(self.test_webhook)
        test_layout.addWidget(test_btn)
        
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px;")
        test_layout.addWidget(self.status_label)
        
        layout.addWidget(test_frame)
        layout.addStretch()
        
        return widget
    
    def save_config_data(self):
        """Save all settings to config"""
        self.config["discord_webhook_url"] = self.webhook_url_input.text().strip()
        self.config["discord_bot_name"] = self.bot_name_input.text().strip()
        self.config["discord_mention_everyone"] = self.mention_everyone.isChecked()
        self.config["discord_role_id"] = self.role_id_input.text().strip()
        self.config["discord_message_template"] = self.message_template.toPlainText().strip()
    
    def send_discord_message(self, telegram_message=""):
        """Send message to Discord webhook"""
        webhook_url = self.config.get("discord_webhook_url", "").strip()
        
        if not webhook_url:
            self.status_label.setText("❌ Webhook URL not configured")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return False
        
        # Build message content
        message_template = self.config.get(
            "discord_message_template",
            "🚨 **RAID ALERT!** 🚨\n\nYou are being raided in Rust!\n\n{telegram_message}"
        )
        
        content = message_template.replace("{telegram_message}", telegram_message)
        
        # Add mentions
        if self.config.get("discord_mention_everyone", False):
            content = "@everyone " + content
        
        role_id = self.config.get("discord_role_id", "").strip()
        if role_id:
            content = f"<@&{role_id}> " + content
        
        # Build webhook payload
        payload = {
            "content": content,
            "username": self.config.get("discord_bot_name", "Raid Alert Bot")
        }
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 204:
                print(f"[Discord] Message sent successfully")
                self.status_label.setText("✓ Message sent to Discord!")
                self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
                return True
            else:
                error_msg = f"HTTP {response.status_code}"
                print(f"[Discord] Error: {error_msg}")
                self.status_label.setText(f"❌ Error: {error_msg}")
                self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
                return False
                
        except requests.exceptions.Timeout:
            print("[Discord] Request timeout")
            self.status_label.setText("❌ Request timeout")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return False
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"[Discord] Error: {error_msg}")
            self.status_label.setText(f"❌ Error: {error_msg}")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return False
    
    def test_webhook(self):
        """Send a test message"""
        if not self.config.get("discord_webhook_url", "").strip():
            QMessageBox.warning(
                None,
                "Missing Configuration",
                "Please enter a webhook URL first."
            )
            return
        
        self.status_label.setText("📤 Sending test message...")
        self.status_label.setStyleSheet("color: #ffa500; padding: 10px;")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        test_message = f"Test alert sent at {timestamp}"
        self.send_discord_message(test_message)
    
    def on_telegram_message(self, message: str):
        """Called when Telegram message received - send to Discord"""
        print("[Discord] Raid alert received, sending to Discord...")
        self.send_discord_message(message)
    
    def show_help(self):
        """Show setup guide"""
        help_text = """<b>Discord Webhook Setup Guide</b><br><br>

<b>Step 1: Create Webhook in Discord</b><br>
1. Open Discord and go to your server<br>
2. Right-click the channel you want alerts in<br>
3. Click "Edit Channel" → "Integrations"<br>
4. Click "Webhooks" → "New Webhook"<br>
5. Give it a name (e.g., "Raid Alert Bot")<br>
6. Click "Copy Webhook URL"<br><br>

<b>Step 2: Configure Plugin</b><br>
1. Paste webhook URL in the field above<br>
2. Customize bot name (optional)<br>
3. Edit message template<br>
4. Click "Send Test Message" to verify<br><br>

<b>Message Template:</b><br>
• Use <b>{telegram_message}</b> to include the raid alert<br>
• Discord supports markdown formatting:<br>
&nbsp;&nbsp;• <b>**bold text**</b><br>
&nbsp;&nbsp;• <i>*italic text*</i><br>
&nbsp;&nbsp;• <u>__underline__</u><br>
&nbsp;&nbsp;• <code>`code`</code><br><br>

<b>Mentions:</b><br>
• <b>@everyone</b> - Notify all server members<br>
• <b>Role mention</b> - Get role ID by typing \\@RoleName in Discord<br>
&nbsp;&nbsp;(enable Developer Mode in Discord settings first)<br><br>

<b>Example Messages:</b><br>
• Simple: 🚨 RAID ALERT! {telegram_message}<br>
• Formatted: **⚠️ URGENT**\\n{telegram_message}\\n@everyone<br>
• Custom: 🔴 Base under attack! Get online NOW!<br><br>

<b>Tips:</b><br>
• Test first to avoid spamming<br>
• Don't share webhook URL publicly<br>
• Create separate webhooks for different channels"""
        
        msg = QMessageBox()
        msg.setWindowTitle("Discord Webhook Help")
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
                background-color: #5865F2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4752C4;
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
