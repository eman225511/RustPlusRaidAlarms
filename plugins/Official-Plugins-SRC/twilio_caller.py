"""
Twilio Call Plugin - Calls multiple phone numbers on raid alerts
"""

from plugin_base import PluginBase
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
    QFrame,
    QTextEdit,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


class Plugin(PluginBase):
    """Twilio Call Plugin"""

    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.widget = None
        self.client = None

    def get_name(self) -> str:
        return "Twilio Caller"

    def get_icon(self) -> str:
        return "📞"

    def get_description(self) -> str:
        return "Call multiple phone numbers on raid alerts using Twilio"

    def get_widget(self) -> QWidget:
        if self.widget is None:
            self.widget = self.create_widget()
        return self.widget

    def create_widget(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header_frame = QFrame()
        header_frame.setObjectName("heroCard")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 16, 16, 16)

        # Title row with help button
        title_row = QHBoxLayout()
        
        header = QLabel("📞 Twilio Caller")
        header.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header.setStyleSheet("color: #ffffff;")
        title_row.addWidget(header)
        
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

        subtitle = QLabel("Call multiple phone numbers when raid alarms are triggered")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

        # Warning if Twilio not installed
        if not TWILIO_AVAILABLE:
            warning_frame = QFrame()
            warning_frame.setObjectName("card")
            warning_layout = QVBoxLayout(warning_frame)
            warning_layout.setContentsMargins(16, 16, 16, 16)
            
            warning = QLabel("⚠️ Twilio library not installed")
            warning.setFont(QFont("Segoe UI", 12, QFont.Bold))
            warning.setStyleSheet("color: #ff8800;")
            warning_layout.addWidget(warning)
            
            install_msg = QLabel("Install it with: pip install twilio")
            install_msg.setFont(QFont("Segoe UI", 10))
            install_msg.setStyleSheet("color: #b8b8b8;")
            warning_layout.addWidget(install_msg)
            
            layout.addWidget(warning_frame)

        # Twilio Credentials
        creds_group = QGroupBox("Twilio Credentials")
        creds_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        creds_group.setStyleSheet(self.get_groupbox_style())
        creds_layout = QVBoxLayout(creds_group)

        # Account SID
        sid_row = QHBoxLayout()
        sid_label = QLabel("Account SID:")
        sid_label.setMinimumWidth(120)
        sid_label.setFont(QFont("Segoe UI", 10))
        sid_row.addWidget(sid_label)
        
        self.account_sid_input = QLineEdit(self.config.get("twilio_account_sid", ""))
        self.account_sid_input.setPlaceholderText("ACxxxxxxxxxxxxxxxxxxxx")
        self.account_sid_input.setMinimumHeight(32)
        self.account_sid_input.textChanged.connect(self.save_credentials)
        sid_row.addWidget(self.account_sid_input)
        creds_layout.addLayout(sid_row)

        # Auth Token
        token_row = QHBoxLayout()
        token_label = QLabel("Auth Token:")
        token_label.setMinimumWidth(120)
        token_label.setFont(QFont("Segoe UI", 10))
        token_row.addWidget(token_label)
        
        self.auth_token_input = QLineEdit(self.config.get("twilio_auth_token", ""))
        self.auth_token_input.setPlaceholderText("your_auth_token")
        self.auth_token_input.setEchoMode(QLineEdit.Password)
        self.auth_token_input.setMinimumHeight(32)
        self.auth_token_input.textChanged.connect(self.save_credentials)
        token_row.addWidget(self.auth_token_input)
        creds_layout.addLayout(token_row)

        # Twilio Phone Number (from)
        from_row = QHBoxLayout()
        from_label = QLabel("Twilio Number:")
        from_label.setMinimumWidth(120)
        from_label.setFont(QFont("Segoe UI", 10))
        from_row.addWidget(from_label)
        
        self.from_number_input = QLineEdit(self.config.get("twilio_from_number", ""))
        self.from_number_input.setPlaceholderText("+1XXXXXXXXXX")
        self.from_number_input.setMinimumHeight(32)
        self.from_number_input.textChanged.connect(self.save_credentials)
        from_row.addWidget(self.from_number_input)
        creds_layout.addLayout(from_row)

        layout.addWidget(creds_group)

        # Phone Numbers to Call
        numbers_group = QGroupBox("Phone Numbers to Call")
        numbers_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        numbers_group.setStyleSheet(self.get_groupbox_style())
        numbers_layout = QVBoxLayout(numbers_group)

        numbers_label = QLabel("Enter one phone number per line (E.164 format: +1XXXXXXXXXX)")
        numbers_label.setFont(QFont("Segoe UI", 9))
        numbers_label.setStyleSheet("color: #b8b8b8; margin-bottom: 8px;")
        numbers_layout.addWidget(numbers_label)

        self.phone_numbers_input = QTextEdit()
        self.phone_numbers_input.setPlaceholderText("+12025551234\n+13035555678\n+14155559999")
        self.phone_numbers_input.setMinimumHeight(120)
        self.phone_numbers_input.setMaximumHeight(200)
        
        # Load saved numbers
        saved_numbers = self.config.get("twilio_phone_numbers", [])
        if saved_numbers:
            self.phone_numbers_input.setPlainText("\n".join(saved_numbers))
        
        self.phone_numbers_input.textChanged.connect(self.save_phone_numbers)
        numbers_layout.addWidget(self.phone_numbers_input)

        layout.addWidget(numbers_group)

        # Call Message
        message_group = QGroupBox("Call Message")
        message_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        message_group.setStyleSheet(self.get_groupbox_style())
        message_layout = QVBoxLayout(message_group)

        message_label = QLabel("Message to speak during the call:")
        message_label.setFont(QFont("Segoe UI", 9))
        message_label.setStyleSheet("color: #b8b8b8; margin-bottom: 8px;")
        message_layout.addWidget(message_label)

        self.call_message_input = QTextEdit()
        self.call_message_input.setPlaceholderText("RAID ALERT. YOU ARE BEING RAIDED IN RUST. LOG IN NOW.")
        self.call_message_input.setMinimumHeight(80)
        self.call_message_input.setMaximumHeight(120)
        
        default_message = self.config.get(
            "twilio_call_message",
            "RAID ALERT. YOU ARE BEING RAIDED IN RUST. LOG IN NOW."
        )
        self.call_message_input.setPlainText(default_message)
        self.call_message_input.textChanged.connect(self.save_call_message)
        message_layout.addWidget(self.call_message_input)

        layout.addWidget(message_group)

        # Test Call Button
        test_frame = QFrame()
        test_frame.setObjectName("card")
        test_layout = QVBoxLayout(test_frame)
        test_layout.setContentsMargins(16, 16, 16, 16)

        test_btn = QPushButton("📞 Test Call All Numbers")
        test_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        test_btn.setMinimumHeight(48)
        test_btn.setStyleSheet(self.get_button_style("#0e639c"))
        test_btn.clicked.connect(self.test_call)
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

    def save_credentials(self):
        """Save Twilio credentials to config"""
        self.config["twilio_account_sid"] = self.account_sid_input.text().strip()
        self.config["twilio_auth_token"] = self.auth_token_input.text().strip()
        self.config["twilio_from_number"] = self.from_number_input.text().strip()

    def save_phone_numbers(self):
        """Save phone numbers list to config"""
        text = self.phone_numbers_input.toPlainText()
        numbers = [line.strip() for line in text.split("\n") if line.strip()]
        self.config["twilio_phone_numbers"] = numbers

    def save_call_message(self):
        """Save call message to config"""
        self.config["twilio_call_message"] = self.call_message_input.toPlainText().strip()

    def make_calls(self):
        """Make calls to all configured phone numbers"""
        if not TWILIO_AVAILABLE:
            self.status_label.setText("❌ Twilio library not installed")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return

        # Get credentials
        account_sid = self.config.get("twilio_account_sid", "").strip()
        auth_token = self.config.get("twilio_auth_token", "").strip()
        from_number = self.config.get("twilio_from_number", "").strip()
        
        if not account_sid or not auth_token or not from_number:
            self.status_label.setText("❌ Missing Twilio credentials")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return

        # Get phone numbers
        phone_numbers = self.config.get("twilio_phone_numbers", [])
        if not phone_numbers:
            self.status_label.setText("❌ No phone numbers configured")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return

        # Get call message
        message = self.config.get("twilio_call_message", "RAID ALERT. YOU ARE BEING RAIDED IN RUST. LOG IN NOW.")

        try:
            # Initialize Twilio client
            client = Client(account_sid, auth_token)

            # Build TwiML
            twiml = f"""
            <Response>
                <Say voice="male">
                    {message}
                </Say>
            </Response>
            """

            # Make calls
            success_count = 0
            fail_count = 0
            
            for number in phone_numbers:
                try:
                    call = client.calls.create(
                        to=number,
                        from_=from_number,
                        twiml=twiml
                    )
                    print(f"[Twilio] Calling: {number} (SID: {call.sid})")
                    success_count += 1
                except Exception as e:
                    print(f"[Twilio] Failed to call {number}: {str(e)}")
                    fail_count += 1

            if fail_count == 0:
                self.status_label.setText(f"✓ Successfully initiated {success_count} call(s)")
                self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
            else:
                self.status_label.setText(f"⚠ {success_count} succeeded, {fail_count} failed")
                self.status_label.setStyleSheet("color: #ffaa00; padding: 10px;")

        except Exception as e:
            self.status_label.setText(f"❌ Error: {str(e)[:50]}")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            print(f"[Twilio] Error making calls: {str(e)}")

    def test_call(self):
        """Test call functionality"""
        if not TWILIO_AVAILABLE:
            QMessageBox.warning(
                None,
                "Twilio Not Installed",
                "Please install the Twilio library:\n\npip install twilio"
            )
            return

        # Validate inputs
        account_sid = self.config.get("twilio_account_sid", "").strip()
        auth_token = self.config.get("twilio_auth_token", "").strip()
        from_number = self.config.get("twilio_from_number", "").strip()
        phone_numbers = self.config.get("twilio_phone_numbers", [])

        missing = []
        if not account_sid:
            missing.append("Account SID")
        if not auth_token:
            missing.append("Auth Token")
        if not from_number:
            missing.append("Twilio Number")
        if not phone_numbers:
            missing.append("Phone Numbers")

        if missing:
            QMessageBox.warning(
                None,
                "Missing Configuration",
                f"Please configure the following:\n\n• " + "\n• ".join(missing)
            )
            return

        # Confirm test
        reply = QMessageBox.question(
            None,
            "Test Call",
            f"This will call {len(phone_numbers)} number(s):\n\n" + "\n".join(phone_numbers) + "\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.status_label.setText("📞 Initiating calls...")
            self.status_label.setStyleSheet("color: #ffa500; padding: 10px;")
            self.make_calls()

    def on_telegram_message(self, message: str):
        """Called when a Telegram message is received - trigger calls"""
        print(f"[Twilio] Raid alert received, making calls...")
        self.make_calls()
    
    def show_help(self):
        """Show setup guide"""
        help_text = """<b>Twilio Setup Guide</b><br><br>

<b>Step 1: Create Twilio Account</b><br>
1. Go to <a href="https://www.twilio.com/try-twilio">twilio.com/try-twilio</a><br>
2. Sign up for free trial ($15 credit)<br>
3. Verify your email and phone number<br><br>

<b>Step 2: Get Credentials</b><br>
1. Go to Twilio Console Dashboard<br>
2. Find "Account SID" - copy and paste it<br>
3. Find "Auth Token" - click "Show" then copy<br><br>

<b>Step 3: Get Phone Number</b><br>
1. In Twilio Console, click "Get a Trial Number"<br>
2. Accept the suggested number<br>
3. Copy this number (format: +1XXXXXXXXXX)<br><br>

<b>Step 4: Add Numbers to Call</b><br>
1. Enter phone numbers one per line<br>
2. Must use E.164 format: +1XXXXXXXXXX<br>
3. <b>Trial accounts can only call verified numbers!</b><br>
4. Verify numbers at: Console → Phone Numbers → Verified Caller IDs<br><br>

<b>Step 5: Customize Message</b><br>
1. Edit the call message text<br>
2. Keep it short and clear<br>
3. Test with one number first<br><br>

<b>Trial Limitations:</b><br>
• Can only call verified numbers<br>
• Call starts with "You have a call from a Twilio trial account"<br>
• Upgrade to remove restrictions<br><br>

<b>Costs (Paid Account):</b><br>
• ~$1/month per phone number<br>
• ~$0.013 per minute of calls"""
        
        msg = QMessageBox()
        msg.setWindowTitle("Twilio Caller Help")
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
