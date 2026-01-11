"""
Example Plugin

A fuller reference plugin that demonstrates the PluginBase contract, basic UI,
config persistence, Telegram handling, and app styling. Use this as a template
when building your own plugins.
"""

from plugin_base import PluginBase
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame,
    QLineEdit,
)
from PySide6.QtGui import QFont


class Plugin(PluginBase):
    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.widget = None

    # Required metadata -------------------------------------------------
    def get_name(self) -> str:
        return "Example Plugin"

    def get_icon(self) -> str:
        return "🧪"

    def get_description(self) -> str:
        return "Reference plugin showing UI + hooks"

    def get_version(self) -> str:
        return "1.0.0"

    def get_author(self) -> str:
        return "RustPlusRaidAlarms Team"

    def get_homepage(self) -> str:
        return "https://github.com/eman225511/RustPlusRaidAlarms"

    # UI ----------------------------------------------------------------
    def get_widget(self) -> QWidget:
        if self.widget is None:
            self.widget = self._build_ui()
        return self.widget

    def _build_ui(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Hero card
        hero = QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 16, 16, 16)
        title = QLabel("Example Plugin")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle = QLabel("Shows how to build a plugin: UI, config, messaging")
        subtitle.setFont(QFont("Segoe UI", 10))
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        # Settings card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        # Config field (stored in self.config)
        self.message_input = QLineEdit(self.config.get("example_message", "Hello from plugin!"))
        self.message_input.setPlaceholderText("Message to show in the dialog")
        self.message_input.setMinimumHeight(32)

        field_row = QHBoxLayout()
        label = QLabel("Dialog message:")
        label.setFont(QFont("Segoe UI", 10))
        label.setMinimumWidth(120)
        field_row.addWidget(label)
        field_row.addWidget(self.message_input)

        card_layout.addLayout(field_row)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        show_btn = QPushButton("Show Message")
        show_btn.setMinimumHeight(36)
        show_btn.clicked.connect(self.show_message)
        btn_row.addWidget(show_btn)

        save_btn = QPushButton("Save Setting")
        save_btn.setMinimumHeight(36)
        save_btn.clicked.connect(self.save_setting)
        btn_row.addWidget(save_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 10))
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)
        layout.addStretch()
        return widget

    # Actions -----------------------------------------------------------
    def show_message(self):
        text = self.message_input.text().strip() or "(empty message)"
        QMessageBox.information(None, "Example Plugin", text)

    def save_setting(self):
        self.config["example_message"] = self.message_input.text().strip()
        self.status_label.setText("Saved setting to config")

    # Telegram hook -----------------------------------------------------
    def on_telegram_message(self, message: str):
        """React to Telegram messages; here we log and optionally pop."""
        print(f"[ExamplePlugin] Received Telegram message: {message}")
        # Optional: uncomment to pop a dialog on every message (noisy!)
        # QMessageBox.information(None, "Example Plugin", f"Telegram said: {message}")
