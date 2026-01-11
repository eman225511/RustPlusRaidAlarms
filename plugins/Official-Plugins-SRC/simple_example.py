"""
Simple Example Plugin (Single File)

This is a minimal single-file plugin demonstrating the PluginBase contract.
Unlike the package-based example_plugin, this shows how to create a plugin
in a single .py file without needing a folder structure.

Perfect for simple plugins that don't require multiple files or dependencies.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, 
    QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt
from plugin_base import PluginBase


class Plugin(PluginBase):
    """
    A minimal single-file plugin example.
    
    Shows:
    - Basic UI creation (label, input, button)
    - Config persistence (counter value)
    - Simple interaction (button click)
    """
    
    def __init__(self, telegram_service, config):
        super().__init__(telegram_service, config)
        self.click_count = config.get("simple_example_clicks", 0)
    
    def get_name(self):
        """Return the plugin name (appears in sidebar)."""
        return "Simple Example Plugin"
    
    def get_icon(self):
        """Return the icon character (appears in sidebar)."""
        return "📝"
    
    def get_description(self):
        """Return plugin description (optional, for tooltips/about)."""
        return "Minimal single-file plugin example"

    def get_version(self):
        return "1.0.0"

    def get_author(self):
        return "RustPlusRaidAlarms Team"

    def get_homepage(self):
        return "https://github.com/eman225511/RustPlusRaidAlarms"
    
    def get_widget(self):
        """Create and return the plugin's UI widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title card
        title_card = QGroupBox()
        title_card.setObjectName("card")
        title_layout = QVBoxLayout(title_card)
        
        title = QLabel("Simple Single-File Plugin")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Demonstrates basic plugin functionality in one file")
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_card)
        
        # Counter display
        self.counter_label = QLabel(f"Button clicked {self.click_count} times")
        self.counter_label.setStyleSheet("font-size: 14px; padding: 10px;")
        self.counter_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.counter_label)
        
        # Name input
        input_card = QGroupBox("Enter Your Name")
        input_card.setObjectName("card")
        input_layout = QVBoxLayout(input_card)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Type your name here...")
        self.name_input.setText(self.config.get("simple_example_name", ""))
        input_layout.addWidget(self.name_input)
        
        layout.addWidget(input_card)
        
        # Action buttons
        button_card = QGroupBox("Actions")
        button_card.setObjectName("card")
        button_layout = QVBoxLayout(button_card)
        
        # Click me button
        self.click_button = QPushButton("Click Me!")
        self.click_button.clicked.connect(self._on_button_click)
        button_layout.addWidget(self.click_button)
        
        # Save button
        save_button = QPushButton("Save Name")
        save_button.clicked.connect(self._save_name)
        button_layout.addWidget(save_button)
        
        layout.addWidget(button_card)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #0e639c; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Push everything to top
        layout.addStretch()
        
        return widget
    
    def _on_button_click(self):
        """Handle button click - increment counter."""
        self.click_count += 1
        self.config["simple_example_clicks"] = self.click_count
        self.counter_label.setText(f"Button clicked {self.click_count} times")
        
        name = self.name_input.text().strip()
        if name:
            self.status_label.setText(f"Hello, {name}! 👋")
        else:
            self.status_label.setText(f"Clicked {self.click_count} times!")
    
    def _save_name(self):
        """Save the name to config."""
        name = self.name_input.text().strip()
        self.config["simple_example_name"] = name
        
        if name:
            self.status_label.setText(f"✓ Saved name: {name}")
        else:
            self.status_label.setText("✓ Name cleared")
    
    def on_telegram_message(self, message_text):
        """
        Optional: React to Telegram messages.
        
        This plugin doesn't use this hook, but it's available if needed.
        For example, you could count messages or update the UI.
        """
        pass  # Do nothing for this simple example


# Export the plugin class
# The plugin loader looks for a class named "Plugin"
__all__ = ['Plugin']
