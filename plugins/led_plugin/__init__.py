"""
LED Plugin - Controls LED lights when raid alarm is triggered
"""

from plugin_base import PluginBase
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QFrame,
    QColorDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

import requests

from .led_controller import LEDController, WLEDController, GoveeController, HueController


class Plugin(PluginBase):
    """LED Controller Plugin"""

    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.controller: LEDController | None = None
        self.widget: QWidget | None = None
        self.selected_color = self.config.get("color", "#ffffff")
        self.action_radios = {}
        self.setup_controller()

    def get_name(self) -> str:
        return "LED Controller"

    def get_icon(self) -> str:
        return "💡"

    def get_description(self) -> str:
        return "Control LED lights when raid alarms are triggered"

    def setup_controller(self):
        """Initialize LED controller based on current config."""
        led_type = self.config.get("led_type", "wled")
        self.controller = None

        if led_type == "wled":
            ip = self.config.get("wled_ip", "")
            if ip:
                self.controller = WLEDController(ip)
        elif led_type == "govee":
            api_key = self.config.get("govee_api_key", "")
            device_id = self.config.get("govee_device_id", "")
            model = self.config.get("govee_model", "")
            if api_key and device_id and model:
                self.controller = GoveeController(api_key, device_id, model)
        elif led_type == "hue":
            bridge_ip = self.config.get("hue_bridge_ip", "")
            username = self.config.get("hue_username", "")
            if bridge_ip and username:
                self.controller = HueController(bridge_ip, username)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
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
        
        header = QLabel("LED Controller")
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

        subtitle = QLabel("Trigger LED actions on raid alarms")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setStyleSheet("color: #b8b8b8;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

        # LED type selection
        type_group = QGroupBox("LED System Type")
        type_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        type_group.setStyleSheet(self.get_groupbox_style())
        type_layout = QHBoxLayout(type_group)

        self.led_type_group = QButtonGroup()

        wled_radio = QRadioButton("WLED")
        govee_radio = QRadioButton("Govee")
        hue_radio = QRadioButton("Philips Hue")
        for radio in (wled_radio, govee_radio, hue_radio):
            radio.setFont(QFont("Segoe UI", 10))

        self.led_type_group.addButton(wled_radio, 0)
        self.led_type_group.addButton(govee_radio, 1)
        self.led_type_group.addButton(hue_radio, 2)

        type_layout.addWidget(wled_radio)
        type_layout.addWidget(govee_radio)
        type_layout.addWidget(hue_radio)
        type_layout.addStretch()

        current_type = self.config.get("led_type", "wled")
        if current_type == "wled":
            wled_radio.setChecked(True)
        elif current_type == "govee":
            govee_radio.setChecked(True)
        elif current_type == "hue":
            hue_radio.setChecked(True)

        self.led_type_group.buttonClicked.connect(self.update_action_visibility)
        self.led_type_group.buttonClicked.connect(self.update_param_visibility)
        layout.addWidget(type_group)

        # Action selection
        action_group = QGroupBox("Action on Trigger")
        action_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        action_group.setStyleSheet(self.get_groupbox_style())
        action_layout = QVBoxLayout(action_group)
        self.action_group = QButtonGroup()

        actions = [
            ("on", "💡 Turn On"),
            ("off", "🌙 Turn Off"),
            ("color", "🎨 Set Color"),
            ("effect", "✨ Set Effect (WLED)"),
            ("preset", "🎭 Run Preset (WLED)"),
            ("scene", "🎪 Run Scene (Govee)"),
            ("brightness", "☀ Set Brightness"),
        ]
        current_action = self.config.get("action", "on")
        for idx, (key, label) in enumerate(actions):
            radio = QRadioButton(label)
            radio.setFont(QFont("Segoe UI", 10))
            self.action_group.addButton(radio, idx)
            self.action_radios[key] = radio
            action_layout.addWidget(radio)
            if key == current_action:
                radio.setChecked(True)

        self.action_group.buttonClicked.connect(self.update_param_visibility)
        layout.addWidget(action_group)

        # Color picker
        color_row = QHBoxLayout()
        color_label = QLabel("Color:")
        color_label.setMinimumWidth(120)
        color_row.addWidget(color_label)
        self.color_btn = QPushButton("Pick Color")
        self.color_btn.setStyleSheet(
            f"background-color: {self.selected_color}; color: #000000;"
        )
        self.color_btn.clicked.connect(self.pick_color)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()
        self.color_row = color_row
        layout.addLayout(color_row)

        # Parameter rows
        params_group = QGroupBox("Action Parameters")
        params_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        params_group.setStyleSheet(self.get_groupbox_style())
        params_layout = QVBoxLayout(params_group)

        # WLED effect
        self.effect_row = QHBoxLayout()
        effect_label = QLabel("Effect #:")
        effect_label.setMinimumWidth(120)
        self.effect_row.addWidget(effect_label)
        self.wled_effect_input = QSpinBox()
        self.wled_effect_input.setRange(0, 255)
        self.wled_effect_input.setValue(int(self.config.get("effect", "0")))
        self.effect_row.addWidget(self.wled_effect_input)
        self.effect_row.addStretch()
        params_layout.addLayout(self.effect_row)

        # WLED preset
        self.preset_row = QHBoxLayout()
        preset_label = QLabel("Preset #:")
        preset_label.setMinimumWidth(120)
        self.preset_row.addWidget(preset_label)
        self.wled_preset_input = QSpinBox()
        self.wled_preset_input.setRange(0, 255)
        self.wled_preset_input.setValue(int(self.config.get("preset", "0")))
        self.preset_row.addWidget(self.wled_preset_input)
        self.preset_row.addStretch()
        params_layout.addLayout(self.preset_row)

        # Govee scene
        self.scene_row = QHBoxLayout()
        scene_label = QLabel("Scene # (Govee):")
        scene_label.setMinimumWidth(120)
        self.scene_row.addWidget(scene_label)
        self.scene_input = QSpinBox()
        self.scene_input.setRange(0, 50)
        self.scene_input.setValue(int(self.config.get("scene", "0")))
        self.scene_row.addWidget(self.scene_input)
        self.scene_row.addStretch()
        params_layout.addLayout(self.scene_row)

        # Brightness (percent)
        self.brightness_row = QHBoxLayout()
        bright_label = QLabel("Brightness (%):")
        bright_label.setMinimumWidth(120)
        self.brightness_row.addWidget(bright_label)
        self.brightness_input = QSpinBox()
        self.brightness_input.setRange(1, 100)
        self.brightness_input.setValue(int(self.config.get("brightness", "100")))
        self.brightness_input.setSuffix("%")
        self.brightness_row.addWidget(self.brightness_input)
        self.brightness_row.addStretch()
        params_layout.addLayout(self.brightness_row)

        layout.addWidget(params_group)

        # WLED configuration
        self.wled_group = QGroupBox("WLED Configuration")
        self.wled_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.wled_group.setStyleSheet(self.get_groupbox_style())
        wled_layout = QVBoxLayout(self.wled_group)
        ip_row = QHBoxLayout()
        ip_label = QLabel("IP Address:")
        ip_label.setMinimumWidth(120)
        ip_row.addWidget(ip_label)
        self.wled_ip_input = QLineEdit(self.config.get("wled_ip", ""))
        self.wled_ip_input.setPlaceholderText("e.g., 192.168.1.100")
        ip_row.addWidget(self.wled_ip_input)
        wled_layout.addLayout(ip_row)
        layout.addWidget(self.wled_group)

        # Govee configuration
        self.govee_group = QGroupBox("Govee Configuration")
        self.govee_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.govee_group.setStyleSheet(self.get_groupbox_style())
        govee_layout = QVBoxLayout(self.govee_group)
        api_row = QHBoxLayout()
        api_label = QLabel("API Key:")
        api_label.setMinimumWidth(120)
        api_row.addWidget(api_label)
        self.govee_api_input = QLineEdit(self.config.get("govee_api_key", ""))
        api_row.addWidget(self.govee_api_input)
        govee_layout.addLayout(api_row)

        device_row = QHBoxLayout()
        device_label = QLabel("Device ID:")
        device_label.setMinimumWidth(120)
        device_row.addWidget(device_label)
        self.govee_device_input = QLineEdit(self.config.get("govee_device_id", ""))
        device_row.addWidget(self.govee_device_input)
        govee_layout.addLayout(device_row)

        model_row = QHBoxLayout()
        model_label = QLabel("Model:")
        model_label.setMinimumWidth(120)
        model_row.addWidget(model_label)
        self.govee_model_input = QLineEdit(self.config.get("govee_model", ""))
        model_row.addWidget(self.govee_model_input)
        govee_layout.addLayout(model_row)

        # Scan devices button
        scan_row = QHBoxLayout()
        scan_row.addStretch()
        scan_btn = QPushButton("🔍 Scan Govee Devices")
        scan_btn.setFont(QFont("Segoe UI", 10))
        scan_btn.setMinimumHeight(32)
        scan_btn.setStyleSheet(self.get_button_style("#0e639c"))
        scan_btn.clicked.connect(self.scan_govee_devices)
        scan_row.addWidget(scan_btn)
        govee_layout.addLayout(scan_row)
        layout.addWidget(self.govee_group)

        # Hue configuration
        self.hue_group = QGroupBox("Philips Hue Configuration")
        self.hue_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.hue_group.setStyleSheet(self.get_groupbox_style())
        hue_layout = QVBoxLayout(self.hue_group)
        bridge_row = QHBoxLayout()
        bridge_label = QLabel("Bridge IP:")
        bridge_label.setMinimumWidth(120)
        bridge_row.addWidget(bridge_label)
        self.hue_bridge_input = QLineEdit(self.config.get("hue_bridge_ip", ""))
        bridge_row.addWidget(self.hue_bridge_input)
        hue_layout.addLayout(bridge_row)

        user_row = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setMinimumWidth(120)
        user_row.addWidget(user_label)
        self.hue_user_input = QLineEdit(self.config.get("hue_username", ""))
        user_row.addWidget(self.hue_user_input)
        hue_layout.addLayout(user_row)
        layout.addWidget(self.hue_group)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setFont(QFont("Segoe UI", 11))
        save_btn.setMinimumHeight(42)
        save_btn.setStyleSheet(self.get_button_style("#0e639c"))
        save_btn.clicked.connect(self.save_settings)
        button_row.addWidget(save_btn)

        test_btn = QPushButton("🔆 Test LEDs")
        test_btn.setFont(QFont("Segoe UI", 11))
        test_btn.setMinimumHeight(42)
        test_btn.setStyleSheet(self.get_button_style("#16825d"))
        test_btn.clicked.connect(self.test_leds)
        button_row.addWidget(test_btn)

        button_row.addStretch()
        layout.addLayout(button_row)

        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet("color: #888888; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Initial visibility
        self.update_config_visibility()
        self.update_action_visibility()
        self.update_param_visibility()

        return widget

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def get_selected_action(self) -> str:
        action_map = {
            0: "on",
            1: "off",
            2: "color",
            3: "effect",
            4: "preset",
            5: "scene",
            6: "brightness",
        }
        return action_map.get(self.action_group.checkedId(), "on")

    def update_config_visibility(self):
        selected_id = self.led_type_group.checkedId()
        self.wled_group.setVisible(selected_id == 0)
        self.govee_group.setVisible(selected_id == 1)
        self.hue_group.setVisible(selected_id == 2)

    def update_action_visibility(self):
        """Show compatible actions for selected LED type."""
        selected_id = self.led_type_group.checkedId()
        led_type = {0: "wled", 1: "govee", 2: "hue"}.get(selected_id, "wled")

        allowed = {
            "wled": {"on", "off", "color", "effect", "preset", "brightness"},
            "govee": {"on", "off", "color", "scene", "brightness"},
            "hue": {"on", "off", "color", "brightness"},
        }[led_type]

        for key, radio in self.action_radios.items():
            radio.setVisible(key in allowed)

        current_action = self.get_selected_action()
        if current_action not in allowed:
            self.action_radios["on"].setChecked(True)

    def update_param_visibility(self):
        """Toggle parameter rows based on action and LED type."""
        led_type = {0: "wled", 1: "govee", 2: "hue"}.get(self.led_type_group.checkedId(), "wled")
        action = self.get_selected_action()

        # Color picker only for color action
        for i in range(self.color_row.count()):
            item = self.color_row.itemAt(i)
            w = item.widget()
            if w:
                w.setVisible(action == "color")

        # Effect/preset rows only for WLED
        for layout, show in (
            (self.effect_row, action == "effect" and led_type == "wled"),
            (self.preset_row, action == "preset" and led_type == "wled"),
        ):
            for i in range(layout.count()):
                w = layout.itemAt(i).widget()
                if w:
                    w.setVisible(show)

        # Scene row only for Govee scene
        for i in range(self.scene_row.count()):
            w = self.scene_row.itemAt(i).widget()
            if w:
                w.setVisible(action == "scene" and led_type == "govee")

        # Brightness row
        for i in range(self.brightness_row.count()):
            w = self.brightness_row.itemAt(i).widget()
            if w:
                w.setVisible(action == "brightness" or (led_type == "wled" and action in {"effect", "preset", "color"}))

    def scan_govee_devices(self):
        """Fetch Govee devices using the provided API key and populate fields."""
        api_key = self.govee_api_input.text().strip()
        if not api_key:
            QMessageBox.warning(self.widget, "Govee Scan", "Please enter your Govee API key first.")
            return

        try:
            resp = requests.get(
                "https://developer-api.govee.com/v1/devices",
                headers={"Govee-API-Key": api_key},
                timeout=10,
            )
            if resp.status_code != 200:
                QMessageBox.warning(
                    self.widget,
                    "Govee Scan",
                    f"Failed to fetch devices (status {resp.status_code}).\nCheck your API key and try again.",
                )
                return

            data = resp.json()
            devices = data.get("data", {}).get("devices", []) if isinstance(data, dict) else []
            if not devices:
                QMessageBox.information(self.widget, "Govee Scan", "No devices found for this API key.")
                return

            first = devices[0]
            device_id = first.get("device", "")
            model = first.get("model", "")
            self.govee_device_input.setText(device_id)
            self.govee_model_input.setText(model)
            self.config["govee_device_id"] = device_id
            self.config["govee_model"] = model
            self.config["govee_api_key"] = api_key
            self.save_settings()

            lines = []
            for d in devices:
                lines.append(f"- {d.get('device','?')} (model {d.get('model','?')})")
            summary = "\n".join(lines)
            QMessageBox.information(
                self.widget,
                "Govee Devices Found",
                f"Found {len(devices)} device(s):\n{summary}\n\nFirst device applied to the form.",
            )

        except requests.RequestException as exc:
            QMessageBox.warning(
                self.widget,
                "Govee Scan",
                f"Network error while scanning devices:\n{exc}",
            )

    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.selected_color), self.widget, "Pick LED Color")
        if color.isValid():
            self.selected_color = color.name()
            self.color_btn.setStyleSheet(
                f"background-color: {self.selected_color}; color: #000000;"
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def save_settings(self):
        selected_id = self.led_type_group.checkedId()
        led_type_map = {0: "wled", 1: "govee", 2: "hue"}
        self.config["led_type"] = led_type_map.get(selected_id, "wled")

        # Credentials
        self.config["wled_ip"] = self.wled_ip_input.text()
        self.config["govee_api_key"] = self.govee_api_input.text()
        self.config["govee_device_id"] = self.govee_device_input.text()
        self.config["govee_model"] = self.govee_model_input.text()
        self.config["hue_bridge_ip"] = self.hue_bridge_input.text()
        self.config["hue_username"] = self.hue_user_input.text()

        # Action + params
        self.config["action"] = self.get_selected_action()
        self.config["color"] = self.selected_color
        self.config["effect"] = str(self.wled_effect_input.value())
        self.config["preset"] = str(self.wled_preset_input.value())
        self.config["scene"] = str(self.scene_input.value())
        self.config["brightness"] = str(self.brightness_input.value())

        # Reinitialize controller after changing type/credentials
        self.setup_controller()

        self.status_label.setText("✓ Settings saved!")
        self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")

    def test_leds(self):
        if not self.controller:
            self.status_label.setText("❌ No controller configured")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return

        self.status_label.setText("Testing...")
        self.status_label.setStyleSheet("color: #ffa500; padding: 10px;")

        if self.controller.test_connection():
            self.trigger_led_action()
            self.status_label.setText("✓ Test successful!")
            self.status_label.setStyleSheet("color: #00ff00; padding: 10px;")
        else:
            self.status_label.setText("❌ Connection failed")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")

    def trigger_led_action(self):
        if not self.controller:
            return

        led_type = self.config.get("led_type", "wled")
        action = self.config.get("action", "on")

        if action == "on" and hasattr(self.controller, "turn_on"):
            self.controller.turn_on()
        elif action == "off" and hasattr(self.controller, "turn_off"):
            self.controller.turn_off()
        elif action == "color" and hasattr(self.controller, "set_color"):
            color = self.config.get("color", "#ffffff")
            self.controller.set_color(color)
        elif action == "effect" and led_type == "wled" and hasattr(self.controller, "set_effect"):
            effect = int(self.config.get("effect", "0"))
            self.controller.set_effect(effect)
        elif action == "preset" and led_type == "wled" and hasattr(self.controller, "set_preset"):
            preset = int(self.config.get("preset", "0"))
            self.controller.set_preset(preset)
        elif action == "scene" and led_type == "govee" and hasattr(self.controller, "set_scene"):
            scene = int(self.config.get("scene", "0"))
            self.controller.set_scene(scene)
        elif action == "brightness" and hasattr(self.controller, "set_brightness"):
            brightness_pct = int(self.config.get("brightness", "100"))
            if led_type == "wled":
                value = int((brightness_pct / 100) * 255)
            else:
                value = brightness_pct
            self.controller.set_brightness(value)

        # For WLED, always apply brightness override if set for effect/preset/color
        if led_type == "wled" and hasattr(self.controller, "set_brightness") and action in {"effect", "preset", "color"}:
            brightness_pct = int(self.config.get("brightness", "100"))
            value = int((brightness_pct / 100) * 255)
            self.controller.set_brightness(value)

    def on_telegram_message(self, message: str):
        self.trigger_led_action()
    
    def show_help(self):
        """Show setup guide"""
        from PySide6.QtWidgets import QMessageBox
        
        help_text = """<b>LED Controller Setup Guide</b><br><br>
        
<b>WLED Setup:</b><br>
1. Install WLED on ESP8266/ESP32<br>
2. Connect to your WiFi network<br>
3. Find device IP (check router or WLED app)<br>
4. Enter IP in 'WLED IP Address' field<br>
5. Test connection<br><br>

<b>Govee Setup:</b><br>
1. Get API key from Govee Home app:<br>
   &nbsp;&nbsp;• Open app → Settings → About Us<br>
   &nbsp;&nbsp;• Tap "Apply for API Key"<br>
2. Click "Scan Devices" to find your lights<br>
3. Select device from dropdown<br>
4. Test connection<br><br>

<b>Philips Hue Setup:</b><br>
1. Find bridge IP (check Hue app or router)<br>
2. Press button on Hue bridge<br>
3. Click "Create User" within 30 seconds<br>
4. Username will be auto-filled<br>
5. Test connection<br><br>

<b>Actions:</b><br>
• <b>Turn On/Off</b> - Simple power control<br>
• <b>Set Color</b> - Choose custom color<br>
• <b>Set Effect</b> - WLED animation (0-255)<br>
• <b>Run Preset</b> - WLED saved preset (0-255)<br>
• <b>Run Scene</b> - Govee scene (0-50)<br>
• <b>Set Brightness</b> - 0-100%"""
        
        msg = QMessageBox()
        msg.setWindowTitle("LED Controller Help")
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

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------
    def get_groupbox_style(self):
        # Keep cards consistent with main theme; let global styles handle inputs.
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