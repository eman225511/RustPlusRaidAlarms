"""
Plugin Base Class
All plugins must inherit from this class
"""

from abc import ABC, abstractmethod
from PySide6.QtWidgets import QWidget


class PluginBase(ABC):
    """
    Abstract base class for all plugins
    
    Plugins must implement all abstract methods to be loaded by the main application.
    Each plugin receives access to the TelegramService and shared config.
    """
    
    def __init__(self, telegram_service, config):
        """
        Initialize the plugin
        
        Args:
            telegram_service: Shared TelegramService instance
            config: Shared configuration dictionary
        """
        self.telegram_service = telegram_service
        self.config = config
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return the plugin's display name
        
        Returns:
            str: Plugin name (e.g., "LED Controller")
        """
        pass
    
    @abstractmethod
    def get_icon(self) -> str:
        """
        Return an emoji or icon for the plugin
        
        Returns:
            str: Icon/emoji (e.g., "💡")
        """
        pass
    
    @abstractmethod
    def get_widget(self) -> QWidget:
        """
        Return the plugin's main widget for display in the UI
        
        Returns:
            QWidget: The widget to be displayed in the plugin tab
        """
        pass
    
    @abstractmethod
    def on_telegram_message(self, message: str):
        """
        Called when a new Telegram message is received
        
        Args:
            message: The message text received from Telegram
        """
        pass
    
    def get_description(self) -> str:
        """
        Optional: Return a description of the plugin
        
        Returns:
            str: Plugin description
        """
        return "No description provided"
    
    def get_version(self) -> str:
        """
        Optional: Return the plugin version
        
        Returns:
            str: Version string (e.g., "1.0.0")
        """
        return "1.0.0"
    
    def get_author(self) -> str:
        """
        Optional: Return the plugin author
        
        Returns:
            str: Author name
        """
        return "Unknown"
    
    def get_homepage(self) -> str:
        """
        Optional: Return the plugin homepage/repo URL
        
        Returns:
            str: URL or empty string
        """
        return ""
    
    def on_enable(self):
        """Optional: Called when the plugin is enabled"""
        pass
    
    def on_disable(self):
        """Optional: Called when the plugin is disabled"""
        pass
    
    def cleanup(self):
        """Optional: Called when the plugin is being unloaded"""
        pass
